#!/usr/bin/env python3

import asyncio
import argparse
import os
import sys

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
    """Test creating an activity diagram using the ACC API."""
    try:
        print("\n=== Testing ACC API Authentication ===")
        print(f"Username: {username}\n")

        # Initialize the UML converter agent
        agent = UMLConverterAgent()

        # 1. Authenticate
        print("1. Attempting to authenticate...")
        await agent.authenticate(username, password)
        print(colored("✓ Authentication successful", "green"))
        print(f"Access token received: {agent.access_token[:20]}...\n")

        # 2. Create a test project
        print("2. Creating test project...")
        project_name = "test_project_4201"
        project = await agent.create_project(project_name)
        print(colored("✓ Project created successfully", "green"))
        print(f"Project name: {project_name}")
        print(f"Project ID: {project['id']}\n")

        # 3. Create a test system
        print("3. Creating test system...")
        system_name = "test_system_4712"
        system = await agent.create_system(project["id"], system_name)
        print(colored("✓ System created successfully", "green"))
        print(f"System name: {system_name}")
        print(f"System ID: {system['id']}\n")

        # 4. Create activity diagram
        print("4. Creating activity diagram...")
        diagram = await agent.create_diagram(project["id"], system["id"], "activity")
        print(colored(f"✅ Created activity diagram with ID: {diagram['id']}", "green"))
        print(f"Project ID: {project['id']}")
        print(f"System ID: {system['id']}\n")

        # 4.1 Create nodes (activities, decisions, etc.)
        print("4.1 Creating nodes...")
        
        # Start node
        start = await agent.add_node(
            diagram["id"],
            "start",
            "initial",
            "Start of activity"
        )
        print(colored(f"✓ Created start node with ID: {start['id']}", "green"))

        # Login activity
        login = await agent.add_node(
            diagram["id"],
            "Login",
            "action",
            "User login activity"
        )
        print(colored(f"✓ Created login activity with ID: {login['id']}", "green"))

        # Decision node
        decision = await agent.add_node(
            diagram["id"],
            "Valid Credentials?",
            "decision",
            "Check credentials"
        )
        print(colored(f"✓ Created decision node with ID: {decision['id']}", "green"))

        # Dashboard activity
        dashboard = await agent.add_node(
            diagram["id"],
            "Dashboard",
            "action",
            "Main dashboard"
        )
        print(colored(f"✓ Created dashboard activity with ID: {dashboard['id']}", "green"))

        # Fork node
        fork = await agent.add_node(
            diagram["id"],
            "fork",
            "fork",
            "Parallel activities"
        )
        print(colored(f"✓ Created fork node with ID: {fork['id']}", "green"))

        # View Orders activity
        view_orders = await agent.add_node(
            diagram["id"],
            "View Orders",
            "action",
            "View order history"
        )
        print(colored(f"✓ Created view orders activity with ID: {view_orders['id']}", "green"))

        # Manage Profile activity
        manage_profile = await agent.add_node(
            diagram["id"],
            "Manage Profile",
            "action",
            "Update user profile"
        )
        print(colored(f"✓ Created manage profile activity with ID: {manage_profile['id']}", "green"))

        # Join node
        join = await agent.add_node(
            diagram["id"],
            "join",
            "join",
            "Join parallel flows"
        )
        print(colored(f"✓ Created join node with ID: {join['id']}", "green"))

        # Logout activity
        logout = await agent.add_node(
            diagram["id"],
            "Logout",
            "action",
            "User logout"
        )
        print(colored(f"✓ Created logout activity with ID: {logout['id']}", "green"))

        # Error activity
        error = await agent.add_node(
            diagram["id"],
            "Show Error",
            "action",
            "Display error message"
        )
        print(colored(f"✓ Created error activity with ID: {error['id']}", "green"))

        # End node
        end = await agent.add_node(
            diagram["id"],
            "end",
            "final",
            "End of activity"
        )
        print(colored(f"✓ Created end node with ID: {end['id']}", "green"))

        # 4.2 Create edges (flows)
        print("\n4.2 Creating edges...")

        # Start -> Login
        await agent.add_edge(diagram["id"], start["id"], login["id"], "control")
        print(colored("✓ Created edge: Start -> Login", "green"))

        # Login -> Decision
        await agent.add_edge(diagram["id"], login["id"], decision["id"], "control")
        print(colored("✓ Created edge: Login -> Decision", "green"))

        # Decision -> Dashboard (yes)
        await agent.add_edge(diagram["id"], decision["id"], dashboard["id"], "control", "yes")
        print(colored("✓ Created edge: Decision -> Dashboard (yes)", "green"))

        # Decision -> Error (no)
        await agent.add_edge(diagram["id"], decision["id"], error["id"], "control", "no")
        print(colored("✓ Created edge: Decision -> Error (no)", "green"))

        # Dashboard -> Fork
        await agent.add_edge(diagram["id"], dashboard["id"], fork["id"], "control")
        print(colored("✓ Created edge: Dashboard -> Fork", "green"))

        # Fork -> View Orders
        await agent.add_edge(diagram["id"], fork["id"], view_orders["id"], "control")
        print(colored("✓ Created edge: Fork -> View Orders", "green"))

        # Fork -> Manage Profile
        await agent.add_edge(diagram["id"], fork["id"], manage_profile["id"], "control")
        print(colored("✓ Created edge: Fork -> Manage Profile", "green"))

        # View Orders -> Join
        await agent.add_edge(diagram["id"], view_orders["id"], join["id"], "control")
        print(colored("✓ Created edge: View Orders -> Join", "green"))

        # Manage Profile -> Join
        await agent.add_edge(diagram["id"], manage_profile["id"], join["id"], "control")
        print(colored("✓ Created edge: Manage Profile -> Join", "green"))

        # Join -> Logout
        await agent.add_edge(diagram["id"], join["id"], logout["id"], "control")
        print(colored("✓ Created edge: Join -> Logout", "green"))

        # Logout -> End
        await agent.add_edge(diagram["id"], logout["id"], end["id"], "control")
        print(colored("✓ Created edge: Logout -> End", "green"))

        # Error -> End
        await agent.add_edge(diagram["id"], error["id"], end["id"], "control")
        print(colored("✓ Created edge: Error -> End", "green"))

        print("\n✅ Activity diagram creation completed successfully!")

    except Exception as e:
        print(colored(f"\n❌ Error: {str(e)}", "red"))
        raise

def main():
    parser = argparse.ArgumentParser(description="Test activity diagram creation with ACC API")
    parser.add_argument("username", help="Username for authentication")
    parser.add_argument("password", help="Password for authentication")
    args = parser.parse_args()

    asyncio.run(test_activity_diagram(args.username, args.password))

if __name__ == "__main__":
    main()