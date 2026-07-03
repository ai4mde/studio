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
You are a Django {data[django_version]} software engineer. Implement one Python method for a Django model.

=== TARGET CLASS ===
{data[classifier_summary]}

=== FULL DATA MODEL (all classes live in the same models.py file) ===
{data[model_context]}

=== RELATIONSHIPS ===
{data[relation_context]}

=== TASK ===
Implement the following method for the {data[target_class]} class:
  name: {data[method_name]}
  description: {data[method_description]}

STRICT RULES:
- Do NOT write any import statements — all models are in the same file, django.db.models is already imported as `models`
- Only use field/attribute names listed above in TARGET CLASS and DATA MODEL
- For reverse FK access use: {data[reverse_fk_pattern]}
- For atomic numeric updates use: models.F("field_name")
- Do NOT reference any model, field, or method not listed above

Output ONLY the Python method (def line + indented body). No class definitions, no imports, no explanatory comments.
"""