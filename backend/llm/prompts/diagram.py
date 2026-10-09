DIAGRAM_GENERATE_ATTRIBUTE = """

You are a software engineer that is going to implement a derived attribute for a Django Model using Django {data[django_version]}. This generation will be based on UML Class & UML Use Case diagrams. This derived attribute will belong to a Django model that is generated using the following UML metadata:

{data[classifier_metadata]}

Your sole role is to implement a derived attribute in Django for this model.

Implement a derived attribute for this model using Django {data[django_version]} that does the following:
name: "{data[attribute_name]}"
return type: {data[attribute_return_type]}
description: "{data[attribute_description]}"

'self' must be the only function argument that is used. If other arguments are needed, they must be retrieved from other attributes of the model (for example from foreign models).

Only show the generated attribute (python function, header & body) in your response, nothing else (no class definitions, comments etc).
"""

DIAGRAM_GENERATE_METHOD = """
You are a software engineer that is going to implement a custom method for a Django Model using Django {data[django_version]}. This generation will be based on UML Class & UML Use Case diagrams. This custom method will belong to a Django model that is generated using the following UML metadata:

{data[classifier_metadata]}

These attributes are already generated in the Django model using a mapping algorithm. Your sole role is to implement a custom method in Django for this model.

Implement a custom method for this model using Django {data[django_version]} that does the following:
name: "{data[method_name]}"
description: "{data[method_description]}"

Only show the generated method (python function, header & body) in your response, nothing else (no class definitions, comments etc).
"""