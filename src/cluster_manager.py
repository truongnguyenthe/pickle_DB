import requests
import threading
import time

class ClusterManager:
    def __init__(self, port, peers):
        self.port = port
        self.peers = peers
        self.is_leader = False
        self.current_leader = None
        self.last_heartbeat = time.time()
        self.alive = True

    # ================== REPLICATION ==================
    def replicate_to_followers(self, key, value):
        """
        Leader gửi dữ liệu đến followers
        value=None nghĩa là xóa key
        """
        for node in self.peers:
            try:
                requests.post(
                    f"{node}/replicate", 
                    json={"key": key, "value": value}, 
                    timeout=2
                )
                action = "xóa" if value is None else "set"
                print(f"[REPL] {action} key='{key}' tới follower {node}")
            except Exception as e:
                print(f"[WARN] Không gửi được tới {node}: {e}")

    # ================== HEARTBEAT =====================
    def start_heartbeat(self):
        """Leader gửi tín hiệu heartbeat định kỳ"""
        if not self.is_leader:
            return
            
        print(f"[HEARTBEAT] Node {self.port} là leader, bắt đầu gửi heartbeat...")
        
        def heartbeat():
            while self.is_leader and self.alive:
                for node in self.peers:
                    try:
                        response = requests.get(f"{node}/heartbeat", timeout=1)
                        if response.status_code == 200:
                            print(f"[HEARTBEAT] Ping → {node} ✓")
                    except Exception as e:
                        print(f"[HEARTBEAT] Ping → {node} ✗ ({e})")
                time.sleep(2)  # Gửi heartbeat mỗi 2 giây
                
        threading.Thread(target=heartbeat, daemon=True).start()

    # ================== ELECTION MONITOR ==============
    def start_election_monitor(self):
        """
        Theo dõi heartbeat từ leader
        Nếu không nhận được heartbeat >5s → tự bầu mình làm leader
        """
        def monitor():
            while self.alive:
                if not self.is_leader:
                    time_since_heartbeat = time.time() - self.last_heartbeat
                    
                    if time_since_heartbeat > 5:
                        print(f"\n[ELECTION] ⚠️ Node {self.port} không nhận heartbeat trong {time_since_heartbeat:.1f}s")
                        print(f"[ELECTION] 🗳️ Tự bầu mình làm LEADER mới!")
                        
                        self.is_leader = True
                        self.current_leader = f"http://127.0.0.1:{self.port}"
                        self.last_heartbeat = time.time()
                        
                        # Bắt đầu gửi heartbeat
                        self.start_heartbeat()
                
                time.sleep(1)  # Kiểm tra mỗi 1 giây
                
        threading.Thread(target=monitor, daemon=True).start()
        print(f"[MONITOR] Node {self.port} bắt đầu theo dõi election")

    # ================== UTILITIES =====================
    def shutdown(self):
        """Dừng node"""
        self.alive = False
        self.is_leader = False
        print(f"[SHUTDOWN] Node {self.port} đã tắt")