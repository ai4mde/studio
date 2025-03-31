import json
from django.db import migrations


def fill_workflow_engine(apps, schema_editor):
    # Get the models
    Process = apps.get_model('workflow_engine', 'Process')
    ActionNode = apps.get_model('workflow_engine', 'ActionNode')
    Rule = apps.get_model('workflow_engine', 'Rule')

    # Load the data
    with open('workflow_engine/migrations/workflow_engine_data.json', 'r') as f:
        data = json.loads(f.read())

    # Create processes
    process_map = {}
    for process_data in data['processes']:
        process = Process.objects.create(
            id=process_data['id'],
            name=process_data['name'],
            start_node=None  # Temporary placeholder
        )
        process_map[process_data['id']] = process

    # Create action nodes
    action_node_map = {}
    for action_node_data in data['action_nodes']:
        action_node = ActionNode.objects.create(
            id=action_node_data['id'],
            actor=action_node_data['actor'],
            name=action_node_data['name'],
            process=process_map[action_node_data['process']],
        )
        action_node_map[action_node_data['id']] = action_node

    # Create rules
    for rule_data in data['rules']:
        Rule.objects.create(
            id=rule_data['id'],
            condition=rule_data['condition'],
            action_node=action_node_map[rule_data['action_node']]
        )

    # Update start_node for processes
    for process_data in data['processes']:
        process = process_map[process_data['id']]
        process.start_node = action_node_map[process_data['start']]
        process.save()


def empty_workflow_engine(apps, schema_editor):
    Process = apps.get_model('workflow_engine', 'Process')
    ActionNode = apps.get_model('workflow_engine', 'ActionNode')
    Rule = apps.get_model('workflow_engine', 'Rule')

    Process.objects.all().delete()
    ActionNode.objects.all().delete()
    Rule.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_engine', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            fill_workflow_engine,
            empty_workflow_engine,
            atomic=True,
        )
    ]