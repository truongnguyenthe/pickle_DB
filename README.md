# PickleDB Distributed Todo System

PickleDB Distributed Todo System là một ứng dụng quản lý công việc phân tán giúp người dùng dễ dàng thêm, sửa và xóa các nhiệm vụ trong ngày. Ứng dụng sử dụng **Python**, **Flask**, **PickleDB** và **JavaScript** để tạo ra một hệ thống phân tán mạnh mẽ với khả năng chịu lỗi cao, đảm bảo dữ liệu luôn an toàn và có thể truy cập ngay cả khi có nodes gặp sự cố.

## Mục đích

PickleDB Distributed Todo System được thiết kế để giúp người dùng tổ chức công việc một cách hiệu quả trong môi trường phân tán. Hệ thống không chỉ đơn thuần là một ứng dụng quản lý công việc mà còn là một công cụ học tập về các khái niệm cơ bản trong **Hệ thống phân tán** như sao lưu dữ liệu tự động, bầu chọn node chính, và tự động phục hồi khi có lỗi. Ứng dụng giúp giảm bớt sự phức tạp trong việc quản lý công việc, đồng thời đảm bảo tính sẵn sàng cao (High Availability) và độ tin cậy của dữ liệu trong môi trường distributed.

## Các tính năng chính

- **Thêm công việc**: Cho phép người dùng thêm các nhiệm vụ vào danh sách công việc, dữ liệu được lưu vào PickleDB và tự động replicate sang các nodes khác.
- **Chỉnh sửa công việc**: Người dùng có thể chỉnh sửa thông tin của nhiệm vụ đã được thêm vào, thay đổi được đồng bộ tự động trên toàn bộ cluster.
- **Xóa công việc**: Cho phép người dùng xóa nhiệm vụ đơn lẻ hoặc hàng loạt khi đã hoàn thành hoặc không còn cần thiết.
- **Giao diện người dùng hiện đại**: Với giao diện responsive và trực quan, người dùng có thể nhanh chóng quản lý công việc và giám sát trạng thái cluster real-time.
- **Replication (Sao chép dữ liệu)**: Đồng bộ hóa dữ liệu tự động giữa các nodes trong cluster (Leader → Followers), đảm bảo mọi thay đổi được backup ngay lập tức. Khi Leader thêm/sửa/xóa task, dữ liệu được replicate sang tất cả Followers trong vòng 2 giây.
- **Batch Processing (Xử lý hàng loạt)**: Cho phép người dùng thêm nhiều nhiệm vụ cùng một lúc bằng textarea multiline, hoặc xóa tất cả nhiệm vụ đã hoàn thành chỉ với một click, giúp tiết kiệm thời gian và nâng cao hiệu suất làm việc.
- **Leader Election (Bầu chọn node chính)**: Trong môi trường phân tán, hệ thống tự động xác định một node làm "Leader" để xử lý tất cả write operations. Khi Leader die, hệ thống tự động bầu Leader mới (node có port nhỏ nhất còn sống) trong vòng 5-8 giây, đảm bảo tính liên tục của dịch vụ.

## Công nghệ sử dụng

- **Python**: Ngôn ngữ lập trình chính, mạnh mẽ và dễ học, phù hợp cho việc xây dựng hệ thống phân tán.
- **Flask**: Web framework nhẹ và linh hoạt cho Python, giúp xây dựng REST API một cách nhanh chóng và hiệu quả.
- **PickleDB**: Cơ sở dữ liệu key-value lightweight với persistent storage, lưu trữ các nhiệm vụ dưới dạng cặp khóa-giá trị và serialize bằng Python pickle.
- **JavaScript**: Xử lý logic client-side, tương tác với REST API, và tự động failover khi phát hiện node die.
- **HTML/CSS**: Xây dựng giao diện người dùng hiện đại với gradient background, animations, và responsive design.

## Các thành viên nhóm 👥

- **Nguyễn Thế Trường** - Mã số sinh viên 22010212
- **Nguyễn Thế Trường An** - Mã số sinh viên 22010253

## Cài đặt và sử dụng

1.  **Clone repo**:  
    Clone repository về máy của bạn bằng lệnh sau:

    ```bash
    git clone https://github.com/truongnguyenthe/pickle_DB.git
    ```

2.  **Chuyển đến thư mục dự án**:  
    Di chuyển vào thư mục dự án đã clone:

    ```bash
    cd pickle_DB
    ```

3.  **(Tuỳ chọn) Tạo môi trường ảo Python**:

    ```bash
    python -m venv venv
    venv\Scripts\activate # Windows
    source venv/bin/activate # Linux/macOS

    ```

4.  **Cài đặt các thư viện**:  
    Cài đặt thư viện cho dự án:

    ```bash
    pip install -r requirements.txt
    ```

5.  **Chạy các node Flask server**:  
    Mỗi node tương ứng là một server Flask riêng biệt.

    Mở 4 terminal riêng và chạy lần lượt:

    Terminal 1 – Node Leader (port 4000):

    ```bash
    python -m examples.cluster
    ```

    Terminal 2 – Node Leader (port 4001):

    ```bash
    python -m examples.follower1
    ```

    Terminal 3 – Node Leader (port 4002):

    ```bash
    python -m examples.follower2
    ```

    Terminal 4 – Node Leader (port 4003):

    ```bash
    python -m examples.follower3
    ```

6.  **Kiểm tra API bằng Postman hoặc cURL**:

    ➤ **Tạo công việc mới** (chỉ gửi đến Leader - Port 4000)

    ```bash
       POST http://127.0.0.1:4000/tasks
    ```

    Body (JSON):

    ```json
    {
      "title": "Học Distributed Systems"
    }
    ```

    ➤ **Thêm nhiều công việc** (Batch Processing)

    Truy cập Dashboard tại `http://localhost:5500/node_dashboard/index.html` và sử dụng textarea "Thêm Nhiều Công Việc":

    ```
       Học Python
       Làm đồ án
       Ôn thi cuối kỳ
    ```

    Hoặc gọi API nhiều lần:

    ```bash
       POST http://127.0.0.1:4000/tasks
       Body: {"title": "Task 1"}

       POST http://127.0.0.1:4000/tasks
       Body: {"title": "Task 2"}
    ```

    ➤ **Cập nhật công việc** (đánh dấu hoàn thành)

    ```bash
       PUT http://127.0.0.1:4000/tasks/<task_id>
    ```

    Body (JSON):

    ```json
    {
      "completed": true
    }
    ```

    ➤ **Xóa công việc**

    ```bash
       DELETE http://127.0.0.1:4000/tasks/<task_id>
    ```

    ➤ **Lấy danh sách tất cả công việc**

    ```bash
       GET http://127.0.0.1:4000/tasks
    ```

    **Lưu ý**: Tất cả các thao tác thêm/sửa/xóa chỉ được thực hiện trên **Leader node** (Port 4000). Nếu gửi request đến Follower, bạn sẽ nhận được thông báo lỗi:

    ```json
    {
      "error": "not_leader",
      "message": "Only leader can create tasks",
      "leader": "http://127.0.0.1:4000"
    }
    ```

7.  **Kiểm tra sao chép dữ liệu (Replication)**:

    Sau khi thêm dữ liệu vào Leader (port 4000), dữ liệu sẽ được **replicate ngay lập tức** sang các node phụ (port 4001, 4002, 4003). Để kiểm tra:

    **Cách 1: Kiểm tra qua API**

    ```bash
       # Lấy danh sách tasks từ Follower 1 (port 4001)
       GET http://127.0.0.1:4001/tasks
       # Lấy danh sách tasks từ Follower 2 (port 4002)
       GET http://127.0.0.1:4002/tasks
       # Lấy danh sách tasks từ Follower 3 (port 4003)
       GET http://127.0.0.1:4003/tasks
    ```

    Kết quả: Cả 4 nodes (4000, 4001, 4002, 4003) sẽ có **cùng dữ liệu tasks**!

    **Cách 2: Kiểm tra qua Dashboard**

    - Mở `http://127.0.0.1:4000/` - Thêm task
    - Mở `http://127.0.0.1:4001/` - Xem task đã được replicate
    - Mở `http://127.0.0.1:4002/` - Xem task đã được replicate
    - Mở `http://127.0.0.1:4003/` - Xem task đã được replicate

    **Thời gian replicate**: Dữ liệu được đồng bộ **ngay lập tức** (< 2 giây), đảm bảo rằng mọi thay đổi trên Leader đều được backup tự động trên tất cả Followers.

8.  **Truy cập Dashboard**:

    Mở trình duyệt và nhập `http://localhost:5500/node_dashboard/index.html` để sử dụng giao diện web quản lý công việc với các tính năng:

    - Thêm công việc đơn lẻ hoặc hàng loạt
    - Đánh dấu hoàn thành
    - Xóa công việc
    - Lọc công việc (Tất cả / Đang làm / Đã hoàn thành)
    - Xem trạng thái cluster real-time

## Các API Endpoint 📡

### **GET /tasks**

- **Mô tả**: Lấy tất cả các tasks từ database.
- **Phương thức**: GET
- **Response**: Trả về danh sách tasks được sắp xếp theo thời gian tạo (mới nhất trước).
- **Ví dụ**:

```bash
  curl -XGET http://localhost:4000/tasks
```

### **POST /tasks**

- **Mô tả**: Tạo task mới. Chỉ leader mới có quyền ghi dữ liệu. Nếu node không phải leader, sẽ trả về thông tin leader hiện tại.
- **Phương thức**: POST
- **Body**: `{"title": "Task title"}`
- **Response**: Trả về task vừa tạo hoặc thông báo lỗi nếu không phải leader.
- **Ví dụ**:

```bash
  curl -XPOST http://localhost:4000/tasks -H 'Content-Type: application/json' -d '{"title": "New task"}'
```

### **PUT /tasks/:task_id**

- **Mô tả**: Cập nhật thông tin task (title hoặc completed status). Chỉ leader mới có quyền thực hiện.
- **Phương thức**: PUT
- **Body**: `{"title": "Updated title", "completed": true}`
- **Response**: Trả về task đã cập nhật hoặc thông báo lỗi.
- **Ví dụ**:

```bash
  curl -XPUT http://localhost:4000/tasks/your-task-id -H 'Content-Type: application/json' -d '{"completed": true}'
```

### **DELETE /tasks/:task_id**

- **Mô tả**: Xóa một task khỏi database. Chỉ leader mới có quyền thực hiện.
- **Phương thức**: DELETE
- **Response**: Trả về status "deleted" hoặc thông báo lỗi.
- **Ví dụ**:

```bash
  curl -XDELETE http://localhost:4000/tasks/your-task-id
```

### **POST /replicate**

- **Mô tả**: Nhận dữ liệu replicate từ leader. API nội bộ dùng để đồng bộ dữ liệu giữa các nodes.
- **Phương thức**: POST
- **Body**: `{"key": "task_id", "value": {...}}`
- **Response**: Trả về status "replicated".
- **Ví dụ**:

```bash
  curl -XPOST http://localhost:4000/replicate -H 'Content-Type: application/json' -d '{"key": "task_123", "value": {"title": "Task"}}'
```

### **GET /heartbeat**

- **Mô tả**: Nhận heartbeat từ leader để duy trì kết nối và xác nhận trạng thái cluster.
- **Phương thức**: GET
- **Response**: Trả về thông tin heartbeat.
- **Ví dụ**:

```bash
  curl -XGET http://localhost:4000/heartbeat
```

### **GET /status**

- **Mô tả**: Trả về trạng thái của node hiện tại (leader hay follower, port, last heartbeat).
- **Phương thức**: GET
- **Response**: `{"leader": "...", "is_leader": true/false, "port": 5000, "last_heartbeat": ...}`
- **Ví dụ**:

```bash
  curl -XGET http://localhost:4000/status
```

### **GET /health**

- **Mô tả**: Health check endpoint để kiểm tra node có hoạt động không.
- **Phương thức**: GET
- **Response**: `{"status": "ok", "port": 4000, "is_leader": true/false}`
- **Ví dụ**:

```bash
  curl -XGET http://localhost:4000/health
```

### **GET /cluster/status**

- **Mô tả**: Trả về thông tin toàn bộ cluster (leader, followers, node hiện tại).
- **Phương thức**: GET
- **Response**: `{"leader": "...", "followers": [...], "current_node": "...", "is_leader": true/false}`
- **Ví dụ**:

```bash
  curl -XGET http://localhost:4000/cluster/status
```

### **GET /**

- **Mô tả**: Trả về dashboard HTML để quản lý tasks qua giao diện web.
- **Phương thức**: GET
- **Ví dụ**: Truy cập `http://localhost:4000/` trên trình duyệt.

---

## 💬 Lời cảm ơn

Cảm ơn bạn đã tham gia và sử dụng **PickleDB Distributed Todo System**!  
Ứng dụng được phát triển với mục tiêu **đơn giản hóa việc quản lý công việc hằng ngày**, giúp người dùng dễ dàng theo dõi và đồng bộ nhiệm vụ trên nhiều node khác nhau.

Hệ thống **Flask + PickleDB** không chỉ mang lại trải nghiệm mượt mà mà còn minh họa cách xây dựng một **môi trường phân tán có khả năng tự bầu leader, tự đồng bộ dữ liệu và tự phục hồi khi gặp sự cố**.

---
