#!/usr/bin/env python3
"""
Demo Cluster - Node Follower
Port: 4001
"""

from src.api_server import create_app

if __name__ == "__main__":
    PORT = 4003
    PEERS = [
        "http://127.0.0.1:4000",  # Leader
        "http://127.0.0.1:4001",
        "http://127.0.0.1:4002"
    ]  # Các peers khác (không bao gồm chính mình)
    
    print("=" * 60)
    print("PICKLEDB CLUSTER - NODE FOLLOWER")
    print("=" * 60)
    print(f" Port: {PORT}")
    print(f" Peers: {PEERS}")
    print(f" Dashboard: http://127.0.0.1:{PORT}/")
    print("=" * 60)
    
    app, cluster = create_app(PORT, PEERS)
    
    # Follower không set leader - sẽ tự detect qua heartbeat
    print(f"\n Node {PORT} khởi động thành công - VAI TRÒ: FOLLOWER\n")
    
    app.run(host="0.0.0.0", port=PORT, debug=False)