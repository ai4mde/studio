from flask import Flask, redirect, request, abort
from multiprocessing import Manager, Lock
import json
import tempfile
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
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            running_prototype.clear()


def start_prototype(prototype_id: str, prototype_name: str, prototype_system: str):
    with lock:
        if "id" in running_prototype:
            pid = running_prototype["pid"]
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            running_prototype.clear()

        prototype_path = os.path.join(ROOT_DIR, prototype_system, prototype_name)
        if not os.path.isdir(prototype_path):
            return None

        # subprocess.run(
        #     ["python", "manage.py", "migrate", "--run-syncdb"],
        #     cwd=prototype_path,
        #     stdout=sys.stdout,
        #     stderr=sys.stderr,
        # )
        # subprocess.run(
        #     ["python", "manage.py", "createsuperuser", "--no-input"],
        #     cwd=prototype_path,
        #     stdout=sys.stdout,
        #     stderr=sys.stderr,
        #     env={**os.environ,
        #          "DJANGO_SUPERUSER_USERNAME": "admin",
        #          "DJANGO_SUPERUSER_PASSWORD": "sequoias",
        #          "DJANGO_SUPERUSER_EMAIL": "admin@localhost"},
        # )
        # # Grant all custom role flags to admin so login works
        # subprocess.run(
        #     ["python", "manage.py", "shell", "-c",
        #      "from shared_models.models import User; u=User.objects.get(username='admin'); "
        #      "[setattr(u, f.name, True) for f in u._meta.get_fields() "
        #      "if f.name.startswith('is_') and f.name not in ('is_staff','is_superuser','is_active')]; "
        #      "u.save()"],
        #     cwd=prototype_path,
        #     stdout=sys.stdout,
        #     stderr=sys.stderr,
        # )

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


@app.route('/overwrite_views', methods=['POST'])
def overwrite_views():
    """
    Called by the API agent's generate_node after LLM-based view generation.
    Writes the LLM-produced views.py directly into the generated prototype directory,
    replacing whatever the Jinja2 template produced.
    """
    data = request.json
    system_id = data.get('system_id', '').strip()
    project_name = data.get('project_name', '').strip()
    application_name = data.get('application_name', '').strip()
    views_content = data.get('views_content', '')

    if not all([system_id, project_name, application_name, views_content]):
        abort(400)

    views_path = os.path.join(
        ROOT_DIR, system_id, project_name, application_name, "views.py"
    )

    if not os.path.exists(os.path.dirname(views_path)):
        abort(404)

    try:
        with open(views_path, 'w') as fh:
            fh.write(views_content)
    except OSError as exc:
        abort(500)

    return {"overwritten": views_path}, 200


@app.route('/overwrite_base_template', methods=['POST'])
def overwrite_base_template():
    """
    Called by the API agent's generate_node after UI Designer builds Tailwind base.html.
    Writes the generated base.html and style CSS into the prototype directory.
    """
    data = request.json
    system_id = data.get('system_id', '').strip()
    project_name = data.get('project_name', '').strip()
    application_name = data.get('application_name', '').strip()
    base_html = data.get('base_html', '')
    style_css = data.get('style_css', '')

    if not all([system_id, project_name, application_name]):
        abort(400)

    base_html_path = os.path.join(
        ROOT_DIR, system_id, project_name, application_name,
        "templates", f"{application_name}_base.html"
    )
    css_path = os.path.join(
        ROOT_DIR, system_id, project_name, application_name,
        "static", application_name, f"{application_name}_style.css"
    )

    overwritten = []

    if base_html:
        base_dir = os.path.dirname(base_html_path)
        if not os.path.exists(base_dir):
            abort(404)
        try:
            with open(base_html_path, 'w') as fh:
                fh.write(base_html)
            overwritten.append(base_html_path)
        except OSError:
            abort(500)

    if style_css:
        css_dir = os.path.dirname(css_path)
        if not os.path.exists(css_dir):
            abort(404)
        try:
            with open(css_path, 'w') as fh:
                fh.write(style_css)
            overwritten.append(css_path)
        except OSError:
            abort(500)

    return {"overwritten": overwritten}, 200


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
    metadata_path = None
    try:
        metadata_payload = metadata if isinstance(metadata, str) else json.dumps(metadata, ensure_ascii=False)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.json', delete=False) as fh:
            fh.write(metadata_payload)
            metadata_path = fh.name
        subprocess.run([GENERATOR_PATH, id, system, name, f"@{metadata_path}"], check=True)
    except subprocess.CalledProcessError:
        return f"Failed to generate prototype, id={id}", 500
    finally:
        if metadata_path and os.path.exists(metadata_path):
            os.unlink(metadata_path)

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
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8010), debug=False)
