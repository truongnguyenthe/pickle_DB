from flask import Flask, request, jsonify, send_from_directory
import pickledb
import os
import time
import uuid
from datetime import datetime
from flask_cors import CORS
from src.cluster_manager import ClusterManager

def create_app(port, peers):
    app = Flask(__name__, static_folder="../examples", static_url_path="/")
    CORS(app)
    
    # Load PickleDB
    db = pickledb.load(f"node_{port}.db", auto_dump=True)
    cluster = ClusterManager(port, peers)

    # ============ FRONTEND =============
    @app.route("/")
    def dashboard():
        return send_from_directory("../examples", "node_dashboard.html")

    # ============ TASKS API =============
    @app.route("/tasks", methods=["GET"])
    def get_tasks():
        """Lấy tất cả tasks"""
        all_keys = db.getall()
        tasks = []
        for key in all_keys:
            if key.startswith("task_"):
                task_data = db.get(key)
                if task_data:
                    tasks.append(task_data)
        
        # Sắp xếp theo thời gian tạo (mới nhất trước)
        tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return jsonify({"tasks": tasks})

    @app.route("/tasks", methods=["POST"])
    def create_task():
        """Tạo task mới - chỉ leader mới được tạo"""
        data = request.get_json()
        title = data.get("title")
        
        if not title:
            return jsonify({"error": "title required"}), 400
        
        # Kiểm tra xem node này có phải leader không
        if not cluster.is_leader:
            return jsonify({
                "error": "not leader", 
                "leader": cluster.current_leader
            }), 403
        
        # Tạo task mới
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "title": title,
            "completed": False,
            "created_at": datetime.now().isoformat()
        }
        
        # Lưu vào DB
        key = f"task_{task_id}"
        db.set(key, task)
        
        # Replicate sang followers
        cluster.replicate_to_followers(key, task)
        
        return jsonify(task), 201

    @app.route("/tasks/<task_id>", methods=["PUT"])
    def update_task(task_id):
        """Cập nhật task - chỉ leader mới được update"""
        if not cluster.is_leader:
            return jsonify({
                "error": "not leader", 
                "leader": cluster.current_leader
            }), 403
        
        key = f"task_{task_id}"
        task = db.get(key)
        
        if not task:
            return jsonify({"error": "task not found"}), 404
        
        # Cập nhật thông tin task
        data = request.get_json()
        if "completed" in data:
            task["completed"] = data["completed"]
        if "title" in data:
            task["title"] = data["title"]
        
        # Lưu vào DB
        db.set(key, task)
        
        # Replicate sang followers
        cluster.replicate_to_followers(key, task)
        
        return jsonify(task)

    @app.route("/tasks/<task_id>", methods=["DELETE"])
    def delete_task(task_id):
        """Xóa task - chỉ leader mới được xóa"""
        if not cluster.is_leader:
            return jsonify({
                "error": "not leader", 
                "leader": cluster.current_leader
            }), 403
        
        key = f"task_{task_id}"
        task = db.get(key)
        
        if not task:
            return jsonify({"error": "task not found"}), 404
        
        # Xóa khỏi DB
        db.rem(key)
        
        # Replicate việc xóa sang followers (gửi value=None)
        cluster.replicate_to_followers(key, None)
        
        return jsonify({"status": "deleted"})

    # ============ LEGACY API =============
    @app.route("/set", methods=["POST"])
    def set_value():
        """API cũ - set key-value"""
        data = request.get_json()
        key, value = data.get("key"), data.get("value", "")
        
        if cluster.is_leader:
            db.set(key, value)
            cluster.replicate_to_followers(key, value)
            return jsonify({"status": "ok", "role": "leader"})
        else:
            return jsonify({
                "error": "not leader", 
                "leader": cluster.current_leader
            }), 403

    @app.route("/jobs")
    def jobs():
        """API cũ - lấy tất cả jobs"""
        all_jobs = db.getall()
        result = {k: db.get(k) for k in all_jobs}
        return jsonify(result)

    # ============ REPLICATION =============
    @app.route("/replicate", methods=["POST"])
    def replicate():
        """Nhận dữ liệu replicate từ leader"""
        data = request.get_json()
        key = data["key"]
        value = data["value"]
        
        if value is None:
            # Xóa key
            if db.exists(key):
                db.rem(key)
                print(f"[FOLLOWER {port}] Xóa key={key}")
        else:
            # Set key-value
            db.set(key, value)
            print(f"[FOLLOWER {port}] Nhận bản sao key={key}")
        
        return jsonify({"status": "replicated"})

    # ============ CLUSTER MANAGEMENT =============
    @app.route("/heartbeat")
    def heartbeat():
        """Nhận heartbeat từ leader"""
        cluster.last_heartbeat = time.time()
        return jsonify({"status": "alive", "port": port})

    @app.route("/status")
    def status():
        """Trả về trạng thái node"""
        return jsonify({
            "leader": cluster.current_leader,
            "is_leader": cluster.is_leader,
            "port": cluster.port,
            "last_heartbeat": cluster.last_heartbeat
        })

    @app.route("/health")
    def health():
        """Health check endpoint"""
        return jsonify({
            "status": "ok",
            "port": cluster.port,
            "is_leader": cluster.is_leader
        })

    # ============ CLUSTER INFO =============
    @app.route("/cluster/status")
    def cluster_status():
        """Trả về thông tin toàn bộ cluster"""
        return jsonify({
            "leader": cluster.current_leader,
            "followers": cluster.peers,
            "current_node": f"http://127.0.0.1:{cluster.port}",
            "is_leader": cluster.is_leader
        })

    # Khởi động election monitor
    cluster.start_election_monitor()
    
    return app, cluster