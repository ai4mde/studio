from flask import Flask, redirect, request, abort
from multiprocessing import Manager, Lock
import subprocess
import os
import re
import tempfile
import time
import socket
import signal
import sys
import jinja2

app = Flask(__name__)


def _run_sh(path: str, args: list, **kwargs):
    """Execute a shell script after stripping Windows CRLF line endings.

    Scripts are volume-mounted from a Windows host so they may contain \\r\\n.
    We write a de-CRLF'd copy to /tmp so we never mutate the mounted file.
    """
    with open(path, 'r', errors='replace') as f:
        src = f.read().replace('\r\n', '\n').replace('\r', '\n')
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.sh', delete=False, dir='/tmp'
    ) as tmp:
        tmp.write(src)
        tmp_path = tmp.name
    os.chmod(tmp_path, 0o755)
    try:
        return subprocess.run([tmp_path] + args, **kwargs)
    finally:
        os.unlink(tmp_path)

ROOT_DIR = "/usr/src/prototypes/generated_prototypes"

RUNNING_PROTOTYPE_PROTO = os.environ.get('RUNNING_PROTOTYPE_PROTO', "http://")
RUNNING_PROTOTYPE_HOST = os.environ.get('RUNNING_PROTOTYPE_HOST', "prototype.ai4mde.localhost")
RUNNING_PROTOTYPE_PORT = os.environ.get('RUNNING_PROTOTYPE_PORT', 8020)


manager = Manager()
lock = Lock()

running_prototype = manager.dict()


def _is_pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _is_port_accepting(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def _running_prototype_is_healthy() -> bool:
    if "id" not in running_prototype:
        return False
    pid = int(running_prototype["pid"])
    port = int(running_prototype["port"])
    return _is_pid_alive(pid) and _is_port_accepting(port)


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
            return None, "prototype_dir_not_found"
        
        process = subprocess.Popen(
            ["python", "manage.py", "runserver", f"0.0.0.0:{RUNNING_PROTOTYPE_PORT}"],
            cwd=prototype_path,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        ready = False
        for _ in range(16):
            if process.poll() is not None:
                break
            if _is_port_accepting(RUNNING_PROTOTYPE_PORT):
                ready = True
                break
            time.sleep(0.5)

        if not ready:
            if process.poll() is None:
                process.terminate()
            return None, "prototype_startup_failed"

        running_prototype["id"] = prototype_id
        running_prototype["pid"] = process.pid
        running_prototype["port"] = RUNNING_PROTOTYPE_PORT
        return (process, RUNNING_PROTOTYPE_PORT), None


@app.route('/run', methods=['POST'])
def run_prototype():
    stop_prototype()
    data = request.json
    id = data.get('id')
    name = data.get('name')
    system = data.get('system')
    result, error_code = start_prototype(id, name, system)
    if result:
        _, port = result
        return redirect(f"{RUNNING_PROTOTYPE_PROTO}{RUNNING_PROTOTYPE_HOST}:{RUNNING_PROTOTYPE_PORT}", code=307)
    else:
        if error_code == "prototype_dir_not_found":
            abort(404)
        return "Prototype failed to start. Check studio-prototypes logs for Django errors.", 500


@app.route('/stop_prototypes', methods=['POST'])
def stop_prototypes():
    stop_prototype()
    return f"Stopped all running prototypes", 200


@app.route('/active_prototype', methods=['GET'])
def get_active_prototype():
    with lock:
        if "id" in running_prototype and not _running_prototype_is_healthy():
            running_prototype.clear()

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
    variant_id = data.get('variant_id', '1')
    try:
        _run_sh(GENERATOR_PATH, [id, system, name, metadata, variant_id], check=True)
    except subprocess.CalledProcessError:
        return f"Failed to generate prototype, id={id}", 500

    # TODO: this database retrieval should be done using ids
    if 'database_prototype_name' in data:
        database_prototype_name = data.get('database_prototype_name')
        try:
            _run_sh(COPY_DATABASE_PATH, [database_prototype_name, name, system], check=True)
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
        _run_sh(REMOVER_PATH, [id, name, system], check=True)
    except subprocess.CalledProcessError:
        return f"Failed to remove {name} prototype, id={id}", 500
    return f"Removed {name} prototype, id={id}", 200


TEMPLATES_DIR = "/usr/src/prototypes/backend/generation/templates"

_PREVIEW_SAMPLE = {
    'application_name': 'MyApp',
    'settings': {'manager_access': False},
    'categories': [],
    'pages': [],
    'page': {
        'display_name': 'Products',
        'category': 'Shop',
        'type': 'normal',
        'section_components': [
            {
                'display_name': 'Featured Items',
                'attributes': ['name', 'category', 'price'],
                'primary_model_list': [
                    {'name': 'Product Alpha', 'category': 'Electronics', 'price': '29.99'},
                    {'name': 'Product Beta',  'category': 'Fashion',     'price': '59.99'},
                    {'name': 'Product Gamma', 'category': 'Books',       'price': '14.99'},
                    {'name': 'Product Delta', 'category': 'Home',        'price': '89.99'},
                    {'name': 'Product Epsilon','category': 'Sports',     'price': '45.00'},
                    {'name': 'Product Zeta',  'category': 'Electronics', 'price': '199.99'},
                ],
            }
        ],
    },
}


@app.after_request
def _cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/preview_template', methods=['GET'])
def preview_template():
    variant = request.args.get('variant', '1')
    if variant not in ('1', '2', '3'):
        abort(400)

    path = os.path.join(TEMPLATES_DIR, f'page_v{variant}.html.jinja2')
    if not os.path.exists(path):
        abort(404)

    with open(path, 'r') as f:
        content = f.read()

    # Strip Jinja2 template-inheritance wrappers — page_vN templates are
    # designed as code-gen sources that extend a Django base; we want only
    # the block content for a self-contained preview.
    content = re.sub(r'\{%-?\s*extends\b[^\%]*%\}\s*\n?', '', content)
    content = re.sub(r'\{%-?\s*block\s+content\s*-?%\}\s*\n?', '', content)
    content = re.sub(r'\{%-?\s*endblock\b[^\%]*-?%\}\s*\n?', '', content)

    full_html = (
        '<!doctype html><html><head>'
        '<meta charset="UTF-8">'
        '<script src="https://cdn.tailwindcss.com"></script>'
        '</head><body>'
        + content +
        '</body></html>'
    )

    env = jinja2.Environment()
    try:
        rendered = env.from_string(full_html).render(**_PREVIEW_SAMPLE)
    except Exception as exc:
        return str(exc), 500, {'Content-Type': 'text/plain'}

    return rendered, 200, {'Content-Type': 'text/html; charset=utf-8'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8010), debug=False)
