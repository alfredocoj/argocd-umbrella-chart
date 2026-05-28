import os
from flask import Flask, jsonify, request

app = Flask(__name__)

_TODOS = [{"id": 1, "title": "initial task", "done": False}]


@app.route('/todos', methods=['GET'])
def list_todos():
    return jsonify(_TODOS), 200


@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json() or {}
    title = data.get('title')
    if not title:
        return jsonify({"error": "title required"}), 400
    new_id = max((t['id'] for t in _TODOS), default=0) + 1
    todo = {"id": new_id, "title": title, "done": False}
    _TODOS.append(todo)
    return jsonify(todo), 201


@app.route('/ready', methods=['GET'])
def readiness():
    # if env var FAIL_READY is set to 'true' returns 500 to simulate failing health
    if os.getenv('FAIL_READY', 'false').lower() == 'true':
        return jsonify({"status": "not ready"}), 500
    return jsonify({"status": "ok"}), 200


def run(host='0.0.0.0', port=8080):
    app.run(host=host, port=port)


if __name__ == '__main__':
    run()
