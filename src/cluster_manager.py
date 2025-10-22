import requests
import threading
import time
import random
from datetime import datetime

class ClusterManager:
    def __init__(self, port, peers, all_nodes):
        self.port = port
        self.peers = peers
        self.all_nodes = all_nodes
        self.is_leader = False
        self.current_leader = None
        self.last_heartbeat = time.time()
        self.alive = True
        self.election_timeout = random.uniform(4, 7)  # ngẫu nhiên để tránh tie election

    # ================== HEARTBEAT =====================
    def start_heartbeat(self):
        """Leader gửi tín hiệu heartbeat định kỳ"""
        if not self.is_leader:
            return
        print(f"[HEARTBEAT] Node {self.port} sending heartbeat every 2s.")
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
        """Theo dõi leader và tự bầu khi leader chết"""
        def monitor():
            print(f"[ELECTION] Node {self.port} bắt đầu theo dõi leader.")
            while self.alive:
                if not self.is_leader:
                    # kiểm tra thời gian từ lần cuối có heartbeat
                    if time.time() - self.last_heartbeat > self.election_timeout:
                        print(f"\n[ELECTION] Leader mất! Node {self.port} bắt đầu bầu cử.")
                        self.start_election()
                time.sleep(1)
        threading.Thread(target=monitor, daemon=True).start()

    def start_election(self):
        """Chọn node có port nhỏ nhất còn sống làm leader"""
        alive_nodes = []
        for node in self.all_nodes:
            try:
                r = requests.get(f"{node}/health", timeout=1)
                if r.status_code == 200:
                    alive_nodes.append(node)
            except:
                pass

        if not alive_nodes:
            print(f"[ELECTION] Không có node nào sống ngoài {self.port}")
            return

        new_leader = min(alive_nodes + [f"http://127.0.0.1:{self.port}"])
        self.current_leader = new_leader
        self.is_leader = (f"http://127.0.0.1:{self.port}" == new_leader)

        if self.is_leader:
            print(f"🔥 Node {self.port} trở thành LEADER")
            self.start_heartbeat()
        else:
            print(f"🤝 Node {self.port} theo LEADER {self.current_leader}")

    # ================== REPLICATION ==================
    def replicate_to_followers(self, key, value):
        """Leader gửi dữ liệu đến tất cả followers"""
        if not self.is_leader:
            return
        timestamp = datetime.now().strftime("%H:%M:%S %p")
        print(f"--- [REPLICATION] Leader {self.port} gửi dữ liệu tới followers lúc {timestamp}")
        for node in self.peers:
            try:
                requests.post(f"{node}/replicate",
                              json={"key": key, "value": value}, timeout=2)
            except Exception as e:
                print(f"[{self.port}] ❌ Lỗi replicate tới {node}: {e.__class__.__name__}")

    # ================== HEARTBEAT HANDLER =============
    def receive_heartbeat(self):
        """Nhận heartbeat từ leader"""
        self.last_heartbeat = time.time()
        return {"status": "alive", "leader": self.current_leader or "unknown"}

    # ================== UTILS =========================
    def shutdown(self):
        self.alive = False
        self.is_leader = False
        print(f"\n [SHUTDOWN] Node {self.port} đã dừng\n")
