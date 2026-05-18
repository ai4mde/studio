import sys, os, json

system_id    = os.environ.get('PROTOTYPE_SYSTEM', '')
project_name = os.environ.get('PROTOTYPE_NAME', '')

if not system_id or not project_name:
    print('ERROR: PROTOTYPE_SYSTEM and PROTOTYPE_NAME must be set', flush=True)
    sys.exit(1)

proto_path = f'/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}'
print(f'Seeding prototype: {project_name}  path: {proto_path}', flush=True)

if not os.path.isdir(proto_path):
    print(f'ERROR: prototype directory not found: {proto_path}', flush=True)
    sys.exit(1)

seed_path = os.path.join(
    '/usr/src/prototypes/generated_prototypes', system_id, 'seed_data.json'
)
if not os.path.exists(seed_path):
    print(f'ERROR: seed_data.json not found at {seed_path}', flush=True)
    print('Run the seed endpoint — it generates seed_data.json via Claude first.', flush=True)
    sys.exit(1)

with open(seed_path) as f:
    data = json.load(f)

if proto_path not in sys.path:
    sys.path.insert(0, proto_path)

os.environ['DJANGO_SETTINGS_MODULE'] = f'{project_name}.settings'

import django
django.setup()

from django.conf import settings as _dj_settings
from django.apps import apps as django_apps

print(f'Database: {_dj_settings.DATABASES["default"]["NAME"]}', flush=True)

User = django_apps.get_model('shared_models', 'User')

# ── Clear in reverse dependency order ─────────────────────────────────────────
order = data.get('order', [])
for model_name in reversed(order):
    try:
        Model = django_apps.get_model('shared_models', model_name)
        Model.objects.all().delete()
    except Exception as e:
        print(f'  Warning: could not clear {model_name}: {e}', flush=True)
User.objects.filter(is_superuser=False).delete()
print('Cleared existing data.', flush=True)

# ── Create user accounts ───────────────────────────────────────────────────────
valid_user_fields = {f.name for f in User._meta.get_fields() if hasattr(f, 'column')}
for u_data in data.get('users', []):
    u_data = dict(u_data)
    password = u_data.pop('password', 'demo1234')
    username = u_data.pop('username')
    u_data = {k: v for k, v in u_data.items() if k in valid_user_fields}
    u, created = User.objects.get_or_create(username=username, defaults=u_data)
    if created:
        u.set_password(password)
        u.save()
print(f'Created {User.objects.filter(is_superuser=False).count()} users.', flush=True)

# ── Insert records in dependency order ────────────────────────────────────────
for model_name in order:
    try:
        Model = django_apps.get_model('shared_models', model_name)
        # Identify FK relation fields to skip — they require object references,
        # but the seed data already has the corresponding *_id CharField values.
        fk_names = {
            f.name
            for f in Model._meta.get_fields()
            if hasattr(f, 'many_to_one') and f.many_to_one and not f.auto_created
        }
        records = data.get('records', {}).get(model_name, [])
        for record in records:
            clean = {k: v for k, v in record.items() if k not in fk_names}
            Model.objects.create(**clean)
        print(f'  {model_name}: {len(records)} records', flush=True)
    except Exception as e:
        print(f'  Warning: could not seed {model_name}: {e}', flush=True)

# ── Seed demo active process nodes (one per actor role) ───────────────────────
try:
    Process = django_apps.get_model('workflow_engine', 'Process')
    ActionNode = django_apps.get_model('workflow_engine', 'ActionNode')
    ActiveProcess = django_apps.get_model('workflow_engine', 'ActiveProcess')
    ActiveProcessNode = django_apps.get_model('workflow_engine', 'ActiveProcessNode')
    ActionLog = django_apps.get_model('workflow_engine', 'ActionLog')

    AssociatedModelInstance = django_apps.get_model('workflow_engine', 'AssociatedModelInstance')
    ActiveConvergencePoint = django_apps.get_model('workflow_engine', 'ActiveConvergencePoint')
    AssociatedModelInstance.objects.all().delete()
    ActiveConvergencePoint.objects.all().delete()
    ActiveProcessNode.objects.all().delete()
    ActionLog.objects.all().delete()
    ActiveProcess.objects.all().delete()

    process = Process.objects.first()
    if process:
        actors_done = set()
        for node in ActionNode.objects.filter(url__isnull=False).order_by('id'):
            if node.actor in actors_done:
                continue
            user = User.objects.filter(**{f"is_{node.actor}": True}).first()
            if user:
                active_process = ActiveProcess.objects.create(process=process)
                ActiveProcessNode.objects.create(
                    active_process=active_process,
                    action_node=node,
                    user=user,
                )
                ActionLog.objects.create(
                    status="STARTED",
                    action_node=node,
                    active_process=active_process,
                    user=user,
                )
                actors_done.add(node.actor)
                print(f'  Demo task: {node.actor} → {node.name}', flush=True)
    print('Demo active processes seeded.', flush=True)
except Exception as e:
    print(f'Warning: could not seed demo active processes: {e}', flush=True)

# ── Summary ───────────────────────────────────────────────────────────────────
print(flush=True)
print('=== Seed complete ===', flush=True)
for model_name in order:
    try:
        Model = django_apps.get_model('shared_models', model_name)
        print(f'{model_name}: {Model.objects.count()}', flush=True)
    except Exception:
        pass
print(f'Users: {User.objects.count()}', flush=True)
