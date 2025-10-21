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
        """Leader gửi dữ liệu đến followers"""
        for node in self.peers:
            try:
                requests.post(f"{node}/replicate", json={"key": key, "value": value}, timeout=2)
                print(f"[REPL] Gửi key='{key}' tới follower {node}")
            except Exception as e:
                print(f"[WARN] Không gửi được tới {node}: {e}")

    # ================== HEARTBEAT =====================
    def start_heartbeat(self):
        """Leader gửi tín hiệu heartbeat"""
        if not self.is_leader:
            return
        print(f"[HEARTBEAT] Node {self.port} là leader, gửi heartbeat...")
        def heartbeat():
            while self.is_leader and self.alive:
                for node in self.peers:
                    try:
                        requests.get(f"{node}/heartbeat", timeout=1)
                    except:
                        pass
                time.sleep(2)
        threading.Thread(target=heartbeat, daemon=True).start()

    # ================== ELECTION MONITOR ==============
    def start_election_monitor(self):
        """Theo dõi heartbeat, nếu mất >5s thì tự bầu leader mới"""
        def monitor():
            while self.alive:
                if not self.is_leader and time.time() - self.last_heartbeat > 5:
                    print(f"[ELECTION] Node {self.port} không thấy leader → tự bầu mình làm leader")
                    self.is_leader = True
                    self.current_leader = f"http://127.0.0.1:{self.port}"
                    self.start_heartbeat()
                time.sleep(1)
        threading.Thread(target=monitor, daemon=True).start()
