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
import threading
import jinja2
import shutil

app = Flask(__name__)


def _private_temp_dir() -> str:
    path = os.environ.get('PROTOTYPE_TEMP_DIR', '/usr/src/prototypes/tmp')
    os.makedirs(path, mode=0o700, exist_ok=True)
    os.chmod(path, 0o700)
    return path


def _run_sh(path: str, args: list, **kwargs):
    """Execute a shell script after stripping Windows CRLF line endings.

    Scripts are volume-mounted from a Windows host so they may contain \\r\\n.
    We write a de-CRLF'd copy to a private temp dir so we never mutate the mounted file.
    """
    script_path = _safe_script_path(path)
    with open(script_path, 'r', errors='replace') as f:
        src = f.read().replace('\r\n', '\n').replace('\r', '\n')
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.sh', delete=False, dir=_private_temp_dir()
    ) as tmp:
        tmp.write(src)
        tmp_path = tmp.name
    os.chmod(tmp_path, 0o700)
    try:
        return subprocess.run([tmp_path] + args, **kwargs)
    finally:
        os.unlink(tmp_path)


def _run_generator(path: str, id: str, system: str, name: str, metadata: str, variant_id: str, **kwargs):
    metadata_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, dir=_private_temp_dir()
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
from django.db.models import NOT_PROVIDED
from django.db import OperationalError, connection

if connection.vendor != 'sqlite':
    raise SystemExit(0)

def cleanup_sqlite_rebuild_tables():
    dropped = []
    with connection.cursor() as cursor:
        table_names = list(connection.introspection.table_names(cursor))
        for table_name in table_names:
            if not table_name.startswith("new__"):
                continue
            quoted_name = connection.ops.quote_name(table_name)
            cursor.execute(f"DROP TABLE IF EXISTS {quoted_name}")
            dropped.append(table_name)
    if dropped:
        print("Dropped stale SQLite rebuild tables: " + ", ".join(dropped))

def reconcile_missing_columns():
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
            cursor.execute(f"SELECT COUNT(*) FROM {connection.ops.quote_name(table)}")
            row_count = cursor.fetchone()[0]
        for field in model._meta.local_fields:
            if field.column in existing_columns:
                continue
            should_relax_required_field = (
                row_count > 0
                and not field.null
                and not field.primary_key
                and not field.auto_created
                and field.default is NOT_PROVIDED
            )
            original_null = field.null
            if should_relax_required_field:
                field.null = True
            with connection.schema_editor() as schema_editor:
                try:
                    schema_editor.add_field(model, field)
                finally:
                    field.null = original_null
            existing_columns.add(field.column)
            added.append(f"{table}.{field.column}")
            if should_relax_required_field:
                added[-1] += " (nullable for copied rows)"

    if added:
        print("Added missing SQLite columns: " + ", ".join(added))

cleanup_sqlite_rebuild_tables()
try:
    reconcile_missing_columns()
except OperationalError as exc:
    message = str(exc)
    if "new__" not in message or "already exists" not in message:
        raise
    cleanup_sqlite_rebuild_tables()
    reconcile_missing_columns()
"""
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = f'{os.path.basename(prototype_path)}.settings'
    return subprocess.run(
        ["python", MANAGE_PY, "shell", "-c", code],
        cwd=prototype_path,
        env=env,
        capture_output=True,
        text=True,
    )


ROOT_DIR = "/usr/src/prototypes/generated_prototypes"
SCRIPT_ROOT_DIR = "/usr/src/prototypes/backend/generation"
MANAGE_PY = "manage.py"
_SAFE_PATH_PART_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

RUNNING_PROTOTYPE_PROTO = os.environ.get('RUNNING_PROTOTYPE_PROTO', "http://")
RUNNING_PROTOTYPE_HOST = os.environ.get('RUNNING_PROTOTYPE_HOST', "prototype.ai4mde.localhost")
RUNNING_PROTOTYPE_PORT = os.environ.get('RUNNING_PROTOTYPE_PORT', 8020)
RUNNING_PROTOTYPE_PUBLIC_PROTO = os.environ.get('RUNNING_PROTOTYPE_PUBLIC_PROTO', RUNNING_PROTOTYPE_PROTO)
RUNNING_PROTOTYPE_PUBLIC_HOST = os.environ.get('RUNNING_PROTOTYPE_PUBLIC_HOST', RUNNING_PROTOTYPE_HOST)
RUNNING_PROTOTYPE_PUBLIC_PORT = os.environ.get('RUNNING_PROTOTYPE_PUBLIC_PORT', "")


def _running_prototype_public_url() -> str:
    port = str(RUNNING_PROTOTYPE_PUBLIC_PORT or "").strip()
    suffix = f":{port}" if port else ""
    return f"{RUNNING_PROTOTYPE_PUBLIC_PROTO}{RUNNING_PROTOTYPE_PUBLIC_HOST}{suffix}"


def _safe_path_part(value: str) -> str:
    part = str(value or "").strip()
    if not part or part in {".", ".."} or not _SAFE_PATH_PART_RE.fullmatch(part):
        raise ValueError("invalid prototype path component")
    return part


def _safe_script_path(path: str) -> str:
    root = os.path.realpath(SCRIPT_ROOT_DIR)
    candidate = os.path.realpath(path)
    if os.path.commonpath([root, candidate]) != root:
        raise ValueError("script path escapes generation directory")
    if not candidate.endswith(".sh"):
        raise ValueError("script path must reference a shell script")
    return candidate


def _prototype_path(system_id: str, project_name: str) -> str:
    root = os.path.realpath(ROOT_DIR)
    system = _safe_path_part(system_id)
    name = _safe_path_part(project_name)
    candidate = os.path.realpath(os.path.join(root, system, name))
    if os.path.commonpath([root, candidate]) != root:
        raise ValueError("prototype path escapes root directory")
    return candidate


def _safe_child_path(root_path: str, *parts: str) -> str:
    root = os.path.realpath(root_path)
    candidate = os.path.realpath(os.path.join(root, *parts))
    if os.path.commonpath([root, candidate]) != root:
        raise ValueError("path escapes root directory")
    return candidate


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
    try:
        prototype_path = _prototype_path(
            running_prototype.get("system", ""),
            running_prototype.get("name", ""),
        )
    except ValueError:
        return False
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
        ["pkill", "-f", f"{MANAGE_PY} runserver 0.0.0.0:{RUNNING_PROTOTYPE_PORT}"],
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

        try:
            safe_id = _safe_path_part(prototype_id)
            safe_name = _safe_path_part(prototype_name)
            safe_system = _safe_path_part(prototype_system)
            prototype_path = _prototype_path(safe_system, safe_name)
        except ValueError:
            return None, "invalid_prototype_path"
        if not os.path.isdir(prototype_path):
            return None, "prototype_dir_not_found"
        
        process = subprocess.Popen(
            ["python", MANAGE_PY, "runserver", f"0.0.0.0:{RUNNING_PROTOTYPE_PORT}", "--noreload"],
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

        running_prototype["id"] = safe_id
        running_prototype["pid"] = process.pid
        running_prototype["port"] = RUNNING_PROTOTYPE_PORT
        running_prototype["system"] = safe_system
        running_prototype["name"] = safe_name
        return (process, RUNNING_PROTOTYPE_PORT), None


@app.route('/run', methods=['POST'])
def run_prototype():
    stop_prototype()
    data = request.json or {}
    id = data.get('id')
    name = data.get('name')
    system = data.get('system')
    try:
        safe_id = _safe_path_part(id)
        safe_name = _safe_path_part(name)
        safe_system = _safe_path_part(system)
    except ValueError:
        return "Invalid prototype identifier", 400
    result, error_code = start_prototype(safe_id, safe_name, safe_system)
    if result:
        return redirect(_running_prototype_public_url(), code=307)
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
                "url": _running_prototype_public_url(),
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
    data = request.json or {}
    id = data.get('id')
    name = data.get('name')
    system = data.get('system')
    metadata = data.get('metadata')
    variant_id = data.get('variant_id', '1')
    try:
        safe_id = _safe_path_part(id)
        safe_name = _safe_path_part(name)
        safe_system = _safe_path_part(system)
        safe_variant_id = _safe_path_part(variant_id)
    except ValueError:
        return "Invalid prototype request", 400

    try:
        _run_generator(GENERATOR_PATH, safe_id, safe_system, safe_name, metadata, safe_variant_id,
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        failed_path = _prototype_path(safe_system, safe_name)
        if os.path.isdir(failed_path):
            shutil.rmtree(failed_path, ignore_errors=True)
        app.logger.exception("Generation failed with return code %s", e.returncode)
        return "Failed to generate prototype", 500

    # TODO: this database retrieval should be done using ids
    if 'database_prototype_name' in data:
        try:
            database_prototype_name = _safe_path_part(data.get('database_prototype_name'))
        except ValueError:
            return "Invalid database prototype name", 400
        try:
            _run_sh(COPY_DATABASE_PATH, [database_prototype_name, safe_name, safe_system], check=True)
        except subprocess.CalledProcessError:
            return "Failed to copy database", 500
        # The copied database may be from an older schema version; re-run migrate
        # so any new tables (e.g. shared_models_user) are created without losing data.
        prototype_path = _prototype_path(safe_system, safe_name)
        result = subprocess.run(
            ["python", MANAGE_PY, "migrate", "--skip-checks"],
            cwd=prototype_path,
            capture_output=True,
        )
        if result.returncode != 0:
            return "Failed to migrate database after copy", 500
        result = _reconcile_sqlite_schema(prototype_path)
        if result.returncode != 0:
            app.logger.error("Failed to reconcile copied database schema")
            return "Failed to reconcile database schema after copy", 500
    return "Generated prototype", 200


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

    try:
        system_id = _safe_path_part(system_id)
        project_name = _safe_path_part(project_name)
        proto_path = _prototype_path(system_id, project_name)
    except ValueError:
        return 'Invalid prototype path', 400
    if not os.path.isdir(proto_path):
        return 'Prototype directory not found', 404

    result = _reconcile_sqlite_schema(proto_path)
    if result.returncode != 0:
        app.logger.error("Failed to reconcile database schema before seed for %s", project_name)
        return 'Failed to reconcile database schema before seed', 500

    env = os.environ.copy()
    env['PROTOTYPE_SYSTEM'] = system_id
    env['PROTOTYPE_NAME']   = project_name
    env['DJANGO_SETTINGS_MODULE'] = f'{project_name}.settings'

    result = subprocess.run(
        ['python', SEED_SCRIPT],
        capture_output=True, text=True, timeout=90, env=env,
    )
    if result.returncode != 0:
        return 'Seed failed', 500

    _patch_autologin(proto_path, project_name)
    return 'Seeded OK', 200



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
        candidates = []
        if value:
            candidates.append(_norm(value))
        if next_url and next_url.startswith('/'):
            candidates.append(_norm(next_url.strip('/').split('/', 1)[0]))
        for wanted in candidates:
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
    views_path = _safe_child_path(proto_path, 'authentication', 'views.py')
    urls_path = _safe_child_path(proto_path, 'authentication', 'urls.py')

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
    data = request.json or {}
    id = data.get('id')
    name = data.get('name')
    system = data.get('system')
    try:
        safe_id = _safe_path_part(id)
        safe_name = _safe_path_part(name)
        safe_system = _safe_path_part(system)
    except ValueError:
        return "Invalid prototype identifier", 400
    if "id" in running_prototype and running_prototype["id"] == safe_id:
        stop_prototype()
    try:
        _run_sh(REMOVER_PATH, [safe_id, safe_name, safe_system], check=True)
    except subprocess.CalledProcessError:
        return "Failed to remove prototype", 500
    return "Removed prototype", 200


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

    path = _safe_child_path(TEMPLATES_DIR, f'page_v{variant}.html.jinja2')
    if not os.path.exists(path):
        abort(404)

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    fallback_css_path = _safe_child_path(TEMPLATES_DIR, 'helpers', 'tailwind_fallback.css.jinja2')
    try:
        with open(fallback_css_path, 'r', encoding='utf-8') as f:
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
    except Exception:
        return "Failed to render preview template", 500, {'Content-Type': 'text/plain'}

    return rendered, 200, {'Content-Type': 'text/html; charset=utf-8'}


def _watchdog():
    while True:
        time.sleep(30)
        try:
            with lock:
                if "id" not in running_prototype:
                    continue
                if _running_prototype_is_healthy():
                    continue
                prototype_id = running_prototype.get("id")
                prototype_name = running_prototype.get("name")
                prototype_system = running_prototype.get("system")
            app.logger.warning(f"Watchdog: prototype {prototype_name} is unhealthy, restarting...")
            start_prototype(prototype_id, prototype_name, prototype_system)
            app.logger.info(f"Watchdog: restarted {prototype_name}")
        except Exception:
            app.logger.exception("Watchdog error")


_watchdog_thread = threading.Thread(target=_watchdog, daemon=True)
_watchdog_thread.start()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8010), debug=False)
