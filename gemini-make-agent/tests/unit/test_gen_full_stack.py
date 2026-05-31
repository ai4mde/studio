import os
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock

# Setup paths
PROJECT_ROOT = str(Path(__file__).resolve().parents[3])
GEN_SCRIPTS_PATH = os.path.join(PROJECT_ROOT, "prototypes/backend/generation/generation_scripts")
sys.path.insert(0, GEN_SCRIPTS_PATH)

from utils.definitions.application_component import ApplicationComponent
from utils.definitions.section_component import SectionComponent, SectionAttribute
from utils.definitions.page import Page
from utils.definitions.model import AttributeType
from utils.view_generation import generate_views


def test_section_component_sanitizes_navigation_page_targets():
    section = SectionComponent(
        id="sec-nav",
        name="Products",
        application="Customer",
        page="Browse_Products",
        primary_model="Product",
        parent_models=[],
        attributes=[],
        text="",
        behavior={"item_click": {"type": "navigate", "target_page": "Product Detail"}},
        workflow={"action": "navigate", "target_page": "Order Confirmation"},
    )

    assert section.item_click_target_page == "Product_Detail"
    assert section.workflow_target_page == "Order_Confirmation"


def test_view_generation_with_multi_class():
    # Mock Application Component
    app_comp = MagicMock(spec=ApplicationComponent)
    app_comp.name = "test_app"
    app_comp.project = "test_proj"
    app_comp.authentication_present = False
    
    # Mock Section with dot-notation attributes
    attr1 = SectionAttribute(name="name", type=AttributeType.STRING, derived=False, enum_literals=None, updatable=True)
    attr2 = SectionAttribute(name="seller.business_name", type=AttributeType.STRING, derived=False, enum_literals=None, updatable=True)
    
    section = SectionComponent(
        id="sec-1",
        name="ProductList",
        application="test_app",
        page="Home",
        primary_model="Product",
        parent_models=[],
        attributes=[attr1, attr2],
        has_create_operation=True,
        has_update_operation=True,
        has_delete_operation=False,
        custom_methods=[],
        text="",
        layout="card",
        style={},
        query={"limit": 5},
        col_span=12,
        position="main"
    )
    
    page = MagicMock(spec=Page)
    page.name = "Home"
    page.section_components = [section]
    page.type = "normal"
    
    app_comp.pages = [page]
    
    # Mock models_on_pages structure expected by templates
    models_on_pages = {
        page: {
            'primary_models': ["Product"],
            'parent_models': []
        }
    }
    
    # We need to monkeypatch or mock the template rendering context
    # For simplicity, we'll try to run the actual generator and check the output file
    system_id = "test-sys"
    output_dir = os.path.join(PROJECT_ROOT, f"prototypes/generated_prototypes/{system_id}/test_proj/test_app")
    os.makedirs(output_dir, exist_ok=True)
    
    # In a real run, file_generation.py would be used. 
    # Here we just want to see if our template logic works.
    from utils.file_generation import generate_output_file
    
    template_path = os.path.join(PROJECT_ROOT, "prototypes/backend/generation/templates/views.py.jinja2")
    output_path = os.path.join(output_dir, "views.py")
    
    data = {
        'application_name': "test_app",
        'pages': [page],
        'models_on_pages': models_on_pages,
        'authentication_present': False,
        'AttributeType': AttributeType
    }
    
    generate_output_file(template_path, output_path, data)
    
    print(f"Generated views.py at {output_path}")
    
    with open(output_path, "r") as f:
        content = f.read()
        
    # Assertions
    assert "_safe_select_related(qs, 'seller')" in content, "Should optimize nested fields safely"
    assert "fields = ['name']" in content, "Create/UpdateView fields should NOT include dot-notation attributes"
    assert "getattr(self.object, 'seller.business_name'" not in content, "Should NOT attempt standard getattr on nested path in UpdateView post"
    
    print("SUCCESS: Multi-class View Generation verified!")

if __name__ == "__main__":
    try:
        test_view_generation_with_multi_class()
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
