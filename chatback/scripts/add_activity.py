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
    """Parse PlantUML content to extract activities and transitions."""
    print(colored("\n6. Parsing PlantUML content...", "cyan"))
    activities = []
    transitions = []
    
    # First, ensure we have start and end nodes
    activities.extend([
        {"name": "start", "type": "initial", "description": "Start node"},
        {"name": "end", "type": "final", "description": "End node"}
    ])
    print(colored("Added start and end nodes", "yellow"))
    
    # Extract activity definitions with improved pattern
    activity_pattern = r'(?::([^;|]+)[;|])|(?:if\s*\(([^)]+)\))|(?:else\s*(\([^)]+\))?)|(?:endif)'
    
    for match in re.finditer(activity_pattern, content):
        # Get the activity name from whichever group matched
        activity_name = next((m for m in match.groups() if m), None)
        if activity_name:
            activity_name = activity_name.strip()
            
            # Determine node type
            node_type = "action"  # default type
            if "if" in match.group(0):
                node_type = "decision"
                # For if conditions, use the condition text as the name
                activity_name = activity_name.replace("(", "").replace(")", "")
            elif "else" in match.group(0):
                continue  # Skip else as it's part of the if-else flow
            elif "endif" in match.group(0):
                continue  # Skip endif as it's part of the if-else flow
            
            # Only add if not already present
            if not any(a["name"] == activity_name for a in activities):
                print(colored(f"Found activity: {activity_name} (Type: {node_type})", "yellow"))
                activities.append({
                    "name": activity_name,
                    "type": node_type,
                    "description": ""
                })
    
    # Extract transitions with simpler pattern
    lines = content.split('\n')
    print(colored("\nLooking for transitions...", "yellow"))
    for line in lines:
        line = line.strip()
        print(colored(f"Checking line: {line}", "yellow"))
        if '->' in line:
            # Skip lines that are part of the PlantUML structure
            if any(keyword in line.lower() for keyword in ['@startuml', '@enduml', 'skinparam']):
                print(colored(f"Skipping PlantUML structure line: {line}", "yellow"))
                continue
                
            # Split the line into source and target
            parts = line.split('->')
            if len(parts) == 2:
                source = parts[0].strip()
                target_with_label = parts[1].strip()
                
                # Handle labels/guards
                target_parts = target_with_label.split(':')
                target = target_parts[0].strip()
                label = target_parts[1].strip() if len(target_parts) > 1 else ""
                
                # Clean up names
                source = source.strip('() \t')
                target = target.strip('() \t')
                
                print(colored(f"Found potential transition: {source} -> {target} [{label}]", "yellow"))
                
                # Only add transition if both source and target exist in activities
                activity_names = [a["name"] for a in activities]
                if source in activity_names and target in activity_names:
                    transitions.append({
                        "source": source,
                        "target": target,
                        "label": label
                    })
                    print(colored(f"Added transition: {source} -> {target} [{label}]", "green"))
                else:
                    print(colored(f"Skipping invalid transition: {source} -> {target}", "red"))
                    print(colored(f"Source in activities: {source in activity_names}", "yellow"))
                    print(colored(f"Target in activities: {target in activity_names}", "yellow"))
                    print(colored(f"Available activities: {activity_names}", "yellow"))
    
    print(colored(f"Found {len(activities)} activities and {len(transitions)} transitions", "yellow"))
    return activities, transitions

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
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                f"{STUDIO_API_URL}/metadata/projects/",
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
                f"{STUDIO_API_URL}/metadata/systems/",
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

async def create_activity_diagram(token: str, system_id: str) -> str:
    """Create a new activity diagram."""
    print(colored("\n4. Creating activity diagram...", "cyan"))
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
                "type": "activity",
                "name": f"test_activity_{uuid.uuid4().hex[:8]}"
            }
        )
        response.raise_for_status()
        diagram = response.json()
        diagram_id = diagram["id"]
        print(colored("✓ Activity diagram created", "green"))
        print(colored(f"Diagram ID: {diagram_id}", "yellow"))
        return diagram_id

async def create_activities(token: str, diagram_id: str, activities: list) -> dict:
    """Create activities in the diagram."""
    print(colored("\n7. Creating activities...", "cyan"))
    activity_ids = {}
    async with httpx.AsyncClient() as client:
        for activity in activities:
            try:
                node_data = {
                    "cls": {
                        "namespace": "",
                        "name": activity["name"],
                        "type": activity["type"],
                        "role": "action" if activity["type"] == "action" else "control",
                        "description": activity["description"],
                        "operation": {
                            "name": activity["name"],
                            "description": activity["description"],
                            "type": "str",
                            "body": ""
                        }
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
                activity_ids[activity["name"]] = node_id
                print(colored(f"✓ Created activity: {activity['name']} (Type: {activity['type']}, Id: {node_id})", "green"))
            except Exception as e:
                print(colored(f"❌ Error creating activity {activity['name']}: {str(e)}", "red"))
                continue
    return activity_ids

async def create_transitions(token: str, diagram_id: str, transitions: list, activity_ids: dict) -> None:
    """Create transitions between activities."""
    print(colored("\n8. Creating transitions...", "cyan"))
    print(colored(f"Available activity IDs: {activity_ids}", "yellow"))
    
    for transition in transitions:
        source = transition.get('source')
        target = transition.get('target')
        source_id = activity_ids.get(source)
        target_id = activity_ids.get(target)
        
        print(colored(f"Processing transition: {source} -> {target}", "yellow"))
        print(colored(f"Source ID: {source_id}", "yellow"))
        print(colored(f"Target ID: {target_id}", "yellow"))
        
        if not source_id or not target_id:
            print(colored(f"❌ Error: Could not find IDs for {source} -> {target}", "red"))
            continue
            
        # Edge data exactly matching API spec
        edge_data = {
            "cls": {
                "source": source_id,
                "target": target_id,
                "type": "controlflow",
                "derived": False,
                "description": "",
                "guard": None,
                "weight": None
            }
        }
        
        print(colored(f"Sending edge data: {edge_data}", "yellow"))
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{STUDIO_API_URL}/diagram/{diagram_id}/edge",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {token}"
                    },
                    json=edge_data
                )
                response.raise_for_status()
                print(colored(f"✓ Created transition: {source} -> {target}", "green"))
                print(colored(f"Response: {response.text}", "yellow"))  # Added for debugging
        except Exception as e:
            print(colored(f"❌ Error creating transition: {str(e)}", "red"))
            print(colored(f"Request data: {edge_data}", "yellow"))
            if hasattr(e, 'response'):
                print(colored(f"Response status: {e.response.status_code}", "red"))
                print(colored(f"Response text: {e.response.text}", "red"))
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

async def create_activity_diagram_from_plantuml(username: str, password: str, project_id: str, system_id: str, plantuml_file: str):
    """Create an activity diagram from PlantUML using STUDIO API."""
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
            
        # Step 4: Create Activity Diagram
        diagram_id = await create_activity_diagram(token, system_id)
        if not diagram_id:
            return
            
        # Step 5: Read PlantUML file
        plantuml_content = await read_plantuml_file(plantuml_file)
        if not plantuml_content:
            return
            
        # Step 6: Parse PlantUML content
        activities, transitions = parse_plantuml(plantuml_content)
        
        # Step 7: Create activities
        activity_ids = await create_activities(token, diagram_id, activities)
        if not activity_ids:
            return
            
        # Step 8: Create transitions
        await create_transitions(token, diagram_id, transitions, activity_ids)
        
        # Print summary
        print(colored("\n=== Summary ===", "green"))
        print(colored(f"Created activity diagram with ID: {diagram_id}", "yellow"))
        print(colored(f"Added {len(activity_ids)} activities", "yellow"))
        print(colored(f"Added {len(transitions)} transitions", "yellow"))
        
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
    parser = argparse.ArgumentParser(description="Create an activity diagram from PlantUML using STUDIO API")
    parser.add_argument("-u", "--user", required=True, help="Username for STUDIO API authentication")
    parser.add_argument("-w", "--password", required=True, help="Password for STUDIO API authentication")
    parser.add_argument("-p", "--project", required=True, help="Project ID")
    parser.add_argument("-s", "--system", required=True, help="System ID")
    parser.add_argument("-i", "--input", required=True, help="Input PlantUML file")
    args = parser.parse_args()

    asyncio.run(create_activity_diagram_from_plantuml(args.user, args.password, args.project, args.system, args.input))

if __name__ == "__main__":
    main() 