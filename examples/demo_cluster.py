#!/usr/bin/env python3
"""
Demo Cluster - Node Chính (Leader)
Port: 4000
"""

from src.api_server import create_app

if __name__ == "__main__":
    PORT = 4000
    PEERS = ["http://127.0.0.1:4001"]  # Danh sách followers
    
    print("=" * 60)
    print("PICKLEDB CLUSTER - NODE CHÍNH (LEADER)")
    print("=" * 60)
    print(f" Port: {PORT}")
    print(f" Peers: {PEERS}")
    print(f" Dashboard: http://127.0.0.1:{PORT}/")
    print("=" * 60)
    
    app, cluster = create_app(PORT, PEERS)
    
    # Node chính tự động trở thành leader
    cluster.is_leader = True
    cluster.current_leader = f"http://127.0.0.1:{PORT}"
    cluster.start_heartbeat()
    
    print(f"\n Node {PORT} khởi động thành công - VAI TRÒ: LEADER\n")
    
    app.run(host="0.0.0.0", port=PORT, debug=False)