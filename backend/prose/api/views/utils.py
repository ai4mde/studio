
import re
import csv
from io import StringIO
from uuid import uuid4

def parse_relations(csv_table, classifiers):
    relations = []
    reader = csv.DictReader(StringIO(csv_table))
    for row in reader:
        try:
            source_name = row['source_class_name']
            target_name = row['target_class_name']
            source_mult = row['source_multiplicity']
            target_mult = row['target_multiplicity']
            rel = {}
            rel['id'] = uuid4().hex
            print(rel)
            for cls in classifiers:
                if cls['data']['name'] == source_name:
                    rel['source'] = cls['id']
                if cls['data']['name'] == target_name:
                    rel['target'] = cls['id']
            rel['data'] = {"type": "association", "multiplicity": {"source": source_mult, "target": target_mult}, "derived": False, "label": " "}
            relations.append(rel)
            print(rel)
        except:
            pass
    return relations


def parse_classifiers(csv_table):
    classifiers = []
    reader = csv.DictReader(StringIO(csv_table))
    
    for row in reader:
        try:
            attributes = []
            attr_str = row['attributes'].strip('[]')
            if attr_str:
                for attr in attr_str.split(','):
                    type_name, attr_name = attr.strip().split(':')
                    attributes.append({
                        "name": attr_name.strip(),
                        "type": type_name.strip(),
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    })
            data = {
                'name': row['class_name'],
                'type': 'class',
                "attributes": attributes,
            }
            cls = {
                'id': uuid4().hex,
                'data': data,
            }
            classifiers.append(cls)
        except:
            pass
    return classifiers



def parse_llm_response(response: str):
    tables = re.findall(r'START\n(.*?)\nEND', response, re.DOTALL)
    if len(tables) != 2:
        return
    classifiers_csv_table = tables[0]
    relations_csv_table = tables[1]
    classifiers = parse_classifiers(classifiers_csv_table)
    relations = parse_relations(relations_csv_table, classifiers)
    output = {
        "classifiers": classifiers,
        "relations": relations
    }
    return output