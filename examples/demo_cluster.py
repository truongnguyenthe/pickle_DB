import threading
from src.api_server import create_app

PORT = 4000
PEERS = ["http://127.0.0.1:4001"]

app, cluster = create_app(PORT, PEERS)
cluster.is_leader = True
cluster.current_leader = f"http://127.0.0.1:{PORT}"
cluster.start_heartbeat()

if __name__ == "__main__":
    app.run(port=PORT)
