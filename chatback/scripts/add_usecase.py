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
    """Parse PlantUML content to extract actors, use cases and relationships."""
    print(colored("\n6. Parsing PlantUML content...", "cyan"))
    actors = []
    usecases = []
    relationships = []
    
    # Extract actor definitions
    actor_pattern = r'actor\s+(\w+)'
    for match in re.finditer(actor_pattern, content):
        actor_name = match.group(1)
        print(colored(f"Found actor: {actor_name}", "yellow"))
        actors.append({
            "name": actor_name,
            "description": ""
        })
    
    # Extract use case definitions
    usecase_pattern = r'usecase\s+"([^"]+)"\s+as\s+(\w+)'
    for match in re.finditer(usecase_pattern, content):
        usecase_name = match.group(1)
        usecase_id = match.group(2)
        print(colored(f"Found use case: {usecase_name} (ID: {usecase_id})", "yellow"))
        usecases.append({
            "name": usecase_name,
            "id": usecase_id,
            "description": ""
        })
    
    # Extract relationships
    rel_pattern = r'(\w+)\s*(?:"[^"]*")?\s*([-.]+)(?:>|<)?\s*(?:"[^"]*")?\s*(\w+)(?:\s*:\s*([^"\n]+))?'
    for match in re.finditer(rel_pattern, content):
        source = match.group(1)
        rel_type = match.group(2)
        target = match.group(3)
        label = match.group(4) if match.group(4) else ""
        
        # Map relationship symbols to types
        type_mapping = {
            '--': 'association',
            '.>': 'extends',
            '<.': 'extends',
            '..>': 'includes',
            '<..': 'includes'
        }
        # Normalize the relationship type
        normalized_rel_type = rel_type.strip('-.')
        rel_type = type_mapping.get(rel_type, 'association')
        
        print(colored(f"Found relationship: {source} {rel_type} {target} {label}", "yellow"))
        relationships.append({
            "source": source,
            "target": target,
            "type": rel_type,
            "label": label
        })
    
    print(colored(f"Found {len(actors)} actors, {len(usecases)} use cases, and {len(relationships)} relationships", "yellow"))
    return actors, usecases, relationships

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
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{STUDIO_API_URL}/metadata/projects/{project_id}",
            headers={
                "accept": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        response.raise_for_status()
        project = response.json()
        print(colored("✓ Project found", "green"))
        print(colored(f"Project name: {project.get('name', 'N/A')}", "yellow"))
        return project

async def verify_system(token: str, project_id: str, system_id: str) -> dict:
    """Verify system exists in project."""
    print(colored("\n3. Verifying system...", "cyan"))
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{STUDIO_API_URL}/metadata/systems/",
            headers={
                "accept": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        response.raise_for_status()
        # Filter systems by project ID after getting all systems
        systems = response.json()
        system = next((s for s in systems if s.get('project') == project_id and s.get('id') == system_id), None)
        if not system:
            print(colored("❌ System not found", "red"))
            print(colored(f"Please check if system ID {system_id} exists in project {project_id}", "yellow"))
            return None
        print(colored("✓ System found", "green"))
        print(colored(f"System name: {system.get('name', 'N/A')}", "yellow"))
        return system

async def create_usecase_diagram(token: str, system_id: str) -> str:
    """Create a new use case diagram."""
    print(colored("\n4. Creating use case diagram...", "cyan"))
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STUDIO_API_URL}/diagram/",  # Added trailing slash
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            json={
                "system": system_id,
                "type": "usecase",
                "name": f"test_usecase_{uuid.uuid4().hex[:8]}"
            }
        )
        response.raise_for_status()
        diagram = response.json()
        diagram_id = diagram["id"]
        print(colored("✓ Use case diagram created", "green"))
        print(colored(f"Diagram ID: {diagram_id}", "yellow"))
        return diagram_id

async def create_actors(token: str, diagram_id: str, actors: list) -> dict:
    """Create actors in the diagram."""
    print(colored("\n7. Creating actors...", "cyan"))
    actor_ids = {}
    async with httpx.AsyncClient() as client:
        for actor in actors:
            try:
                node_data = {
                    "cls": {
                        "namespace": "",
                        "name": actor["name"],
                        "type": "actor",
                        "description": actor["description"]
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
                actor_ids[actor["name"]] = node["id"]
                print(colored(f"✓ Created actor: {actor['name']}", "green"))
            except Exception as e:
                print(colored(f"❌ Error creating actor {actor['name']}: {str(e)}", "red"))
                continue
    return actor_ids

async def create_usecases(token: str, diagram_id: str, usecases: list) -> dict:
    """Create use cases in the diagram."""
    print(colored("\n8. Creating use cases...", "cyan"))
    usecase_ids = {}
    async with httpx.AsyncClient() as client:
        for usecase in usecases:
            try:
                node_data = {
                    "cls": {
                        "namespace": "",
                        "name": usecase["name"],
                        "type": "usecase",
                        "description": usecase["description"]
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
                usecase_ids[usecase["id"]] = node["id"]
                print(colored(f"✓ Created use case: {usecase['name']}", "green"))
            except Exception as e:
                print(colored(f"❌ Error creating use case {usecase['name']}: {str(e)}", "red"))
                continue
    return usecase_ids

async def create_relationships(token: str, diagram_id: str, relationships: list, actor_ids: dict, usecase_ids: dict):
    """Create relationships between actors and use cases."""
    print(colored("\n9. Creating relationships...", "cyan"))
    async with httpx.AsyncClient() as client:
        for rel in relationships:
            try:
                source_id = actor_ids.get(rel["source"]) or usecase_ids.get(rel["source"])
                target_id = actor_ids.get(rel["target"]) or usecase_ids.get(rel["target"])
                
                if source_id and target_id:
                    # Map relationship types to API expected types
                    type_mapping = {
                        'association': 'interaction',
                        'extends': 'extension',
                        'includes': 'inclusion'
                    }
                    edge_type = type_mapping.get(rel["type"], "interaction")
                    
                    edge_data = {
                        "source": source_id,
                        "target": target_id,
                        "rel": {
                            "type": edge_type,
                            "label": rel["label"] or ""
                        }
                    }
                    response = await client.post(
                        f"{STUDIO_API_URL}/diagram/{diagram_id}/edge/",
                        headers={
                            "accept": "application/json",
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {token}"
                        },
                        json=edge_data
                    )
                    response.raise_for_status()
                    print(colored(f"✓ Created {edge_type} relationship: {rel['source']} -> {rel['target']}", "green"))
                else:
                    print(colored(f"❌ Error: Could not find IDs for {rel['source']} -> {rel['target']}", "red"))
            except Exception as e:
                print(colored(f"❌ Error creating relationship: {str(e)}", "red"))
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

async def create_usecase_diagram_from_plantuml(username: str, password: str, project_id: str, system_id: str, plantuml_file: str):
    """Create a use case diagram from PlantUML using STUDIO API."""
    try:
        # Step 1: Authentication
        token = await authenticate(username, password)
        if not token:
            return
            
        # Step 2: Verify Project
        project = await verify_project(token, project_id)
        if not project:
            return
            
        # Step 3: Verify System
        system = await verify_system(token, project_id, system_id)
        if not system:
            return
            
        # Step 4: Create Use Case Diagram
        diagram_id = await create_usecase_diagram(token, system_id)
        if not diagram_id:
            return
            
        # Step 5: Read PlantUML file
        plantuml_content = await read_plantuml_file(plantuml_file)
        if not plantuml_content:
            return
            
        # Step 6: Parse PlantUML content
        actors, usecases, relationships = parse_plantuml(plantuml_content)
        
        # Step 7: Create actors
        actor_ids = await create_actors(token, diagram_id, actors)
        if not actor_ids:
            return
            
        # Step 8: Create use cases
        usecase_ids = await create_usecases(token, diagram_id, usecases)
        if not usecase_ids:
            return
            
        # Step 9: Create relationships
        await create_relationships(token, diagram_id, relationships, actor_ids, usecase_ids)
        
        # Print summary
        print(colored("\n=== Summary ===", "green"))
        print(colored(f"Created use case diagram with ID: {diagram_id}", "yellow"))
        print(colored(f"Added {len(actor_ids)} actors", "yellow"))
        print(colored(f"Added {len(usecase_ids)} use cases", "yellow"))
        print(colored(f"Added {len(relationships)} relationships", "yellow"))
        
    except Exception as e:
        print(colored(f"\n❌ Error: {str(e)}", "red"))
        traceback.print_exc()
        raise

def main():
    parser = argparse.ArgumentParser(description="Create a use case diagram from PlantUML using STUDIO API")
    parser.add_argument("-u", "--user", required=True, help="Username for STUDIO API authentication")
    parser.add_argument("-w", "--password", required=True, help="Password for STUDIO API authentication")
    parser.add_argument("-p", "--project", required=True, help="Project ID")
    parser.add_argument("-s", "--system", required=True, help="System ID")
    parser.add_argument("-i", "--input", required=True, help="Input PlantUML file")
    args = parser.parse_args()

    asyncio.run(create_usecase_diagram_from_plantuml(args.user, args.password, args.project, args.system, args.input))

if __name__ == "__main__":
    main() 