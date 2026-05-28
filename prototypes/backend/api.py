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
import shutil

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


def _run_generator(path: str, id: str, system: str, name: str, metadata: str, variant_id: str, **kwargs):
    metadata_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, dir='/tmp'
        ) as tmp:
            tmp.write(metadata or '')
            metadata_path = tmp.name
        return _run_sh(path, [id, system, name, f"@{metadata_path}", variant_id], **kwargs)
    finally:
        if metadata_path and os.path.exists(metadata_path):
            os.unlink(metadata_path)


def _reconcile_sqlite_schema(prototype_path: str) -> subprocess.CompletedProcess:
    """Add missing SQLite columns when a copied db has stale migration history."""
    code = r"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ.get('DJANGO_SETTINGS_MODULE', ''))
import django
django.setup()
from django.apps import apps
from django.db import connection

if connection.vendor != 'sqlite':
    raise SystemExit(0)

with connection.cursor() as cursor:
    existing_tables = set(connection.introspection.table_names(cursor))

added = []
for model in apps.get_models():
    if model._meta.proxy or model._meta.managed is False:
        continue
    table = model._meta.db_table
    if table not in existing_tables:
        continue
    with connection.cursor() as cursor:
        existing_columns = {col.name for col in connection.introspection.get_table_description(cursor, table)}
    for field in model._meta.local_fields:
        if field.column in existing_columns:
            continue
        with connection.schema_editor() as schema_editor:
            schema_editor.add_field(model, field)
        existing_columns.add(field.column)
        added.append(f"{table}.{field.column}")

if added:
    print("Added missing SQLite columns: " + ", ".join(added))
"""
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = f'{os.path.basename(prototype_path)}.settings'
    return subprocess.run(
        ["python", "manage.py", "shell", "-c", code],
        cwd=prototype_path,
        env=env,
        capture_output=True,
        text=True,
    )


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


def _is_pid_zombie(pid: int) -> bool:
    try:
        with open(f"/proc/{pid}/stat", "r") as f:
            return f.read().split()[2] == "Z"
    except (OSError, IndexError):
        return False


def _pid_cwd(pid: int) -> str | None:
    try:
        return os.path.realpath(os.readlink(f"/proc/{pid}/cwd"))
    except OSError:
        return None


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
    prototype_path = os.path.realpath(
        os.path.join(
            ROOT_DIR,
            running_prototype.get("system", ""),
            running_prototype.get("name", ""),
        )
    )
    return (
        _is_pid_alive(pid)
        and not _is_pid_zombie(pid)
        and _pid_cwd(pid) == prototype_path
        and _is_port_accepting(port)
    )


def _terminate_pid(pid: int):
    try:
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGTERM)
    except OSError:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return

    for _ in range(20):
        if not _is_pid_alive(pid) or _is_pid_zombie(pid):
            return
        time.sleep(0.1)

    try:
        os.killpg(os.getpgid(pid), signal.SIGKILL)
    except OSError:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def _stop_stale_runservers():
    subprocess.run(
        ["pkill", "-f", f"manage.py runserver 0.0.0.0:{RUNNING_PROTOTYPE_PORT}"],
        check=False,
    )
    for _ in range(20):
        if not _is_port_accepting(RUNNING_PROTOTYPE_PORT):
            return
        time.sleep(0.1)


def stop_prototype():
    with lock:
        if "id" in running_prototype:
            pid = running_prototype["pid"]
            _terminate_pid(pid)
            running_prototype.clear()
        _stop_stale_runservers()


def start_prototype(prototype_id: str, prototype_name: str, prototype_system: str):
    with lock:
        if "id" in running_prototype:
            pid = running_prototype["pid"]
            _terminate_pid(pid)
            running_prototype.clear()
        _stop_stale_runservers()

        prototype_path = os.path.join(ROOT_DIR, prototype_system, prototype_name)
        if not os.path.isdir(prototype_path):
            return None, "prototype_dir_not_found"
        
        process = subprocess.Popen(
            ["python", "manage.py", "runserver", f"0.0.0.0:{RUNNING_PROTOTYPE_PORT}", "--noreload"],
            cwd=prototype_path,
            stdout=sys.stdout,
            stderr=sys.stderr,
            start_new_session=True,
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
        running_prototype["system"] = prototype_system
        running_prototype["name"] = prototype_name
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
                "port": running_prototype["port"],
                "system": running_prototype.get("system", ""),
                "name": running_prototype.get("name", ""),
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
        _run_generator(GENERATOR_PATH, id, system, name, metadata, variant_id,
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        error_detail = (e.stderr or e.stdout or "no output captured")
        failed_path = os.path.join(ROOT_DIR, system, name)
        if os.path.isdir(failed_path):
            shutil.rmtree(failed_path, ignore_errors=True)
        app.logger.error(f"Generation failed for {name}:\n{error_detail}")
        return f"Failed to generate prototype, id={id}\n{error_detail}", 500

    # TODO: this database retrieval should be done using ids
    if 'database_prototype_name' in data:
        database_prototype_name = data.get('database_prototype_name')
        try:
            _run_sh(COPY_DATABASE_PATH, [database_prototype_name, name, system], check=True)
        except subprocess.CalledProcessError:
            return f"Failed to copy database from {database_prototype_name} to {name}", 500
        # The copied database may be from an older schema version; re-run migrate
        # so any new tables (e.g. shared_models_user) are created without losing data.
        prototype_path = os.path.join(ROOT_DIR, system, name)
        result = subprocess.run(
            ["python", "manage.py", "migrate", "--skip-checks"],
            cwd=prototype_path,
            capture_output=True,
        )
        if result.returncode != 0:
            return f"Failed to migrate database after copy for {name}", 500
        result = _reconcile_sqlite_schema(prototype_path)
        if result.returncode != 0:
            app.logger.error(f"Failed to reconcile copied database schema for {name}:\n{result.stderr or result.stdout}")
            return f"Failed to reconcile database schema after copy for {name}", 500
    return f"Generated {name} prototype", 200


@app.route('/seed', methods=['POST'])
def seed_prototype_data():
    SEED_SCRIPT = '/usr/src/prototypes/backend/seed_prototype.py'
    if not os.path.exists(SEED_SCRIPT):
        return 'Seed script not found', 404

    req_data     = request.json or {}
    # Prefer the currently-running prototype; fall back to what the caller provided.
    system_id    = running_prototype.get('system') or req_data.get('system', '')
    project_name = running_prototype.get('name')   or req_data.get('name', '')
    if not system_id or not project_name:
        return 'No prototype is running — start a prototype first, then seed', 400

    proto_path = os.path.join(ROOT_DIR, system_id, project_name)
    if not os.path.isdir(proto_path):
        return f'Prototype directory not found: {proto_path}', 404

    result = _reconcile_sqlite_schema(proto_path)
    if result.returncode != 0:
        app.logger.error(f"Failed to reconcile database schema before seed for {project_name}:\n{result.stderr or result.stdout}")
        return f'Failed to reconcile database schema before seed for {project_name}', 500

    env = os.environ.copy()
    env['PROTOTYPE_SYSTEM'] = system_id
    env['PROTOTYPE_NAME']   = project_name
    env['DJANGO_SETTINGS_MODULE'] = f'{project_name}.settings'

    result = subprocess.run(
        ['python', SEED_SCRIPT],
        capture_output=True, text=True, timeout=90, env=env,
    )
    if result.returncode != 0:
        return result.stderr or 'Seed failed', 500

    _patch_autologin(proto_path, project_name)
    return result.stdout or 'Seeded OK', 200


@app.route('/seed_script', methods=['POST'])
def seed_with_script():
    """Run a caller-supplied Python seed script in the active prototype's Django context."""
    req_data     = request.json or {}
    script       = req_data.get('script', '')
    if not script:
        return 'Missing script field', 400

    system_id    = running_prototype.get('system') or req_data.get('system', '')
    project_name = running_prototype.get('name')   or req_data.get('name', '')
    if not system_id or not project_name:
        return 'No prototype is running — start a prototype first, then seed', 400

    proto_path = os.path.join(ROOT_DIR, system_id, project_name)
    if not os.path.isdir(proto_path):
        return f'Prototype directory not found: {proto_path}', 404

    script_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='/tmp') as tmp:
            tmp.write(script)
            script_file = tmp.name

        env = os.environ.copy()
        env['PROTOTYPE_SYSTEM'] = system_id
        env['PROTOTYPE_NAME']   = project_name
        env['DJANGO_SETTINGS_MODULE'] = f'{project_name}.settings'

        result = subprocess.run(
            ['python', script_file],
            capture_output=True, text=True, timeout=90, env=env,
        )
    finally:
        if script_file and os.path.exists(script_file):
            os.unlink(script_file)

    if result.returncode != 0:
        return result.stderr or 'Seed script failed', 500

    _patch_autologin(proto_path, project_name)
    return result.stdout or 'Seeded OK', 200


def _patch_autologin(proto_path: str, project_name: str):
    AUTOLOGIN_VIEW = '''
def autologin(request):
    from django.contrib.auth import login as _login
    username = request.GET.get('as', '')
    next_url = request.GET.get('next', '')
    role_fields = [
        field.name for field in User._meta.get_fields()
        if field.name.startswith('is_')
        and field.name not in ('is_superuser', 'is_staff', 'is_active')
    ]

    def _norm(value):
        return str(value or '').strip().lower().replace('-', '_').replace(' ', '_')

    def _role_field_from(value):
        wanted = _norm(value)
        if not wanted and next_url and next_url.startswith('/'):
            wanted = _norm(next_url.strip('/').split('/', 1)[0])
        for field in role_fields:
            role = field[3:]
            if wanted in {_norm(role), _norm('demo_' + role)}:
                return field
        return None

    role_field = _role_field_from(username)
    user = User.objects.filter(username=username).first() if username else None
    if user is None and role_field:
        user = User.objects.create_user(
            username=username or role_field[3:].lower(),
            password='demo',
            **{role_field: True},
        )
    elif user is not None and role_field and not getattr(user, role_field, False):
        setattr(user, role_field, True)
        user.save(update_fields=[role_field])
    if user is None:
        user = User.objects.filter(is_superuser=False).first()
    if user:
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        _login(request, user)
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        for field in [f.name for f in user._meta.get_fields()
                      if f.name.startswith('is_') and f.name not in ('is_superuser', 'is_staff', 'is_active')]:
            if getattr(user, field, False):
                return redirect(f'/{field[3:].lower()}/')
    return redirect('/')
'''
    views_path = os.path.join(proto_path, 'authentication', 'views.py')
    urls_path  = os.path.join(proto_path, 'authentication', 'urls.py')

    if not os.path.exists(views_path):
        return

    with open(views_path) as f:
        vcontent = f.read()
    if 'def autologin' in vcontent:
        import re as _re
        vcontent = _re.sub(
            r'\ndef autologin\(request\):\n.*?(?=\ndef\s+\w+\(request\):|\Z)',
            '\n' + AUTOLOGIN_VIEW.strip() + '\n',
            vcontent,
            count=1,
            flags=_re.S,
        )
        with open(views_path, 'w') as f:
            f.write(vcontent)
    else:
        with open(views_path, 'a') as f:
            f.write(AUTOLOGIN_VIEW)

    if not os.path.exists(urls_path):
        return
    with open(urls_path) as f:
        ucontent = f.read()
    if 'autologin' not in ucontent:
        # Ensure the last path() entry before ] ends with a comma
        import re as _re
        ucontent = _re.sub(
            r'(path\([^)]+\))\s*\n(\s*\])',
            lambda m: m.group(1) + ',\n' + m.group(2)
            if not m.group(1).rstrip().endswith(',') else m.group(0),
            ucontent,
        )
        ucontent = ucontent.replace(
            ']',
            "    path('autologin', views.autologin, name='autologin'),\n]",
            1,
        )
        with open(urls_path, 'w') as f:
            f.write(ucontent)


@app.route('/remove', methods=['DELETE'])
def remove_prototype():
    REMOVER_PATH = "/usr/src/prototypes/backend/generation/remover.sh"
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

    fallback_css_path = os.path.join(TEMPLATES_DIR, 'helpers', 'tailwind_fallback.css.jinja2')
    try:
        with open(fallback_css_path, 'r') as f:
            fallback_css = f.read()
    except OSError:
        fallback_css = ''

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
        '<style>' + fallback_css + '</style>'
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
