from flask import Flask, redirect, request, abort
from multiprocessing import Manager, Lock
import subprocess
import os
import time
import socket
import signal
import sys

app = Flask(__name__)

ROOT_DIR = "/usr/src/prototypes/generated_prototypes"

RUNNING_PROTOTYPE_PROTO = os.environ.get('RUNNING_PROTOTYPE_PROTO', "http://")
RUNNING_PROTOTYPE_HOST = os.environ.get('RUNNING_PROTOTYPE_HOST', "prototype.ai4mde.localhost")
RUNNING_PROTOTYPE_PORT = os.environ.get('RUNNING_PROTOTYPE_PORT', 8020)


manager = Manager()
lock = Lock()

running_prototype = manager.dict()


def stop_prototype():
    with lock:
        if "id" in running_prototype:
            pid = running_prototype["pid"]
            os.kill(pid, signal.SIGTERM)
            running_prototype.clear()


def start_prototype(prototype_id: str, prototype_name: str, prototype_system: str):
    with lock:
        if "id" in running_prototype:
            pid = running_prototype["pid"]
            os.kill(pid, signal.SIGTERM)
            running_prototype.clear()

        prototype_path = os.path.join(ROOT_DIR, prototype_system, prototype_name)
        if not os.path.isdir(prototype_path):
            return None
        
        process = subprocess.Popen(
            ["python", "manage.py", "runserver", f"0.0.0.0:{RUNNING_PROTOTYPE_PORT}"],
            cwd=prototype_path,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        time.sleep(2)
        if process.poll() is not None:
            return None

        running_prototype["id"] = prototype_id
        running_prototype["pid"] = process.pid
        running_prototype["port"] = RUNNING_PROTOTYPE_PORT
        return process, RUNNING_PROTOTYPE_PORT


@app.route('/run', methods=['POST'])
def run_prototype():
    stop_prototype()
    data = request.json
    id = data.get('id')
    name = data.get('name')
    system = data.get('system')
    result = start_prototype(id, name, system)
    if result:
        _, port = result
        return redirect(f"{RUNNING_PROTOTYPE_PROTO}{RUNNING_PROTOTYPE_HOST}:{RUNNING_PROTOTYPE_PORT}", code=307)
    else:
        abort(404)


@app.route('/stop_prototypes', methods=['POST'])
def stop_prototypes():
    stop_prototype()
    return f"Stopped all running prototypes", 200


@app.route('/active_prototype', methods=['GET'])
def get_active_prototype():
    with lock:
        if "id" in running_prototype:
            return {
                "prototype_id": running_prototype["id"],
                "running": True,
                "pid": running_prototype["pid"],
                "ip": socket.gethostbyname(socket.gethostname()),
                "port": running_prototype["port"]
            }
        else:
            return {
                "prototype_id": None,
                "running": False,
                "pid": None,
                "ip": None,
                "port": None
            }


@app.route('/generate', methods=['POST'])
def generate_prototype():
    GENERATOR_PATH = "/usr/src/prototypes/backend/generation/generator.sh" # TODO: put in env
    COPY_DATABASE_PATH = "/usr/src/prototypes/backend/generation/copy_database.sh"
    data = request.json
    id = data.get('id')
    name = data.get('name')
    system = data.get('system')
    metadata = data.get('metadata')
    try:
        subprocess.run([GENERATOR_PATH, id, system, name, metadata], check=True)
    except subprocess.CalledProcessError:
        return f"Failed to generate prototype, id={id}", 500

    # TODO: this database retrieval should be done using ids
    if 'database_prototype_name' in data:
        database_prototype_name = data.get('database_prototype_name')
        try:
            subprocess.run([COPY_DATABASE_PATH, database_prototype_name, name, system], check=True)
        except subprocess.CalledProcessError:
            return f"Failed to copy database from {database_prototype_name} to {name}", 500
    return f"Generated {name} prototype", 200


@app.route('/remove', methods=['DELETE'])
def remove_prototype():
    REMOVER_PATH = "/usr/src/prototypes/backend/generation/remover.sh" # TODO: put in env
    data = request.json
    id = data.get('id')
    name = data.get('name')
    system = data.get('system')
    if "id" in running_prototype and running_prototype["id"] == id:
        stop_prototype()
    try:
        subprocess.run([REMOVER_PATH, id, name, system], check=True)
    except subprocess.CalledProcessError:
        return f"Failed to remove {name} prototype, id={id}", 500
    return f"Removed {name} prototype, id={id}", 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=os.environ.get('PORT', 8010), debug=False)
