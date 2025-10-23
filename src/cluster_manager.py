import requests
import threading
import time
import random
from datetime import datetime

class ClusterManager:
    def __init__(self, port, peers, all_nodes):
        self.port = port
        self.peers = peers  # Danh sách followers hiện tại
        self.all_nodes = all_nodes  # Tất cả nodes trong cluster
        self.is_leader = False
        self.current_leader = None
        self.last_heartbeat = time.time()
        self.alive = True
        self.election_timeout = random.uniform(5, 8)  # Random để tránh split vote
        self.term = 0  # Election term để tránh conflict

    # ================== HEARTBEAT =====================
    def start_heartbeat(self):
        """Leader gửi tín hiệu heartbeat định kỳ"""
        if not self.is_leader:
            return
            
        print(f"[HEARTBEAT] Node {self.port} started sending heartbeat every 2s.\n")
        
        def heartbeat():
            while self.is_leader and self.alive:
                for node in self.peers:
                    follower_port = node.split(':')[-1]
                    try:
                        response = requests.get(f"{node}/heartbeat", timeout=1)
                        if response.status_code != 200:
                            print(f"[HEARTBEAT] Follower {follower_port} not responding")
                    except Exception as e:
                        print(f"[HEARTBEAT] ❌ Cannot reach follower {follower_port}")
                        
                time.sleep(2)
                
        threading.Thread(target=heartbeat, daemon=True).start()

    # ================== ELECTION MONITOR ==============
    def start_election_monitor(self):
        """Theo dõi heartbeat và trigger election khi cần"""
        def monitor():
            print(f"[ELECTION] Node {self.port} monitoring for leader election.\n")
            
            while self.alive:
                if not self.is_leader:
                    time_since_heartbeat = time.time() - self.last_heartbeat
                    
                    # Chỉ trigger election nếu vượt timeout
                    if time_since_heartbeat > self.election_timeout:
                        print(f"\n{'='*70}")
                        print(f"  [ELECTION] Leader timeout! No heartbeat for {time_since_heartbeat:.1f}s")
                        print(f"  Node {self.port} starting election (term {self.term + 1})")
                        print(f"{'='*70}\n")
                        
                        self.start_election()
                        
                time.sleep(1)
                
        threading.Thread(target=monitor, daemon=True).start()

    def start_election(self):
        """
        Bầu cử leader mới theo thuật toán:
        1. Tìm tất cả nodes còn sống
        2. Chọn node có port nhỏ nhất (deterministic)
        3. Cập nhật peers list cho leader mới
        """
        self.term += 1
        alive_nodes = []
        
        print(f"[ELECTION] Checking health of all nodes...")
        
        # Kiểm tra tất cả nodes
        for node in self.all_nodes:
            node_port = node.split(':')[-1]
            try:
                response = requests.get(f"{node}/health", timeout=1.5)
                if response.status_code == 200:
                    alive_nodes.append(node)
                    print(f"  ✓ Node {node_port}: ALIVE")
                else:
                    print(f"  ✗ Node {node_port}: UNHEALTHY")
            except Exception as e:
                print(f"  ✗ Node {node_port}: DEAD ({e.__class__.__name__})")
        
        if not alive_nodes:
            print(f"\n[ELECTION] ⚠️  No nodes alive! Cannot elect leader.\n")
            return
        
        # Chọn node có port nhỏ nhất làm leader (deterministic)
        new_leader = min(alive_nodes, key=lambda x: int(x.split(':')[-1]))
        self.current_leader = new_leader
        
        my_url = f"http://127.0.0.1:{self.port}"
        self.is_leader = (my_url == new_leader)
        
        print(f"\n{'='*70}")
        if self.is_leader:
            # Cập nhật peers: tất cả nodes còn sống trừ bản thân
            self.peers = [node for node in alive_nodes if node != my_url]
            
            print(f" Node {self.port} elected as LEADER (term {self.term})")
            print(f" Followers: {len(self.peers)} nodes")
            for i, peer in enumerate(self.peers, 1):
                peer_port = peer.split(':')[-1]
                print(f"   {i}. http://127.0.0.1:{peer_port}")
            
            # Reset heartbeat timestamp
            self.last_heartbeat = time.time()
            
            # Bắt đầu gửi heartbeat
            self.start_heartbeat()
        else:
            leader_port = new_leader.split(':')[-1]
            print(f"📡 Node {self.port} following LEADER at port {leader_port} (term {self.term})")
            
            # Reset heartbeat timestamp để đợi heartbeat từ leader mới
            self.last_heartbeat = time.time()
        
        print(f"{'='*70}\n")

    # ================== REPLICATION ==================
    def replicate_to_followers(self, key, value):
        """
        Leader replicate dữ liệu đến tất cả followers
        """
        if not self.is_leader:
            print(f"[REPLICATION] ⚠️  Node {self.port} không phải leader, không thể replicate!")
            return
        
        if not self.peers:
            print(f"[REPLICATION] No followers to replicate to.")
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S %p")
        action = "DELETE" if value is None else "SET"
        
        print(f"--- Replication done at {timestamp}")
        print(f"--- Start replicate at {timestamp}")
        print(f"Action: {action} | Key: '{key}'")
        
        success_count = 0
        failed_count = 0
        
        for node in self.peers:
            follower_port = node.split(':')[-1]
            try:
                response = requests.post(
                    f"{node}/replicate",
                    json={"key": key, "value": value},
                    timeout=2
                )
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"Replicated key='{key}' to http://127.0.0.1:{follower_port} success.")
                else:
                    failed_count += 1
                    print(f"Replicated key='{key}' to http://127.0.0.1:{follower_port} failed (HTTP {response.status_code}).")
                    
            except requests.exceptions.Timeout:
                failed_count += 1
                print(f"Replicated key='{key}' to http://127.0.0.1:{follower_port} failed (Timeout).")
            except requests.exceptions.ConnectionError:
                failed_count += 1
                print(f"Replicated key='{key}' to http://127.0.0.1:{follower_port} failed (Connection Error).")
            except Exception as e:
                failed_count += 1
                print(f"Replicated key='{key}' to http://127.0.0.1:{follower_port} failed ({e.__class__.__name__}).")
        
        print(f"--- Replication done at {datetime.now().strftime('%H:%M:%S %p')}")
        print(f"Result: {success_count}/{len(self.peers)} followers synced successfully")
        if failed_count > 0:
            print(f"⚠️  {failed_count} followers failed to sync\n")
        else:
            print()

    # ================== HEARTBEAT HANDLER =============
    def receive_heartbeat(self):
        """
        Nhận heartbeat từ leader
        Cập nhật timestamp để reset election timeout
        """
        self.last_heartbeat = time.time()
        
        return {
            "status": "alive",
            "port": self.port,
            "is_leader": self.is_leader,
            "current_leader": self.current_leader,
            "term": self.term
        }

    # ================== UTILS =========================
    def get_status(self):
        """Trả về trạng thái hiện tại của node"""
        return {
            "port": self.port,
            "is_leader": self.is_leader,
            "current_leader": self.current_leader,
            "term": self.term,
            "peers": self.peers,
            "last_heartbeat": self.last_heartbeat,
            "election_timeout": self.election_timeout
        }
    
    def shutdown(self):
        """Dừng node một cách graceful"""
        self.alive = False
        was_leader = self.is_leader
        self.is_leader = False
        
        if was_leader:
            print(f"\n [SHUTDOWN] Leader node {self.port} shutting down...")
            print(f"   Followers will elect new leader in ~{self.election_timeout:.1f}s\n")
        else:
            print(f"\n [SHUTDOWN] Follower node {self.port} shutting down...\n")