from flask import Flask, request, jsonify, send_from_directory
import pickledb
import os
import time
import uuid
from datetime import datetime
from flask_cors import CORS
from src.cluster_manager import ClusterManager

def create_app(port, peers, all_nodes=None):
    app = Flask(__name__, static_folder="../examples", static_url_path="/")
    CORS(app)
    
    # Load PickleDB
    db = pickledb.load(f"node_{port}.db", auto_dump=True)

    if all_nodes is None:
        all_nodes = peers.copy()

    cluster = ClusterManager(port, peers, all_nodes)

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
        tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return jsonify({"tasks": tasks})

    @app.route("/tasks", methods=["POST"])
    def create_task():
        """Tạo task mới — chỉ leader mới ghi"""
        data = request.get_json()
        title = data.get("title")
        if not title:
            return jsonify({"error": "title required"}), 400

        if not cluster.is_leader:
            leader_url = cluster.current_leader or f"http://127.0.0.1:{port}"
            if not str(leader_url).startswith("http"):
                leader_url = f"http://127.0.0.1:{leader_url}"
            return jsonify({"error": "not leader", "leader": leader_url}), 403

        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "title": title,
            "completed": False,
            "created_at": datetime.now().isoformat()
        }

        db.set(f"task_{task_id}", task)
        cluster.replicate_to_followers(f"task_{task_id}", task)
        return jsonify(task), 201

    @app.route("/tasks/<task_id>", methods=["PUT"])
    def update_task(task_id):
        """Cập nhật task"""
        if not cluster.is_leader:
            leader_url = cluster.current_leader or f"http://127.0.0.1:{port}"
            if not str(leader_url).startswith("http"):
                leader_url = f"http://127.0.0.1:{leader_url}"
            return jsonify({"error": "not leader", "leader": leader_url}), 403

        key = f"task_{task_id}"
        task = db.get(key)
        if not task:
            return jsonify({"error": "task not found"}), 404

        data = request.get_json()
        if "completed" in data:
            task["completed"] = data["completed"]
        if "title" in data:
            task["title"] = data["title"]

        db.set(key, task)
        cluster.replicate_to_followers(key, task)
        return jsonify(task)

    @app.route("/tasks/<task_id>", methods=["DELETE"])
    def delete_task(task_id):
        """Xóa task"""
        if not cluster.is_leader:
            leader_url = cluster.current_leader or f"http://127.0.0.1:{port}"
            if not str(leader_url).startswith("http"):
                leader_url = f"http://127.0.0.1:{leader_url}"
            return jsonify({"error": "not leader", "leader": leader_url}), 403

        key = f"task_{task_id}"
        if not db.exists(key):
            return jsonify({"error": "task not found"}), 404

        db.rem(key)
        cluster.replicate_to_followers(key, None)
        return jsonify({"status": "deleted"})

    # ============ REPLICATION =============
    @app.route("/replicate", methods=["POST"])
    def replicate():
        """Nhận dữ liệu replicate từ leader"""
        data = request.get_json()
        key = data["key"]
        value = data["value"]

        if value is None:
            if db.exists(key):
                db.rem(key)
        else:
            db.set(key, value)

        return jsonify({"status": "replicated"})

    # ============ HEARTBEAT & CLUSTER MGMT ============
    @app.route("/heartbeat")
    def heartbeat():
        """Nhận heartbeat từ leader"""
        info = cluster.receive_heartbeat()
        cluster.current_leader = request.remote_addr or cluster.current_leader
        return jsonify(info)

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
        """Health check"""
        return jsonify({
            "status": "ok",
            "port": cluster.port,
            "is_leader": cluster.is_leader
        })

    @app.route("/cluster/status")
    def cluster_status():
        """Trả thông tin toàn cluster"""
        return jsonify({
            "leader": cluster.current_leader,
            "followers": cluster.peers,
            "current_node": f"http://127.0.0.1:{cluster.port}",
            "is_leader": cluster.is_leader
        })

    # Khởi động election monitor
    cluster.start_election_monitor()
    return app, cluster
