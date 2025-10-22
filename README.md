# PickleDB Distributed System

Hệ thống quản lý công việc phân tán sử dụng PickleDB với tính năng Replication và Leader Election.

## 🚀 Tính năng

- ✅ **Replication**: Dữ liệu tự động sao lưu từ Leader sang Followers
- ✅ **Leader Election**: Tự động bầu Leader mới khi node chính die
- ✅ **Failover**: Dashboard tự động chuyển sang node phụ khi cần
- ✅ **Persistent Storage**: Dữ liệu được lưu dưới dạng pickle file
- ✅ **Real-time Sync**: Tasks được đồng bộ ngay lập tức

## 📦 Cài đặt

```bash
# Clone hoặc tải project

# Cài đặt dependencies
pip install flask flask-cors pickledb

# Tạo thư mục logs
mkdir -p logs
```

## 🏃 Chạy Cluster

### Cách 1: Chạy tự động (khuyến nghị)

```bash
chmod +x run_cluster.sh
./run_cluster.sh
```

### Cách 2: Chạy thủ công

**Terminal 1 - Node Chính (Port 4000):**

```bash
python3 demo_cluster.py
```

**Terminal 2 - Node Phụ (Port 4001):**

```bash
python3 demo_follower.py
```

## 🌐 Truy cập

- **Dashboard Node Chính**: http://127.0.0.1:4000/
- **Dashboard Node Phụ**: http://127.0.0.1:4001/

## 🔍 Kiểm tra trạng thái

```bash
# Health check
curl http://127.0.0.1:4000/health
curl http://127.0.0.1:4001/health

# Cluster status
curl http://127.0.0.1:4000/cluster/status

# Node status
curl http://127.0.0.1:4000/status
curl http://127.0.0.1:4001/status
```

## 🧪 Test Failover

1. Mở dashboard: http://127.0.0.1:4000/
2. Thêm vài tasks
3. Dừng node 4000:
   ```bash
   pkill -f demo_cluster.py
   ```
4. Dashboard tự động chuyển sang port 4001
5. Tasks vẫn còn đầy đủ nhờ replication!

## 📊 Cấu trúc thư mục

```
pickledb-cluster/
├── api_server.py          # Flask API server
├── cluster_manager.py     # Cluster management logic
├── demo_cluster.py        # Node chính (4000)
├── demo_follower.py       # Node phụ (4001)
├── run_cluster.sh         # Script khởi động
├── examples/
│   └── node_dashboard.html  # Dashboard UI
├── logs/                  # Log files
│   ├── node_4000.log
│   └── node_4001.log
└── *.db                   # PickleDB data files
```

## 🔧 API Endpoints

### Tasks Management

- `GET /tasks` - Lấy danh sách tasks
- `POST /tasks` - Tạo task mới
- `PUT /tasks/:id` - Cập nhật task
- `DELETE /tasks/:id` - Xóa task

### Cluster Management

- `GET /health` - Health check
- `GET /status` - Node status
- `GET /cluster/status` - Cluster info
- `GET /heartbeat` - Heartbeat từ leader
- `POST /replicate` - Nhận data replication

### Legacy API

- `POST /set` - Set key-value
- `GET /jobs` - Lấy tất cả jobs

## 🛑 Dừng Cluster

```bash
# Dừng tất cả nodes
pkill -f demo_cluster.py
pkill -f demo_follower.py
```

## 📝 Cách hoạt động

### Replication

1. Client gửi request đến Leader (4000)
2. Leader lưu vào PickleDB của mình
3. Leader replicate sang Follower (4001)
4. Follower lưu vào PickleDB của mình
5. Trả response về client

### Leader Election

1. Leader gửi heartbeat mỗi 2 giây
2. Follower theo dõi heartbeat
3. Nếu không nhận heartbeat >5 giây:
   - Follower tự bầu mình làm Leader
   - Bắt đầu gửi heartbeat
   - Dashboard tự động failover

### Failover

1. Dashboard ping node chính mỗi 5 giây
2. Nếu node chính die:
   - Dashboard chuyển sang node phụ
   - Hiển thị cảnh báo failover
   - Tất cả requests gửi đến node phụ
3. Khi node chính hoạt động lại:
   - Dashboard tự động failback về node chính

## 🐛 Troubleshooting

**Port already in use:**

```bash
lsof -ti:4000 | xargs kill -9
lsof -ti:4001 | xargs kill -9
```

**Cannot connect to node:**

- Kiểm tra firewall
- Kiểm tra node có đang chạy không: `ps aux | grep demo_`

**Tasks not syncing:**

- Kiểm tra logs: `tail -f logs/node_*.log`
- Kiểm tra network giữa các nodes

## 👨‍💻 Các thành viên nhóm

- Nguyễn Thế Trường - 22010212

- Nguyễn Thế Trường An - 22010253
