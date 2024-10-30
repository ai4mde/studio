from flask import Flask, redirect, request, abort
from multiprocessing import Manager, Lock
import subprocess
import os
import time
import socket
import signal

app = Flask(__name__)

ROOT_DIR = "/usr/src/prototypes/generated_prototypes"

manager = Manager()
running_prototypes = manager.dict()
lock = Lock()

def stop_prototypes_func():
    with lock:
        for prototype_name in list(running_prototypes.keys()):
            pid, _ = running_prototypes[prototype_name]
            os.kill(pid, signal.SIGTERM)
            del running_prototypes[prototype_name]
    return True



def start_prototype(prototype_name: str):
    with lock:
        if prototype_name in running_prototypes:
            return running_prototypes[prototype_name]
        
        prototype_path = os.path.join(ROOT_DIR, prototype_name)
        print(prototype_path)
        if not os.path.isdir(prototype_path):
            return None

        port = 8020 # TODO: put in env
        process = subprocess.Popen(
            ["python", "manage.py", "runserver", f"0.0.0.0:{port}"],
            cwd=prototype_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)
        print(f"process: {process.pid}")
        if process.poll() is not None:
            return None
        print("setting")
    
        running_prototypes[prototype_name] = (process.pid, port)
        return process, port


@app.route('/run/<prototype_name>', methods=['POST'])
def run_prototype(prototype_name: str):
    stop_prototypes_func()
    result = start_prototype(prototype_name)
    if result:
        pid, port = result
        return redirect(f"http://prototype.ai4mde.localhost", code=307)
    else:
        abort(404)


@app.route('/stop_prototypes', methods=['POST'])
def stop_prototypes():
    stop_prototypes_func()
    return f"Stopped all running prototypes", 200


@app.route('/status/<prototype_name>', methods=['GET'])
def status_prototype(prototype_name: str):
    with lock:
        if prototype_name in running_prototypes:
            pid, port = running_prototypes[prototype_name]
            return {
                "prototype_name": prototype_name,
                "running": True,
                "pid": pid,
                "ip": socket.gethostbyname(socket.gethostname()),
                "port": port
            }
        else:
            return {
                "prototype_name": prototype_name,
                "running": False,
                "pid": None,
                "ip": None,
                "port": None
            }


@app.route('/generate', methods=['POST'])
def generate_prototype():
    GENERATOR_PATH = "/usr/src/prototypes/backend/generation/generator.sh"
    COPY_DATABASE_PATH = "/usr/src/prototypes/backend/generation/copy_database.sh"
    data = request.json
    prototype_name = data.get('prototype_name')
    metadata = data.get('metadata')
    try:
        subprocess.run([GENERATOR_PATH, prototype_name, metadata], check=True)
    except subprocess.CalledProcessError:
        return f"Failed to generate {prototype_name} prototype", 500
    
    if 'database_prototype_name' in data:
        database_prototype_name = data.get('database_prototype_name')
        try:
            subprocess.run([COPY_DATABASE_PATH, database_prototype_name, prototype_name], check=True)
        except subprocess.CalledProcessError:
            return f"Failed to copy database from {database_prototype_name} to {prototype_name}", 500
    return f"Generated {prototype_name} prototype", 200


@app.route('/remove', methods=['DELETE'])
def remove_prototype():
    REMOVER_PATH = "/usr/src/prototypes/backend/generation/remover.sh"
    data = request.json
    prototype_name = data.get('prototype_name')
    if prototype_name in running_prototypes:
        pid, _ = running_prototypes[prototype_name]
        os.kill(pid, signal.SIGTERM)
        del running_prototypes[prototype_name]
    try:
        subprocess.run([REMOVER_PATH, prototype_name], check=True)
    except subprocess.CalledProcessError:
        return f"Failed to remove {prototype_name} prototype", 500
    return f"Removed {prototype_name} prototype", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8010, debug=True)
