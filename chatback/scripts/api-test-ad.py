#!/usr/bin/env python3

import asyncio
import argparse
import os
import sys
import uuid
import random
import traceback

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Try to import termcolor, use fallback if not available
try:
    from termcolor import colored
    COLORED_OUTPUT = True
except ImportError:
    print("Note: Install termcolor for colored output: pip install termcolor")
    print("Continuing with monochrome output...\n")
    # Fallback colored function
    def colored(text, *args, **kwargs):
        return text
    COLORED_OUTPUT = False

from app.services.chat.uml_converter_agent import UMLConverterAgent

# Sample activity diagram in PlantUML format
ACTIVITY_DIAGRAM = """
@startuml
start
:Login;
if (Valid Credentials?) then (yes)
  :Dashboard;
  fork
    :View Orders;
  fork again
    :Manage Profile;
  end fork
  :Logout;
else (no)
  :Show Error;
endif
stop
@enduml
"""

async def test_activity_diagram(username: str, password: str):
    """Test creating an activity diagram with nodes and edges."""
    try:
        # Initialize the agent
        agent = UMLConverterAgent(session_id=str(uuid.uuid4()))
        
        print("\n=== Testing ACC API Authentication ===")
        print(f"Username: {username}\n")
        
        # Step 1: Authenticate
        print("1. Attempting to authenticate...")
        access_token = await agent.authenticate(username, password)
        print("✓ Authentication successful")
        print(f"Access token received: {access_token[:20]}...\n")
        
        # Step 2: Create test project
        print("2. Creating test project...")
        project_name = f"test_project_{random.randint(1000, 9999)}"
        project_id = await agent.create_project(
            name=project_name,
            description="Test project for activity diagram"
        )
        print("✓ Project created successfully")
        print(f"Project name: {project_name}")
        print(f"Project ID: {project_id}\n")
        
        # Step 3: Create test system
        print("3. Creating test system...")
        system_name = f"test_system_{random.randint(1000, 9999)}"
        system_id = await agent.create_system(
            project_id=project_id,
            name=system_name,
            description="Test system for activity diagram"
        )
        print("✓ System created successfully")
        print(f"System name: {system_name}")
        print(f"System ID: {system_id}\n")
        
        # Step 4: Create activity diagram
        print("4. Creating activity diagram...")
        diagram = await agent.create_diagram(
            system_id=system_id,
            plantuml_code="",  # Empty for now
            diagram_type="activity"
        )
        diagram_id = diagram["id"]
        print(f"✅ Created activity diagram with ID: {diagram_id}")
        print(f"Project ID: {project_id}")
        print(f"System ID: {system_id}\n")
        
        # Step 4.1: Create nodes
        print("4.1 Creating nodes...")
        
        # Create start node
        start = await agent.add_node(
            diagram_id=diagram_id,
            name="start",
            node_type="initial",
            description="Start of activity"
        )
        print(f"✓ Created start node with ID: {start['id']}")
        
        # Create login activity
        login = await agent.add_node(
            diagram_id=diagram_id,
            name="Login",
            node_type="action",
            description="User login activity"
        )
        print(f"✓ Created login activity with ID: {login['id']}")
        
        # Create decision node
        decision = await agent.add_node(
            diagram_id=diagram_id,
            name="Check Login",
            node_type="decision",
            description="Check login credentials"
        )
        print(f"✓ Created decision node with ID: {decision['id']}")
        
        # Create dashboard activity
        dashboard = await agent.add_node(
            diagram_id=diagram_id,
            name="Dashboard",
            node_type="action",
            description="User dashboard"
        )
        print(f"✓ Created dashboard activity with ID: {dashboard['id']}")
        
        # Create fork node
        fork = await agent.add_node(
            diagram_id=diagram_id,
            name="fork",
            node_type="fork",
            description="Fork to parallel activities"
        )
        print(f"✓ Created fork node with ID: {fork['id']}")
        
        # Create view orders activity
        view_orders = await agent.add_node(
            diagram_id=diagram_id,
            name="View Orders",
            node_type="action",
            description="View user orders"
        )
        print(f"✓ Created view orders activity with ID: {view_orders['id']}")
        
        # Create manage profile activity
        manage_profile = await agent.add_node(
            diagram_id=diagram_id,
            name="Manage Profile",
            node_type="action",
            description="Manage user profile"
        )
        print(f"✓ Created manage profile activity with ID: {manage_profile['id']}")
        
        # Create join node
        join = await agent.add_node(
            diagram_id=diagram_id,
            name="join",
            node_type="join",
            description="Join parallel activities"
        )
        print(f"✓ Created join node with ID: {join['id']}")
        
        # Create logout activity
        logout = await agent.add_node(
            diagram_id=diagram_id,
            name="Logout",
            node_type="action",
            description="User logout"
        )
        print(f"✓ Created logout activity with ID: {logout['id']}")
        
        # Create error activity
        error = await agent.add_node(
            diagram_id=diagram_id,
            name="Error",
            node_type="action",
            description="Login error"
        )
        print(f"✓ Created error activity with ID: {error['id']}")
        
        # Create end node
        end = await agent.add_node(
            diagram_id=diagram_id,
            name="end",
            node_type="final",
            description="End of activity"
        )
        print(f"✓ Created end node with ID: {end['id']}\n")
        
        # Step 4.2: Create edges
        print("4.2 Creating edges...")
        
        # Create edges with control flow
        edges = [
            (start['id'], login['id'], "Start -> Login"),
            (login['id'], decision['id'], "Login -> Decision"),
            (decision['id'], dashboard['id'], "Decision -> Dashboard (yes)"),
            (decision['id'], error['id'], "Decision -> Error (no)"),
            (dashboard['id'], fork['id'], "Dashboard -> Fork"),
            (fork['id'], view_orders['id'], "Fork -> View Orders"),
            (fork['id'], manage_profile['id'], "Fork -> Manage Profile"),
            (view_orders['id'], join['id'], "View Orders -> Join"),
            (manage_profile['id'], join['id'], "Manage Profile -> Join"),
            (join['id'], logout['id'], "Join -> Logout"),
            (logout['id'], end['id'], "Logout -> End"),
            (error['id'], end['id'], "Error -> End")
        ]
        
        for source_id, target_id, description in edges:
            edge = await agent.add_edge(
                diagram_id=diagram_id,
                source=source_id,
                target=target_id,
                edge_type="controlflow",  # Use controlflow for activity diagram edges
                label=description
            )
            print(f"✓ Created edge: {description}")
        
        print("\n✅ Activity diagram creation completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="Test ACC API with activity diagram")
    parser.add_argument("username", help="Username for authentication")
    parser.add_argument("password", help="Password for authentication")
    args = parser.parse_args()
    
    asyncio.run(test_activity_diagram(args.username, args.password))

# Run the script
if __name__ == "__main__":
    main() 