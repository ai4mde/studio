from flask import Flask, redirect, request, abort
import subprocess
import os
import time

app = Flask(__name__)

ROOT_DIR = "../prototypes"

running_prototypes = {}


def run_prototype(prototype_name: str):
    if prototype_name in running_prototypes:
        return running_prototypes[prototype_name]
    
    prototype_path = os.path.join(ROOT_DIR, prototype_name)

    if not os.path.isdir(prototype_path):
        return None

    process = subprocess.Popen(
        ["python", "manage.py", "runserver", "0.0.0.0:8020"], # TODO: manage ports
        cwd=prototype_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(4)
    
    if process.poll() is not None:
        return None

    running_prototypes[prototype_name] = process
    return process


@app.route('/prototypes/<prototype_name>', methods=['GET'])
def start_prototype(prototype_name: str):
    process = run_prototype(prototype_name)
    if process:
        return redirect(f'http://127.0.0.1:8000') # TODO
    else:
        abort(404)


@app.route('/stop/<prototype_name>', methods=['GET'])
def stop_prototype(prototype_name: str):
    process = running_prototypes.pop(prototype_name, None)
    if process:
        process.terminate()
        process.wait()
        return f"{prototype_name} stopped", 200
    else:
        abort(404)


@app.route('/status/<prototype_name>', methods=['GET'])
def status_prototype(prototype_name: str):
    if prototype_name in running_prototypes:
        return f"{prototype_name} is running", 200
    else:
        return f"{prototype_name} is not running", 404


@app.route('/generate', methods=['POST'])
def generate_prototype():
    GENERATOR_PATH="/usr/src/prototypes/backend/generation/generator.sh"
    data = request.json
    prototype_name = data.get('prototype_name')
    metadata = data.get('metadata')
    try:
        subprocess.run([GENERATOR_PATH, prototype_name, metadata], check=True)
    except:
        return f"Failed to generate {prototype_name} prototype", 404
    return f"Generated {prototype_name} prototype", 200


@app.route('/remove', methods=['DELETE'])
def remove_prototype():
    REMOVER_PATH="/usr/src/prototypes/backend/generation/remover.sh"
    data = request.json
    prototype_name = data.get('prototype_name')
    try:
        subprocess.run([REMOVER_PATH, prototype_name], check=True)
    except:
        return f"Failed to remove {prototype_name} prototype", 404
    return f"Removed {prototype_name} prototype", 200

    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8010, debug=True)
