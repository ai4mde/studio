#!/usr/bin/env python3
import asyncio
import sys
import os
from pathlib import Path
import argparse
import traceback
import re
import httpx
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get STUDIO_API_URL from environment variables with a default fallback
STUDIO_API_URL = os.getenv('STUDIO_API_URL', 'https://acc-api.ai4mde.org/api/v1')

if not STUDIO_API_URL:
    print(colored("❌ Error: STUDIO_API_URL not found in environment variables", "red"))
    sys.exit(1)

# Try to import termcolor, use fallback if not available
try:
    from termcolor import colored
    HAS_TERMCOLOR = True
except ImportError:
    print("Note: Install termcolor for colored output: pip install termcolor")
    print("Continuing with monochrome output...\n")
    HAS_TERMCOLOR = False
    def colored(text, color=None, *args, **kwargs):
        return text

def parse_plantuml(content):
    """Parse PlantUML content to extract classes and relationships."""
    print(colored("\n6. Parsing PlantUML content...", "cyan"))
    classes = []
    relationships = []
    
    # Extract class definitions
    class_pattern = r'class\s+(\w+)\s*{([^}]*)}'
    for match in re.finditer(class_pattern, content):
        class_name = match.group(1)
        class_body = match.group(2)
        print(colored(f"Found class: {class_name}", "yellow"))
        
        attributes = []
        methods = []
        
        # Parse class body
        for line in class_body.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Parse visibility
            visibility = "private"
            if line.startswith('+'):
                visibility = "public"
                line = line[1:].strip()
            elif line.startswith('-'):
                visibility = "private"
                line = line[1:].strip()
            elif line.startswith('#'):
                visibility = "protected"
                line = line[1:].strip()
                
            # Method with parameters
            if '(' in line:
                method_parts = line.split('(')
                method_name = method_parts[0].strip()
                params_part = method_parts[1].split(')')[0].strip()
                return_type = "void"  # Default return type
                
                # Check for return type after the closing parenthesis
                if ')' in line and ':' in line.split(')')[-1]:
                    return_type = line.split(')')[-1].split(':')[-1].strip()
                
                # Parse parameters
                parameters = []
                if params_part:
                    param_list = params_part.split(',')
                    for param in param_list:
                        param = param.strip()
                        if ':' in param:
                            param_name, param_type = param.split(':')
                            parameters.append({
                                "name": param_name.strip(),
                                "type": param_type.strip()
                            })
                
                print(colored(f"  Found method: {method_name}({params_part}) -> {return_type}", "yellow"))
                methods.append({
                    "name": method_name,
                    "type": return_type,
                    "visibility": visibility,
                    "parameters": parameters,
                    "description": "",
                    "body": ""
                })
            # Attribute
            else:
                attr_parts = line.split(':')
                if len(attr_parts) == 2:
                    attr_name = attr_parts[0].strip()
                    attr_type = attr_parts[1].strip()
                    print(colored(f"  Found attribute: {attr_name}: {attr_type} [{visibility}]", "yellow"))
                    
                    # Map PlantUML types to API types
                    type_mapping = {
                        'string': 'str',
                        'String': 'str',
                        'integer': 'int',
                        'Integer': 'int',
                        'int': 'int',
                        'boolean': 'bool',
                        'Boolean': 'bool',
                        'date': 'str',
                        'Date': 'str',
                        'float': 'str',
                        'Float': 'str'
                    }
                    api_type = type_mapping.get(attr_type, 'str')
                    
                    attributes.append({
                        "name": attr_name,
                        "type": api_type,
                        "visibility": visibility,
                        "derived": False,
                        "description": "",
                        "body": None
                    })
        
        classes.append({
            "name": class_name,
            "attributes": attributes,
            "methods": methods
        })
    
    # Extract relationships - Updated pattern to match PlantUML class relationships
    # Look for lines that contain relationship symbols but aren't inside class definitions
    rel_pattern = r'(?:^|\n)\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:"[^"]*")?\s*([<|*o]?-+[>|*o]?)\s*(?:"[^"]*")?\s*([A-Za-z_][A-Za-z0-9_]*)'
    
    # Get content outside of class definitions
    class_blocks = re.finditer(r'class\s+\w+\s*{[^}]*}', content, re.MULTILINE)
    class_positions = [(m.start(), m.end()) for m in class_blocks]
    
    # Find relationships in the remaining content
    for match in re.finditer(rel_pattern, content, re.MULTILINE):
        # Check if this match is inside a class definition
        pos = match.start()
        if not any(start <= pos <= end for start, end in class_positions):
            source = match.group(1)
            rel_type = match.group(2)
            target = match.group(3)
            
            # Map relationship symbols to types
            type_mapping = {
                '--': 'association',
                '<--': 'inheritance',
                '<|--': 'inheritance',
                '--|>': 'inheritance',
                '--*': 'composition',
                '*--': 'composition',
                '--o': 'aggregation',
                'o--': 'aggregation',
                '-->': 'dependency',
                '<.--': 'dependency',
                '-->.': 'dependency'
            }
            
            # Normalize the relationship type
            rel_type = rel_type.strip()
            relationship_type = type_mapping.get(rel_type, 'association')
            
            print(colored(f"Found relationship: {source} {rel_type} {target} ({relationship_type})", "yellow"))
            
            # Only add if both source and target are actual classes
            if source in [cls["name"] for cls in classes] and target in [cls["name"] for cls in classes]:
                relationships.append({
                    "source": source,
                    "target": target,
                    "type": relationship_type
                })
            else:
                print(colored(f"Skipping relationship {source} -> {target} as one or both classes not found", "yellow"))
    
    print(colored(f"Found {len(classes)} classes and {len(relationships)} relationships", "yellow"))
    return classes, relationships

async def authenticate(username: str, password: str) -> str:
    """Authenticate with STUDIO API."""
    print(colored("\n1. Attempting to authenticate...", "cyan"))
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STUDIO_API_URL}/auth/token",
            headers={
                "accept": "*/*",
                "Content-Type": "application/json"
            },
            json={
                "username": username,
                "password": password
            }
        )
        response.raise_for_status()
        token = response.json()["token"]
        print(colored("✓ Authentication successful", "green"))
        print(colored(f"Access token received: {token[:20]}...", "yellow"))
        return token

async def verify_project(token: str, project_id: str) -> dict:
    """Verify project exists."""
    print(colored("\n2. Verifying project...", "cyan"))
    try:
        # Create client with redirect following enabled
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Note the trailing slash in the URL
            response = await client.get(
                f"{STUDIO_API_URL}/metadata/projects/",  # Added trailing slash
                headers={
                    "accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )
            response.raise_for_status()
            projects = response.json()
            
            # Check if project ID exists in the list
            project = next((p for p in projects if p.get('id') == project_id), None)
            
            if not project:
                print(colored("❌ Error: Project not found", "red"))
                print(colored(f"Available projects:", "yellow"))
                for p in projects:
                    print(colored(f"  - ID: {p.get('id')} | Name: {p.get('name')}", "yellow"))
                return None
            
            print(colored("✓ Project found", "green"))
            print(colored(f"Project name: {project.get('name', 'N/A')}", "yellow"))
            return project
            
    except httpx.HTTPStatusError as e:
        print(colored(f"❌ HTTP Error: {str(e)}", "red"))
        print(colored("Please verify your project ID and try again", "yellow"))
        return None
    except Exception as e:
        print(colored(f"❌ Unexpected error: {str(e)}", "red"))
        traceback.print_exc()
        return None

async def verify_system(token: str, project_id: str, system_id: str) -> dict:
    """Verify system exists in project."""
    print(colored("\n3. Verifying system...", "cyan"))
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                f"{STUDIO_API_URL}/metadata/systems/",  # Note the trailing slash
                headers={
                    "accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )
            response.raise_for_status()
            systems = response.json()
            system = next((s for s in systems if s.get('project') == project_id and s.get('id') == system_id), None)
            
            if not system:
                print(colored("❌ System not found", "red"))
                print(colored(f"Available systems for project {project_id}:", "yellow"))
                project_systems = [s for s in systems if s.get('project') == project_id]
                for s in project_systems:
                    print(colored(f"  - ID: {s.get('id')} | Name: {s.get('name')}", "yellow"))
                return None
                
            print(colored("✓ System found", "green"))
            print(colored(f"System name: {system.get('name', 'N/A')}", "yellow"))
            return system
            
    except httpx.HTTPStatusError as e:
        print(colored(f"❌ HTTP Error: {str(e)}", "red"))
        print(colored("Please verify your system ID and try again", "yellow"))
        return None
    except Exception as e:
        print(colored(f"❌ Unexpected error: {str(e)}", "red"))
        traceback.print_exc()
        return None

async def create_class_diagram(token: str, system_id: str) -> str:
    """Create a new class diagram."""
    print(colored("\n4. Creating class diagram...", "cyan"))
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STUDIO_API_URL}/diagram/",
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            json={
                "system": system_id,
                "type": "classes",
                "name": f"test_class_{uuid.uuid4().hex[:8]}"
            }
        )
        response.raise_for_status()
        diagram = response.json()
        diagram_id = diagram["id"]
        print(colored("✓ Class diagram created", "green"))
        print(colored(f"Diagram ID: {diagram_id}", "yellow"))
        return diagram_id

async def create_class_nodes(token: str, diagram_id: str, classes: list) -> dict:
    """Create nodes for each class in the diagram."""
    print(colored("\n7. Creating class nodes...", "cyan"))
    class_ids = {}
    async with httpx.AsyncClient() as client:
        for cls in classes:
            try:
                # Format attributes with proper structure
                formatted_attributes = []
                for attr in cls["attributes"]:
                    # Map float to str since float is not supported
                    if attr["type"] == "float":
                        attr_type = "str"
                    else:
                        attr_type = attr["type"]
                    
                    formatted_attr = {
                        "name": attr["name"],
                        "type": attr_type,
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    }
                    formatted_attributes.append(formatted_attr)
                    print(colored(f"  Adding attribute: {attr['name']}: {attr_type}", "yellow"))

                # Format methods with proper structure
                formatted_methods = []
                for method in cls["methods"]:
                    # All methods return str by default if no specific return type
                    method_type = "str"
                    if method["type"] not in ["str", "int", "bool", "datetime", "enum"]:
                        method_type = "str"
                    
                    formatted_method = {
                        "name": method["name"],
                        "description": "",
                        "type": method_type,
                        "body": ""
                    }
                    formatted_methods.append(formatted_method)
                    print(colored(f"  Adding method: {method['name']} -> {method_type}", "yellow"))

                # Create node with proper structure
                node_data = {
                    "cls": {
                        "namespace": "",
                        "name": cls["name"],
                        "type": "class",
                        "attributes": formatted_attributes,
                        "methods": formatted_methods
                    }
                }

                response = await client.post(
                    f"{STUDIO_API_URL}/diagram/{diagram_id}/node/",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {token}"
                    },
                    json=node_data
                )
                response.raise_for_status()
                node = response.json()
                node_id = node["id"]
                class_ids[cls["name"]] = node_id
                print(colored(f"✓ Created class: {cls['name']} (Id: {node_id})", "green"))
            except Exception as e:
                print(colored(f"❌ Error creating class {cls['name']}: {str(e)}", "red"))
                continue
    return class_ids

async def create_relationships(token: str, diagram_id: str, relationships: list, class_ids: dict):
    """Create relationships between classes."""
    print(colored("\n8. Creating relationships...", "cyan"))
    print(colored(f"Available class IDs: {class_ids}", "yellow"))
    
    async with httpx.AsyncClient() as client:
        for rel in relationships:
            try:
                source_id = class_ids.get(rel["source"])
                target_id = class_ids.get(rel["target"])
                
                print(colored(f"Processing relationship: {rel['source']} -> {rel['target']} ({rel['type']})", "yellow"))
                print(colored(f"Source ID: {source_id}", "yellow"))
                print(colored(f"Target ID: {target_id}", "yellow"))
                
                if source_id and target_id:
                    edge_data = {
                        "source": source_id,
                        "target": target_id,
                        "rel": {
                            "type": rel["type"],
                            "label": "",
                            "derived": False,
                            "multiplicity": None,
                            "labels": None
                        }
                    }
                    print(colored(f"Sending edge data: {edge_data}", "yellow"))
                    
                    response = await client.post(
                        f"{STUDIO_API_URL}/diagram/{diagram_id}/edge/",
                        headers={
                            "accept": "application/json",
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {token}"
                        },
                        json=edge_data
                    )
                    
                    if response.status_code != 200:
                        print(colored(f"Response status: {response.status_code}", "yellow"))
                        print(colored(f"Response body: {response.text}", "yellow"))
                        
                    response.raise_for_status()
                    print(colored(f"✓ Created {rel['type']} relationship: {rel['source']} -> {rel['target']}", "green"))
                else:
                    print(colored(f"❌ Error: Could not find IDs for {rel['source']} -> {rel['target']}", "red"))
            except Exception as e:
                print(colored(f"❌ Error creating relationship: {str(e)}", "red"))
                print(colored(f"Full error details: {traceback.format_exc()}", "red"))
                continue

async def read_plantuml_file(plantuml_file: str) -> str:
    """Read and validate PlantUML file."""
    print(colored("\n5. Reading PlantUML file...", "cyan"))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, plantuml_file)
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_content = f.read()
        print(colored("✓ PlantUML file read successfully", "green"))
        return plantuml_content
    except FileNotFoundError:
        print(colored(f"❌ Error: File {plantuml_file} not found in {script_dir}", "red"))
        return None

async def create_class_diagram_from_plantuml(username: str, password: str, project_id: str, system_id: str, plantuml_file: str):
    """Create a class diagram from PlantUML using STUDIO API."""
    try:
        # Step 1: Authentication
        token = await authenticate(username, password)
        if not token:
            return
            
        # Step 2: Verify Project
        project = await verify_project(token, project_id)
        if not project:
            print(colored("\nTip: Use the project IDs listed above or create a new project first.", "yellow"))
            print(colored("You can create a new project using:", "yellow"))
            print(colored("  python scripts/add_project.py -u <username> -w <password> -p <project_name> -s <system_name>", "yellow"))
            return
            
        # Step 3: Verify System
        system = await verify_system(token, project_id, system_id)
        if not system:
            return
            
        # Step 4: Create Class Diagram
        diagram_id = await create_class_diagram(token, system_id)
        if not diagram_id:
            return
            
        # Step 5: Read PlantUML file
        plantuml_content = await read_plantuml_file(plantuml_file)
        if not plantuml_content:
            return
            
        # Step 6: Parse PlantUML content
        classes, relationships = parse_plantuml(plantuml_content)
        
        # Step 7: Create class nodes
        class_ids = await create_class_nodes(token, diagram_id, classes)
        if not class_ids:
            return
            
        # Step 8: Create relationships
        await create_relationships(token, diagram_id, relationships, class_ids)
        
        # Print summary
        print(colored("\n=== Summary ===", "green"))
        print(colored(f"Created class diagram with ID: {diagram_id}", "yellow"))
        print(colored(f"Added {len(class_ids)} classes", "yellow"))
        print(colored(f"Added {len(relationships)} relationships", "yellow"))
        
    except Exception as e:
        print(colored(f"\n❌ Error: {str(e)}", "red"))
        traceback.print_exc()
        print(colored("\nTroubleshooting tips:", "yellow"))
        print(colored("1. Verify your credentials", "yellow"))
        print(colored("2. Check if the project ID exists using the list above", "yellow"))
        print(colored("3. Ensure the STUDIO_API_URL is correct in your environment", "yellow"))
        print(colored(f"Current API URL: {STUDIO_API_URL}", "yellow"))
        raise

def main():
    parser = argparse.ArgumentParser(description="Create a class diagram from PlantUML using STUDIO API")
    parser.add_argument("-u", "--user", required=True, help="Username for STUDIO API authentication")
    parser.add_argument("-w", "--password", required=True, help="Password for STUDIO API authentication")
    parser.add_argument("-p", "--project", required=True, help="Project ID")
    parser.add_argument("-s", "--system", required=True, help="System ID")
    parser.add_argument("-i", "--input", required=True, help="Input PlantUML file")
    args = parser.parse_args()

    asyncio.run(create_class_diagram_from_plantuml(args.user, args.password, args.project, args.system, args.input))

if __name__ == "__main__":
    main() 