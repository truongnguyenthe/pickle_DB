from src.api_server import create_app

if __name__ == "__main__":
    PORT = 4003
    ALL_NODES = [
        "http://127.0.0.1:4000",
        "http://127.0.0.1:4001",
        "http://127.0.0.1:4002",
        "http://127.0.0.1:4003",
    ]
    PEERS = [n for n in ALL_NODES if f":{PORT}" not in n]

    print("=" * 60)
    print("PICKLEDB CLUSTER - NODE FOLLOWER 4003")
    print("=" * 60)
    print(f" Port: {PORT}")
    print(f" Peers: {PEERS}")
    print(f" Dashboard: http://127.0.0.1:{PORT}/")
    print("=" * 60)

    app, cluster = create_app(PORT, PEERS, ALL_NODES)
    cluster.start_election_monitor()

    print(f"\n Node {PORT} khởi động thành công - VAI TRÒ: FOLLOWER\n")
    app.run(host="0.0.0.0", port=PORT, debug=False)