#!/usr/bin/env python3
"""
Demo Follower - Node Phụ (Follower)
Port: 4001
Chức năng: Nhận replication từ Leader, tự động lên làm Leader khi Leader die
"""

from src.api_server import create_app

if __name__ == "__main__":
    PORT = 4001
    PEERS = ["http://127.0.0.1:4000"]  # Node chính (Leader)
    
    print("=" * 60)
    print("PICKLEDB CLUSTER - NODE PHỤ (FOLLOWER)")
    print("=" * 60)
    print(f"Port: {PORT}")
    print(f"Leader: {PEERS[0]}")
    print(f"Dashboard: http://127.0.0.1:{PORT}/")
    print("=" * 60)
    
    # Khởi tạo app và cluster
    app, cluster = create_app(PORT, PEERS)
    
    # Thiết lập node phụ
    cluster.is_leader = False
    cluster.current_leader = PEERS[0]
    
    print(f"\nNode {PORT} khởi động thành công - VAI TRÒ: FOLLOWER")
    print(f"Đang chờ heartbeat từ Leader ({PEERS[0]})...")
    print(f"Nếu không nhận heartbeat >5s → Tự bầu làm Leader\n")
    
    # Chạy Flask server
    app.run(host="0.0.0.0", port=PORT, debug=False)