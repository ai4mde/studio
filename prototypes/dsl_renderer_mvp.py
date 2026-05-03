import json
from jinja2 import Template

# Example DSL provided in the requirements
DSL_INPUT = {
    "page": {
        "ui": {
            "layout": {
                "type": "shell",
                "regions": {
                    "main": {
                        "items": ["section-main"]
                    }
                }
            }
        }
    },
    "sections": {
        "section-main": {
            "id": "section-main",
            "class": "Product",
            "ui": {
                "layout": {
                    "type": "split",
                    "regions": {
                        "start": {
                            "span": 7,
                            "items": ["gallery"]
                        },
                        "end": {
                            "span": 5,
                            "items": ["summary", "actions"]
                        }
                    }
                },
                "components": [
                    {
                        "id": "gallery",
                        "type": "MediaGallery",
                        "bind": { "images": "images" }
                    },
                    {
                        "id": "summary",
                        "type": "ContentSummary",
                        "bind": {
                            "title": "title",
                            "price": "price",
                            "description": "description"
                        }
                    },
                    {
                        "id": "actions",
                        "type": "ActionGroup",
                        "actions": [
                            { "label": "Add to cart", "role": "primary" },
                            { "label": "Buy now", "role": "secondary" }
                        ]
                    }
                ]
            }
        }
    },
    "data": {
        "Product": {
            "title": "iPhone 15",
            "price": 999,
            "description": "Latest Apple smartphone with powerful features and sleek design.",
            "images": [
                "https://via.placeholder.com/600",
                "https://via.placeholder.com/150",
                "https://via.placeholder.com/150",
                "https://via.placeholder.com/150"
            ]
        }
    }
}

# Template Registry
LAYOUT_TEMPLATES = {
    "shell": """
    <div class="max-w-7xl mx-auto px-4 py-8">
        {% for region_id, region in regions.items() %}
            {% for item_id in region['items'] %}
                {{ render_node(item_id) }}
            {% endfor %}
        {% endfor %}
    </div>
    """,
    "split": """
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {% for region_id, region in regions.items() %}
        <div class="lg:col-span-{{ region.span }}">
            {% for item_id in region['items'] %}
                {{ render_node(item_id) }}
            {% endfor %}
        </div>
        {% endfor %}
    </div>
    """
}

COMPONENT_TEMPLATES = {
    "MediaGallery": """
    <div class="flex flex-col gap-4">
        <div class="aspect-square bg-gray-100 rounded-lg overflow-hidden">
            <img src="{{ images[0] }}" class="w-full h-full object-cover" />
        </div>
        <div class="grid grid-cols-4 gap-4">
            {% for img in images[1:] %}
            <div class="aspect-square bg-gray-100 rounded-md overflow-hidden">
                <img src="{{ img }}" class="w-full h-full object-cover" />
            </div>
            {% endfor %}
        </div>
    </div>
    """,
    "ContentSummary": """
    <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">{{ title }}</h1>
        <p class="text-2xl font-semibold text-blue-600 mb-4">${{ price }}</p>
        <p class="text-gray-600 leading-relaxed">{{ description }}</p>
    </div>
    """,
    "ActionGroup": """
    <div class="flex flex-col gap-3">
        {% for action in actions %}
        <button class="px-6 py-3 rounded-lg font-medium transition-colors
            {% if action.role == 'primary' %}
            bg-blue-600 text-white hover:bg-blue-700
            {% else %}
            border border-gray-300 text-gray-700 hover:bg-gray-50
            {% endif %}
        ">
            {{ action.label }}
        </button>
        {% endfor %}
    </div>
    """
}

BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DSL Rendered Page</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    {{ content | safe }}
</body>
</html>
"""

class Renderer:
    def __init__(self, dsl):
        self.dsl = dsl
        self.sections = dsl.get("sections", {})
        self.data = dsl.get("data", {})
        self._current_section_data = {}
        self._current_section_components = {}

    def render_component(self, component_id):
        comp = self._current_section_components.get(component_id)
        if not comp:
            return f"<!-- Component {component_id} not found -->"
        
        # Prepare context for template
        context = {}
        # 1. Bindings
        for prop, key in comp.get("bind", {}).items():
            context[prop] = self._current_section_data.get(key)
        # 2. Static props (actions, etc)
        for key, val in comp.items():
            if key not in ["id", "type", "bind"]:
                context[key] = val
                
        template_str = COMPONENT_TEMPLATES.get(comp["type"], "")
        return Template(template_str).render(**context)

    def render_layout(self, layout, render_node_fn):
        template_str = LAYOUT_TEMPLATES.get(layout["type"], "")
        return Template(template_str).render(
            regions=layout.get("regions", {}),
            render_node=render_node_fn
        )

    def render_section(self, section_id):
        section = self.sections.get(section_id)
        if not section:
            return f"<!-- Section {section_id} not found -->"
        
        # Set context for this section
        data_class = section.get("class")
        self._current_section_data = self.data.get(data_class, {})
        self._current_section_components = {c["id"]: c for c in section.get("ui", {}).get("components", [])}
        
        return self.render_layout(section["ui"]["layout"], self.render_component)

    def render_page(self):
        page_layout = self.dsl.get("page", {}).get("ui", {}).get("layout", {})
        # Note: We pass render_section as the node renderer for the page level
        page_content = self.render_layout(page_layout, self.render_section)
        return Template(BASE_HTML).render(content=page_content)

if __name__ == "__main__":
    renderer = Renderer(DSL_INPUT)
    print(renderer.render_page())
