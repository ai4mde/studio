#!/usr/bin/env python3
import asyncio
import sys
import os
from pathlib import Path
import argparse
import traceback

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

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

from app.services.chat.uml_converter_agent import UMLConverterAgent

async def verify_project_system(username: str, password: str, project_id: str, system_id: str):
    """Verify if a project and system exist using ACC API."""
    try:
        # Initialize the UML converter agent
        agent = UMLConverterAgent(session_id="verify_project_system")
        
        print(colored("\n=== ACC API Authentication ===", "cyan"))
        print(colored(f"Username: {username}", "yellow"))
        
        # Step 1: Authentication
        print(colored("\n1. Attempting to authenticate...", "cyan"))
        token = await agent.authenticate(username, password)
        print(colored("✓ Authentication successful", "green"))
        print(colored(f"Access token received: {token[:20]}...", "yellow"))
        
        # Step 2: Verify Project
        print(colored("\n2. Verifying project...", "cyan"))
        projects = await agent.get_projects()
        project = next((p for p in projects if p.get('id') == project_id), None)
        if project:
            print(colored("✓ Project found", "green"))
            print(colored(f"Project name: {project.get('name', 'N/A')}", "yellow"))
            print(colored(f"Project ID: {project_id}", "yellow"))
        else:
            print(colored("❌ Project not found", "red"))
            print(colored(f"Please check if project ID {project_id} exists", "yellow"))
            return
        
        # Step 3: Verify System
        print(colored("\n3. Verifying system...", "cyan"))
        systems = await agent.get_systems(project_id)
        system = next((s for s in systems if s.get('id') == system_id), None)
        if system:
            print(colored("✓ System found", "green"))
            print(colored(f"System name: {system.get('name', 'N/A')}", "yellow"))
            print(colored(f"System ID: {system_id}", "yellow"))
        else:
            print(colored("❌ System not found", "red"))
            print(colored(f"Please check if system ID {system_id} exists in project {project_id}", "yellow"))
            return
        
        print(colored("\n=== Summary ===", "green"))
        print(colored("Both project and system exist and are accessible.", "green"))
        print(colored(f"Project: {project.get('name', 'N/A')} ({project_id})", "yellow"))
        print(colored(f"System: {system.get('name', 'N/A')} ({system_id})", "yellow"))
        
    except Exception as e:
        print(colored(f"\n❌ Error: {str(e)}", "red"))
        traceback.print_exc()
        raise

def main():
    parser = argparse.ArgumentParser(description="Verify project and system existence in ACC API")
    parser.add_argument("-u", "--user", required=True, help="Username for ACC API authentication")
    parser.add_argument("-w", "--password", required=True, help="Password for ACC API authentication")
    parser.add_argument("-p", "--project", required=True, help="Project ID to verify")
    parser.add_argument("-s", "--system", required=True, help="System ID to verify")
    args = parser.parse_args()

    asyncio.run(verify_project_system(args.user, args.password, args.project, args.system))

if __name__ == "__main__":
    main() 