from flask import Flask, request, jsonify, send_from_directory
import pickledb
import os
from flask_cors import CORS
from src.cluster_manager import ClusterManager

def create_app(port, peers):
    app = Flask(__name__, static_folder="../examples", static_url_path="/")
    CORS(app)
    db = pickledb.load(f"node_{port}.db", auto_dump=True)
    cluster = ClusterManager(port, peers)

    # ============ FRONTEND =============
    @app.route("/")
    def dashboard():
        return send_from_directory("../examples", "node_dashboard.html")

    # ============ CORE API =============
    @app.route("/set", methods=["POST"])
    def set_value():
        data = request.get_json()
        key, value = data.get("key"), data.get("value", "")
        if cluster.is_leader:
            db.set(key, value)
            cluster.replicate_to_followers(key, value)
            return jsonify({"status": "ok", "role": "leader"})
        else:
            return jsonify({"error": "not leader", "leader": cluster.current_leader}), 403

    @app.route("/replicate", methods=["POST"])
    def replicate():
        data = request.get_json()
        db.set(data["key"], data["value"])
        print(f"[FOLLOWER] Nhận bản sao key={data['key']} value={data['value']}")
        return jsonify({"status": "replicated"})

    @app.route("/jobs")
    def jobs():
        all_jobs = db.getall()
        result = {k: db.get(k) for k in all_jobs}
        return jsonify(result)

    @app.route("/heartbeat")
    def heartbeat():
        cluster.last_heartbeat = time.time()
        return jsonify({"status": "alive"})

    @app.route("/status")
    def status():
        return jsonify({
            "leader": cluster.current_leader,
            "is_leader": cluster.is_leader,
            "port": cluster.port
        })

    cluster.start_election_monitor()
    return app, cluster
