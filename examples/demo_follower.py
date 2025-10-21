from src.api_server import create_app

PORT = 4001
PEERS = ["http://127.0.0.1:4000"]

app, cluster = create_app(PORT, PEERS)
if __name__ == "__main__":
    app.run(port=PORT)
