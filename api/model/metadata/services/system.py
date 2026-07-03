from typing import Optional
from django.db import transaction

from diagram.models.diagram import Diagram
from metadata.models import Classifier, Relation, Project, Interface, System


@transaction.atomic
def import_project_from_json(data):
    # Expects the data to be validated using the ImportProject schema
    # So all required fields should be present and valid
    project, _ = Project.upsert_from_json(data)

    system_ids = []
    for system_data in data["systems"]:
        import_system_from_json(system_data)
        system_ids.append(system_data["id"])

    Project.delete_missing(project.systems, system_ids)

    return project

@transaction.atomic
def import_systems_from_json(project, data: list[dict]):
    for system_data in data:
        imported_system_data = system_data.copy()
        imported_system_data["project"] = project.id  # Associate the imported system with the current project
        import_system_from_json(
            imported_system_data,
            project=project,
            # Associate the imported classifiers with the current project. This shouldn't be necessary as the classifier should not have a project field (should be inferred from the system)
        )
    # After importing all systems, check if there are any classifiers that can be moved back to their original system
    Classifier.move_to_original_system(project)

@transaction.atomic
def import_system_from_json(data, project: Optional[Project] = None):
    system = System.import_from_json(data)

    classifier_ids = []
    for classifier_data in data['classifiers']:
        classifier_data_copy = classifier_data.copy() # To avoid mutating the original data which might cause unintended side effects
        if project:
            classifier_data_copy['project'] = project.id
        Classifier.import_from_json(classifier_data_copy)
        classifier_ids.append(classifier_data_copy['id'])

    for classifier_data in data.get('imported_classifiers', []):
        # For now just add the classifier to the current system and add the original_system_id
        # This is because the system it belongs to might not be importe yet
        # Or it might be imported after this system is imported
        # After all systems are imported we can move all classifiers back to the original system if it exists
        imported_classifier_data = classifier_data.copy() # To avoid mutating the original data which might cause unintended side effects
        if project:
            imported_classifier_data['project'] = project.id
        imported_classifier_data['original_system_id'] = (
                classifier_data.get('original_system_id') or imported_classifier_data.get('system')
        )
        imported_classifier_data['system'] = system.id
        Classifier.import_from_json(imported_classifier_data)
        classifier_ids.append(imported_classifier_data['id'])
    System.delete_missing(system.classifiers, classifier_ids)

    relation_ids = []
    for relation_data in data['relations']:
        Relation.import_from_json(relation_data)
        relation_ids.append(relation_data['id'])
    System.delete_missing(system.relations, relation_ids)

    diagram_ids = []
    for diagram_data in data['diagrams']:
        Diagram.import_from_json(diagram_data)
        diagram_ids.append(diagram_data['id'])
    System.delete_missing(system.diagrams, diagram_ids)

    interface_ids = []
    for interface_data in data['interfaces']:
        Interface.import_from_json(interface_data)
        interface_ids.append(interface_data['id'])
    System.delete_missing(system.interfaces, interface_ids)

    return system
