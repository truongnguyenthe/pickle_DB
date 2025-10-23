# 🗄️ PickleDB Distributed System

**Hệ thống cơ sở dữ liệu phân tán sử dụng PickleDB với Replication và Leader Election**

---

## 📖 Giới thiệu

**PickleDB Distributed System** là một hệ thống quản lý công việc (Todo List) phân tán được xây dựng trên nền tảng PickleDB - một cơ sở dữ liệu key-value nhẹ cho Python. Hệ thống triển khai các tính năng quan trọng của database phân tán như **Data Replication**, **Leader Election**, và **Automatic Failover** để đảm bảo tính sẵn sàng cao (High Availability) và độ tin cậy của dữ liệu.

### 🎯 Mục tiêu dự án

- Tìm hiểu và triển khai các khái niệm cơ bản về hệ thống phân tán
- Xây dựng cơ chế đồng bộ dữ liệu giữa nhiều nodes
- Triển khai thuật toán Leader Election để chọn node chính
- Đảm bảo tính nhất quán của dữ liệu trong môi trường phân tán
- Xây dựng giao diện web trực quan để quản lý và giám sát cluster

---

## ✨ Tính năng chính

### 1. 🗄️ PickleDB - Persistent Key-Value Storage

PickleDB là một cơ sở dữ liệu key-value đơn giản được thiết kế cho Python, sử dụng module `pickle` để serialize và lưu trữ dữ liệu vào file.

**Đặc điểm:**

- **Persistent Storage**: Dữ liệu được lưu vĩnh viễn vào file `.db`
- **Auto-dump**: Tự động ghi dữ liệu xuống disk sau mỗi thao tác
- **Key-Value Model**: Lưu trữ dữ liệu dưới dạng cặp key-value
- **Python Native**: Hoạt động native với Python, không cần cài đặt database server

**Cách hoạt động trong hệ thống:**

- Mỗi node có một file database riêng: `node_4000.db`, `node_4001.db`, `node_4002.db`
- Tasks được lưu với key format: `task_<uuid>` và value là JSON object
- Dữ liệu được serialize bằng pickle và lưu persistent trên disk

### 2. 🔄 Replication - Sao lưu dữ liệu tự động

**Replication** là quá trình sao chép dữ liệu từ node Leader sang các node Follower để đảm bảo tính nhất quán và sẵn sàng cao.

**Cơ chế hoạt động:**

1. **Write Request**: Client gửi request tạo/sửa/xóa task đến Leader
2. **Local Write**: Leader lưu dữ liệu vào database của mình
3. **Replicate**: Leader gửi dữ liệu đến tất cả Followers qua HTTP POST `/replicate`
4. **Follower Write**: Mỗi Follower nhận data và lưu vào database của mình
5. **Acknowledgment**: Leader đợi phản hồi từ Followers (timeout 2s)

**Log replication trong terminal:**

```
--- Replication done at 14:30:45 PM
--- Start replicate at 14:30:45 PM
Action: SET | Key: 'task_abc123'
Replicated key='task_abc123' to http://127.0.0.1:4001 success.
Replicated key='task_abc123' to http://127.0.0.1:4002 success.
Replicated key='task_abc123' to http://127.0.0.1:4003 success.
--- Replication done at 14:30:45 PM
Result: 2/2 followers synced successfully
```

**Ưu điểm:**

- ✅ Dữ liệu được backup trên nhiều nodes
- ✅ Tăng khả năng chịu lỗi (fault tolerance)
- ✅ Cho phép đọc dữ liệu từ bất kỳ node nào
- ✅ Dữ liệu không bị mất khi một node die

### 3. 👑 Leader Election - Bầu chọn node chính

**Leader Election** là cơ chế tự động chọn một node làm Leader (node chính) để xử lý tất cả write operations.

**Thuật toán:**

```python
1. Tất cả nodes bắt đầu như Follower
2. Leader gửi heartbeat mỗi 2 giây
3. Follower theo dõi heartbeat với timeout ngẫu nhiên 5-8 giây
4. Nếu Follower không nhận heartbeat > timeout:
   a. Trigger election
   b. Kiểm tra health của tất cả nodes
   c. Chọn node có port nhỏ nhất còn sống làm Leader
   d. Leader mới bắt đầu gửi heartbeat
```

**Ví dụ quá trình election:**

```
======================================================================
⚠️  [ELECTION] Leader timeout! No heartbeat for 5.2s
🗳️  Node 4001 starting election (term 2)
======================================================================

[ELECTION] Checking health of all nodes...
  ✗ Node 4000: DEAD (ConnectionError)
  ✓ Node 4001: ALIVE
  ✓ Node 4002: ALIVE
  ✓ Node 4003: ALIVE

======================================================================
👑 Node 4001 elected as LEADER (term 2)
📊 Followers: 1 nodes
   1. http://127.0.0.1:4002
======================================================================
```

**Đặc điểm:**

- **Deterministic**: Luôn chọn node có port nhỏ nhất (tránh split-brain)
- **Term-based**: Mỗi lần election tăng term để phát hiện stale leaders
- **Random timeout**: Tránh nhiều nodes trigger election đồng thời
- **Health check**: Chỉ chọn nodes còn sống

### 4. 🔁 Automatic Failover - Chuyển đổi tự động

**Failover** là quá trình tự động chuyển sang node backup khi node chính gặp sự cố.

**Kịch bản:**

**Khi Leader die:**

1. Followers phát hiện mất heartbeat sau 5-8 giây
2. Trigger leader election
3. Node mới được chọn làm Leader
4. Dashboard tự động redirect sang Leader mới
5. Dữ liệu vẫn còn nguyên nhờ replication

**Khi Leader cũ sống lại:**

1. Node cũ join lại cluster như một Follower
2. Nhận heartbeat từ Leader mới
3. Dashboard có thể tự động failback về node cũ (nếu có priority)

**Dashboard tự động redirect:**

```javascript
// Kiểm tra health mỗi 5 giây
async function checkNodeHealth() {
  if (primaryNodeDead && secondaryNodeAlive) {
    // Tự động chuyển URL từ :4000 → :4001
    window.location.href = "http://127.0.0.1:4001/";
  }
}
```

### 5. 💓 Heartbeat - Giám sát trạng thái

**Heartbeat** là tín hiệu định kỳ giữa Leader và Followers để duy trì trạng thái cluster.

**Cơ chế:**

- Leader gửi HTTP GET `/heartbeat` đến tất cả Followers mỗi 2 giây
- Follower nhận heartbeat và cập nhật `last_heartbeat` timestamp
- Nếu Follower không nhận heartbeat > timeout → trigger election

**Thông tin heartbeat:**

```json
{
  "status": "alive",
  "port": 4001,
  "is_leader": false,
  "current_leader": "http://127.0.0.1:4000",
  "term": 1
}
```

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT / BROWSER                      │
│                  (Dashboard - Port 5500)                     │
└────────────────┬───────────────────────────┬─────────────────┘
                 │ HTTP API                  │ HTTP API
                 ▼                           ▼
┌────────────────────────────┐  ┌──────────────────────────────┐
│   NODE 4000 (LEADER)       │  │   NODE 4001 (FOLLOWER)       │
│  ┌──────────────────────┐  │  │  ┌──────────────────────┐    │
│  │  Flask API Server    │  │  │  │  Flask API Server    │    │
│  │  - CRUD APIs         │  │  │  │  - Read APIs         │    │
│  │  - Replication       │  │  │  │  - Receive Replicate │    │
│  └──────────┬───────────┘  │  │  └──────────┬───────────┘    │
│             │              │  │             │                │
│  ┌──────────▼───────────┐  │  │  ┌──────────▼───────────┐    │
│  │  Cluster Manager     │  │◄─┼──┤  Cluster Manager     │    │
│  │  - Heartbeat Sender  │  │  │  │  - Heartbeat Monitor │    │
│  │  - Leader Election   │  │  │  │  - Election Trigger  │    │
│  └──────────┬───────────┘  │  │  └──────────┬───────────┘    │
│             │              │  │             │                │
│  ┌──────────▼───────────┐  │  │  ┌──────────▼───────────┐    │
│  │   PickleDB           │  │  │  │   PickleDB           │    │
│  │   node_4000.db       │  │  │  │   node_4001.db       │    │
│  └──────────────────────┘  │  │  └──────────────────────┘    │
└────────────────────────────┘  └──────────────────────────────┘
                 │                           ▲
                 │ Replication               │
                 └───────────────────────────┘

┌──────────────────────────────┐
│   NODE 4002 (FOLLOWER)       │
│  ┌──────────────────────┐    │
│  │  Flask API Server    │    │
│  │  - Read APIs         │    │
│  │  - Receive Replicate │    │
│  └──────────┬───────────┘    │
│             │                │
│  ┌──────────▼───────────┐    │
│  │  Cluster Manager     │    │
│  │  - Heartbeat Monitor │    │
│  │  - Election Trigger  │    │
│  └──────────┬───────────┘    │
│             │                │
│  ┌──────────▼───────────┐    │
│  │   PickleDB           │    │
│  │   node_4002.db       │    │
│  └──────────────────────┘    │
└──────────────────────────────┘
```

---

## 📦 Cài đặt

### Yêu cầu hệ thống

- **Python**: 3.7 trở lên
- **Hệ điều hành**: Linux, macOS, hoặc Windows
- **RAM**: Tối thiểu 512MB
- **Disk**: 100MB trống

### Các bước cài đặt

**1. Clone repository:**

```bash
git clone https://github.com/truongnguyenthe/pickle_DB.git
cd pickle_DB
```

**2. Cài đặt dependencies:**

```bash
pip install -r requirements.txt
```

Hoặc cài đặt thủ công:

```bash
pip install flask==3.0.0
pip install flask-cors==4.0.0
pip install pickledb==0.9.2
pip install requests==2.31.0
```

**3. Tạo cấu trúc thư mục:**

```bash
mkdir -p logs
mkdir -p src
touch src/__init__.py
```

**4. Đảm bảo cấu trúc đúng:**

```
pickle_DB/
├── src/
│   ├── __init__.py
│   ├── api_server.py
│   └── cluster_manager.py
├── examples/
│   ├── culster.py
│   ├── follower1.py
│   ├── follower2.py
│   └── follower3.py
├── node_dashboard.html
├── requirements.txt
└── README.md
```

---

## 🚀 Hướng dẫn chạy

### Cách 1: Chạy thủ công (Khuyến nghị cho development)

**Terminal 1 - Node Leader (Port 4000):**

```bash
python -m examples.cluster
```

**Terminal 2 - Node Follower 1 (Port 4001):**

```bash
python -m examples.follower1
```

**Terminal 3 - Node Follower 2 (Port 4002):**

```bash
python -m examples.follower2
```

**Terminal 4 - Node Follower 3 (Port 4003):**

```bash
python -m examples.follower3
```

**Mở Dashboard:**

```
http://localhost:5500/node_dashboard.html
```

---

## 🧪 Hướng dẫn test

### Test 1: Kiểm tra Replication

**1. Thêm task từ Dashboard:**

- Mở http://localhost:5500/node_dashboard.html
- Thêm task: "Học Distributed Systems"

**2. Kiểm tra terminal:**

```
Terminal 1 (4000):
--- Replication done at 14:30:45 PM
Replicated to 4001 success.
Replicated to 4002 success.
Replicated to 4003 success.

Terminal 2 (4001):
--- Replication received at 14:30:45 PM
Saved key='task_xyz' to db.json

Terminal 3 (4002):
--- Replication received at 14:30:45 PM
Saved key='task_xyz' to db.json

Terminal 4 (4003):
--- Replication received at 14:30:45 PM
Saved key='task_xyz' to db.json
```

**3. Verify data:**

```bash
# Kiểm tra 3 nodes có cùng data
curl http://127.0.0.1:4000/tasks
curl http://127.0.0.1:4001/tasks
curl http://127.0.0.1:4002/tasks
curl http://127.0.0.1:4003/tasks
```

### Test 2: Kiểm tra Leader Election & Failover

**1. Thêm tasks vào node 4000**

**2. Kill node 4000:**

```bash
pkill -f examples.cluster.py
```

**3. Quan sát Terminal 2 (4001):**

```
[ELECTION] Leader timeout! No heartbeat for 5.2s
👑 Node 4001 elected as LEADER (term 2)
[HEARTBEAT] Node 4001 started sending heartbeat
```

**4. Dashboard tự động redirect:**

- URL thay đổi từ `:4000` → `:4001`
- Tasks vẫn hiển thị đầy đủ

**5. Thêm task mới từ node 4001:**

- Task được replicate sang node 4002

**6. Khởi động lại node 4000:**

```bash
python -m examples.culster
```

- Node 4000 join lại như Follower
- Node 4001 vẫn là Leader

### Test 3: Test với Postman

**Set key-value:**

```
POST http://127.0.0.1:4000/set
Content-Type: application/json

{
  "key": "username",
  "value": "Trường"
}
```

**Get all data:**

```
GET http://127.0.0.1:4000/jobs
```

**Check cluster status:**

```
GET http://127.0.0.1:4000/status
```

---

## 🔧 API Documentation

### Tasks Management

#### GET /tasks

Lấy danh sách tất cả tasks

**Response:**

```json
{
  "tasks": [
    {
      "id": "abc-123",
      "title": "Học Python",
      "completed": false,
      "created_at": "2025-01-20T10:30:00"
    }
  ]
}
```

#### POST /tasks

Tạo task mới (chỉ Leader)

**Request:**

```json
{
  "title": "Học Distributed Systems"
}
```

**Response:**

```json
{
  "id": "xyz-789",
  "title": "Học Distributed Systems",
  "completed": false,
  "created_at": "2025-01-20T10:35:00"
}
```

#### PUT /tasks/:id

Cập nhật task (chỉ Leader)

**Request:**

```json
{
  "completed": true
}
```

#### DELETE /tasks/:id

Xóa task (chỉ Leader)

### Cluster Management

#### GET /health

Health check cho leader election

```json
{
  "status": "ok",
  "port": 4000,
  "is_leader": true,
  "term": 1
}
```

#### GET /status

Trạng thái chi tiết của node

```json
{
  "port": 4000,
  "is_leader": true,
  "current_leader": "http://127.0.0.1:4000",
  "term": 1,
  "peers": [
    "http://127.0.0.1:4001",
    "http://127.0.0.1:4002",
    "http://127.0.0.1:4003"
  ],
  "last_heartbeat": 1705750800.123
}
```

#### GET /heartbeat

Nhận heartbeat từ Leader

#### POST /replicate

Nhận data replication từ Leader (internal)

### Legacy Key-Value API

#### POST /set

Set key-value pair

```json
{
  "key": "name",
  "value": "Trường"
}
```

#### GET /jobs

Lấy tất cả key-value pairs

---

## 📊 Monitoring & Troubleshooting

### Xem logs realtime

```bash
# Node 4000
tail -f logs/node_4000.log

# Node 4001
tail -f logs/node_4001.log

# Tất cả nodes
tail -f logs/node_*.log
```

### Kiểm tra ports đang sử dụng

```bash
# Linux/Mac
lsof -i :4000
lsof -i :4001
lsof -i :4002

# Windows
netstat -ano | findstr :4000
```

### Giải phóng ports

```bash
# Linux/Mac
lsof -ti:4000 | xargs kill -9
lsof -ti:4001 | xargs kill -9
lsof -ti:4002 | xargs kill -9

# Windows
taskkill /PID <PID> /F
```

## 👥 Thành viên nhóm

| STT | Họ và Tên            | MSSV     |
| --- | -------------------- | -------- |
| 1   | Nguyễn Thế Trường    | 22010212 |
| 2   | Nguyễn Thế Trường An | 22010253 |

---

## 🎓 Kiến thức áp dụng

### Công nghệ

- **Backend**: Python, Flask, PickleDB
- **Frontend**: HTML, CSS, JavaScript
- **Protocol**: HTTP/REST API
- **Serialization**: Pickle, JSON

### Kỹ năng

- Thiết kế hệ thống phân tán
- Xử lý đồng bộ dữ liệu
- Xử lý lỗi và recovery
- API design và documentation
