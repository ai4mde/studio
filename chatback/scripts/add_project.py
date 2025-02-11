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

async def create_project_system(username: str, password: str, project_name: str, system_name: str):
    """Create a new project and system using ACC API."""
    try:
        # Initialize the UML converter agent
        agent = UMLConverterAgent(session_id="create_project_system")
        
        print(colored("\n=== ACC API Authentication ===", "cyan"))
        print(colored(f"Username: {username}", "yellow"))
        
        # Step 1: Authentication
        print(colored("\n1. Attempting to authenticate...", "cyan"))
        token = await agent.authenticate(username, password)
        print(colored("✓ Authentication successful", "green"))
        print(colored(f"Access token received: {token[:20]}...", "yellow"))
        
        # Step 2: Create Project
        print(colored("\n2. Creating project...", "cyan"))
        project_description = f"Project created by create_project_system.py"
        
        project_id = await agent.create_project(
            name=project_name,
            description=project_description
        )
        print(colored("✓ Project created successfully", "green"))
        print(colored(f"Project name: {project_name}", "yellow"))
        print(colored(f"Project ID: {project_id}", "yellow"))
        
        # Step 3: Create System
        print(colored("\n3. Creating system...", "cyan"))
        system_description = f"System created by create_project_system.py"
        
        system_id = await agent.create_system(
            project_id=project_id,
            name=system_name,
            description=system_description
        )
        print(colored("✓ System created successfully", "green"))
        print(colored(f"System name: {system_name}", "yellow"))
        print(colored(f"System ID: {system_id}", "yellow"))
        
        print(colored("\n=== Summary ===", "green"))
        print(colored(f"Project Name: {project_name}", "yellow"))
        print(colored(f"Project ID: {project_id}", "yellow"))
        print(colored(f"System Name: {system_name}", "yellow"))
        print(colored(f"System ID: {system_id}", "yellow"))
        
    except Exception as e:
        print(colored(f"\n❌ Error: {str(e)}", "red"))
        traceback.print_exc()
        raise

def main():
    parser = argparse.ArgumentParser(description="Create a new project and system using ACC API")
    parser.add_argument("-u", "--user", required=True, help="Username for ACC API authentication")
    parser.add_argument("-w", "--password", required=True, help="Password for ACC API authentication")
    parser.add_argument("-p", "--project", required=True, help="Project name")
    parser.add_argument("-s", "--system", required=True, help="System name")
    args = parser.parse_args()

    asyncio.run(create_project_system(args.user, args.password, args.project, args.system))

if __name__ == "__main__":
    main() 