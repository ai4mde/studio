import uuid

def convert_to_dict(obj, rel):
    # Helper function to generate uuid
    def generate_uuid():
        return str(uuid.uuid4())

    # Initialize dictionaries to store classifiers and relationships
    classifiers = {}
    relationships = {}

    # Iterate over the input data to process classifiers
    for key, value in obj.items():
        id = generate_uuid()
        classifiers[value["Class"]] = {
            "id": id,
            "attributes": value["Attribute"]
        }

    # Iterate over the input data to process relationships
    for relation in input_data[1]:
        uuid_relation = generate_uuid()
        relationships[uuid_relation] = {
            "type": relation[0][1],
            "from": classifiers[relation[1][1]]["class"],
            "to": classifiers[relation[3][1]]["class"],
            "multiplicity": tuple(relation[5][1])
        }

    result_dict = {
        "classifiers": classifiers,
        "relationships": relationships
    }

    return result_dict

# Example usage
input_data = [
    {
        "Box": {"Class": "Box", "Attribute": []},
        "A": {"Class": "A", "Attribute": []},
        "Customer": {"Class": "Customer", "Attribute": []},
        "Product": {"Class": "Product", "Attribute": []}
    },
    [
        [
            ["Composition", "has"],
            ["from", "Box"],
            ["to", "A"],
            ["multiplicity", ["1", "*"]]
        ],
        [
            ["Association", "orders"],
            ["from", "Customer"],
            ["to", "Product"],
            ["multiplicity", ["*", "*"]]
        ]
    ]
]

result = convert_to_dict(input_data)
print(result)
