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

async def test_activity_diagram(agent, project_id, system_id):
    """Test creating an activity diagram with nodes and edges."""
    try:
        print("\n=== Testing Activity Diagram Creation ===")
        
        # Create activity diagram
        print("1. Creating activity diagram...")
        diagram = await agent.create_diagram(
            system_id=system_id,
            plantuml_code="",  # Empty for now
            diagram_type="activity"
        )
        diagram_id = diagram["id"]
        print(f"✅ Created activity diagram with ID: {diagram_id}")
        
        # Create nodes
        print("\n2. Creating nodes...")
        
        # Create start node
        start = await agent.add_node(
            diagram_id=diagram_id,
            name="start",
            node_type="initial",
            description="Start of activity"
        )
        print(f"✅ Created start node with ID: {start['id']}")
        
        # Create login activity
        login = await agent.add_node(
            diagram_id=diagram_id,
            name="Login",
            node_type="action",
            description="User login activity"
        )
        print(f"✅ Created login activity with ID: {login['id']}")
        
        # Create decision node
        decision = await agent.add_node(
            diagram_id=diagram_id,
            name="Check Login",
            node_type="decision",
            description="Check login credentials"
        )
        print(f"✅ Created decision node with ID: {decision['id']}")
        
        # Create dashboard activity
        dashboard = await agent.add_node(
            diagram_id=diagram_id,
            name="Dashboard",
            node_type="action",
            description="User dashboard"
        )
        print(f"✅ Created dashboard activity with ID: {dashboard['id']}")
        
        # Create fork node
        fork = await agent.add_node(
            diagram_id=diagram_id,
            name="fork",
            node_type="fork",
            description="Fork to parallel activities"
        )
        print(f"✅ Created fork node with ID: {fork['id']}")
        
        # Create view orders activity
        view_orders = await agent.add_node(
            diagram_id=diagram_id,
            name="View Orders",
            node_type="action",
            description="View user orders"
        )
        print(f"✅ Created view orders activity with ID: {view_orders['id']}")
        
        # Create manage profile activity
        manage_profile = await agent.add_node(
            diagram_id=diagram_id,
            name="Manage Profile",
            node_type="action",
            description="Manage user profile"
        )
        print(f"✅ Created manage profile activity with ID: {manage_profile['id']}")
        
        # Create join node
        join = await agent.add_node(
            diagram_id=diagram_id,
            name="join",
            node_type="join",
            description="Join parallel activities"
        )
        print(f"✅ Created join node with ID: {join['id']}")
        
        # Create logout activity
        logout = await agent.add_node(
            diagram_id=diagram_id,
            name="Logout",
            node_type="action",
            description="User logout"
        )
        print(f"✅ Created logout activity with ID: {logout['id']}")
        
        # Create error activity
        error = await agent.add_node(
            diagram_id=diagram_id,
            name="Error",
            node_type="action",
            description="Login error"
        )
        print(f"✅ Created error activity with ID: {error['id']}")
        
        # Create end node
        end = await agent.add_node(
            diagram_id=diagram_id,
            name="end",
            node_type="final",
            description="End of activity"
        )
        print(f"✅ Created end node with ID: {end['id']}")
        
        # Create edges
        print("\n3. Creating edges...")
        
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
            print(f"✅ Created edge: {description}")
        
        print("\n✅ Activity diagram creation completed successfully!")
        return diagram_id
        
    except Exception as e:
        print(f"\n❌ Error in activity diagram creation: {str(e)}")
        traceback.print_exc()
        raise

async def test_class_diagram(agent, project_id, system_id):
    """Test creating a class diagram with classes and relationships."""
    try:
        print("\n=== Testing Class Diagram Creation ===")
        
        # Create class diagram
        print("1. Creating class diagram...")
        diagram = await agent.create_diagram(
            system_id=system_id,
            plantuml_code="",
            diagram_type="classes"
        )
        diagram_id = diagram["id"]
        print(f"✅ Created class diagram with ID: {diagram_id}")
        
        # Create nodes (classes)
        print("\n2. Creating classes...")
        
        # Create User class
        user = await agent.add_node(
            diagram_id=diagram_id,
            name="User",
            node_type="class",
            description="User class",
            properties={
                "attributes": [
                    {
                        "name": "id",
                        "type": "str",
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    },
                    {
                        "name": "username",
                        "type": "str",
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    },
                    {
                        "name": "email",
                        "type": "str",
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    },
                    {
                        "name": "password",
                        "type": "str",
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    }
                ],
                "methods": [
                    {
                        "name": "login",
                        "description": "",
                        "type": "str",
                        "body": ""
                    },
                    {
                        "name": "logout",
                        "description": "",
                        "type": "str",
                        "body": ""
                    },
                    {
                        "name": "updateProfile",
                        "description": "",
                        "type": "str",
                        "body": ""
                    }
                ]
            }
        )
        print(f"✅ Created User class with ID: {user['id']}")
        
        # Create Order class
        order = await agent.add_node(
            diagram_id=diagram_id,
            name="Order",
            node_type="class",
            description="Order class",
            properties={
                "attributes": [
                    {
                        "name": "id",
                        "type": "str",
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    },
                    {
                        "name": "userId",
                        "type": "str",
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    },
                    {
                        "name": "date",
                        "type": "datetime",
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    },
                    {
                        "name": "status",
                        "type": "str",
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    }
                ],
                "methods": [
                    {
                        "name": "place",
                        "description": "",
                        "type": "str",
                        "body": ""
                    },
                    {
                        "name": "cancel",
                        "description": "",
                        "type": "str",
                        "body": ""
                    },
                    {
                        "name": "getStatus",
                        "description": "",
                        "type": "str",
                        "body": ""
                    }
                ]
            }
        )
        print(f"✅ Created Order class with ID: {order['id']}")
        
        # Create Product class
        product = await agent.add_node(
            diagram_id=diagram_id,
            name="Product",
            node_type="class",
            description="Product class",
            properties={
                "attributes": [
                    {
                        "name": "id",
                        "type": "str",
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    },
                    {
                        "name": "name",
                        "type": "str",
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    },
                    {
                        "name": "price",
                        "type": "int",
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    },
                    {
                        "name": "description",
                        "type": "str",
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    }
                ],
                "methods": [
                    {
                        "name": "getDetails",
                        "description": "",
                        "type": "str",
                        "body": ""
                    },
                    {
                        "name": "updateStock",
                        "description": "",
                        "type": "str",
                        "body": ""
                    }
                ]
            }
        )
        print(f"✅ Created Product class with ID: {product['id']}")
        
        # Create edges (relationships)
        print("\n3. Creating relationships...")
        
        # User -|> Order (User has many Orders)
        await agent.add_edge(
            diagram_id=diagram_id,
            source=user["id"],
            target=order["id"],
            edge_type="association",
            label="places"
        )
        print("✅ Created relationship: User -> Order")
        
        # Order -|> Product (Order has many Products)
        await agent.add_edge(
            diagram_id=diagram_id,
            source=order["id"],
            target=product["id"],
            edge_type="association",
            label="contains"
        )
        print("✅ Created relationship: Order -> Product")
        
        print("\n✅ Class diagram creation completed successfully!")
        return diagram_id
        
    except Exception as e:
        print(f"\n❌ Error in class diagram creation: {str(e)}")
        traceback.print_exc()
        raise

async def test_use_case_diagram(agent, project_id, system_id):
    """Test creating a use case diagram with actors and use cases."""
    try:
        print("\n=== Testing Use Case Diagram Creation ===")
        
        # Create use case diagram
        print("1. Creating use case diagram...")
        diagram = await agent.create_diagram(
            system_id=system_id,
            plantuml_code="",
            diagram_type="usecase"
        )
        diagram_id = diagram["id"]
        print(f"✅ Created use case diagram with ID: {diagram_id}")
        
        # Create actors
        print("\n2. Creating actors...")
        
        # Create Customer actor
        customer = await agent.add_actor(
            diagram_id=diagram_id,
            name="Customer",
            description="A registered customer"
        )
        print(f"✅ Created Customer actor with ID: {customer['data']['id']}")
        
        # Create Admin actor
        admin = await agent.add_actor(
            diagram_id=diagram_id,
            name="Admin",
            description="System administrator"
        )
        print(f"✅ Created Admin actor with ID: {admin['data']['id']}")
        
        # Create use cases
        print("\n3. Creating use cases...")
        
        # Create Login use case
        login = await agent.add_use_case(
            diagram_id=diagram_id,
            name="Login",
            description="User authentication"
        )
        print(f"✅ Created Login use case with ID: {login['data']['id']}")
        
        # Create Manage Profile use case
        manage_profile = await agent.add_use_case(
            diagram_id=diagram_id,
            name="Manage Profile",
            description="Update user profile"
        )
        print(f"✅ Created Manage Profile use case with ID: {manage_profile['data']['id']}")
        
        # Create View Orders use case
        view_orders = await agent.add_use_case(
            diagram_id=diagram_id,
            name="View Orders",
            description="View order history"
        )
        print(f"✅ Created View Orders use case with ID: {view_orders['data']['id']}")
        
        # Create Place Order use case
        place_order = await agent.add_use_case(
            diagram_id=diagram_id,
            name="Place Order",
            description="Create a new order"
        )
        print(f"✅ Created Place Order use case with ID: {place_order['data']['id']}")
        
        # Create Manage Users use case
        manage_users = await agent.add_use_case(
            diagram_id=diagram_id,
            name="Manage Users",
            description="Manage user accounts"
        )
        print(f"✅ Created Manage Users use case with ID: {manage_users['data']['id']}")
        
        # Create relationships
        print("\n4. Creating relationships...")
        
        # Customer associations
        await agent.add_actor_association(
            diagram_id=diagram_id,
            actor_id=customer['data']['id'],
            use_case_id=login['data']['id']
        )
        print("✅ Created relationship: Customer -> Login")
        
        await agent.add_actor_association(
            diagram_id=diagram_id,
            actor_id=customer['data']['id'],
            use_case_id=manage_profile['data']['id']
        )
        print("✅ Created relationship: Customer -> Manage Profile")
        
        await agent.add_actor_association(
            diagram_id=diagram_id,
            actor_id=customer['data']['id'],
            use_case_id=view_orders['data']['id']
        )
        print("✅ Created relationship: Customer -> View Orders")
        
        await agent.add_actor_association(
            diagram_id=diagram_id,
            actor_id=customer['data']['id'],
            use_case_id=place_order['data']['id']
        )
        print("✅ Created relationship: Customer -> Place Order")
        
        # Admin associations
        await agent.add_actor_association(
            diagram_id=diagram_id,
            actor_id=admin['data']['id'],
            use_case_id=login['data']['id']
        )
        print("✅ Created relationship: Admin -> Login")
        
        await agent.add_actor_association(
            diagram_id=diagram_id,
            actor_id=admin['data']['id'],
            use_case_id=manage_users['data']['id']
        )
        print("✅ Created relationship: Admin -> Manage Users")
        
        print("\n✅ Use case diagram creation completed successfully!")
        return diagram_id
        
    except Exception as e:
        print(f"\n❌ Error in use case diagram creation: {str(e)}")
        traceback.print_exc()
        raise

async def main(username: str, password: str):
    """Main function to test all diagram types."""
    try:
        # Initialize the agent
        agent = UMLConverterAgent(session_id=str(uuid.uuid4()))
        
        print("\n=== Testing ACC API Authentication ===")
        print(f"Username: {username}\n")
        
        # Step 1: Authenticate
        print("1. Attempting to authenticate...")
        access_token = await agent.authenticate(username, password)
        print("✅ Authentication successful")
        print(f"Access token received: {access_token[:20]}...\n")
        
        # Step 2: Create test project
        print("2. Creating test project...")
        project_name = f"test_project_{random.randint(1000, 9999)}"
        project_id = await agent.create_project(
            name=project_name,
            description="Test project for UML diagrams"
        )
        print("✅ Project created successfully")
        print(f"Project name: {project_name}")
        print(f"Project ID: {project_id}\n")
        
        # Step 3: Create test system
        print("3. Creating test system...")
        system_name = f"test_system_{random.randint(1000, 9999)}"
        system_id = await agent.create_system(
            project_id=project_id,
            name=system_name,
            description="Test system for UML diagrams"
        )
        print("✅ System created successfully")
        print(f"System name: {system_name}")
        print(f"System ID: {system_id}\n")
        
        # Step 4: Test each diagram type
        activity_diagram_id = await test_activity_diagram(agent, project_id, system_id)
        class_diagram_id = await test_class_diagram(agent, project_id, system_id)
        use_case_diagram_id = await test_use_case_diagram(agent, project_id, system_id)
        
        print("\n=== Test Summary ===")
        print(f"Project ID: {project_id}")
        print(f"System ID: {system_id}")
        print(f"Activity Diagram ID: {activity_diagram_id}")
        print(f"Class Diagram ID: {class_diagram_id}")
        print(f"Use Case Diagram ID: {use_case_diagram_id}")
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test ACC API with all diagram types")
    parser.add_argument("username", help="Username for authentication")
    parser.add_argument("password", help="Password for authentication")
    args = parser.parse_args()
    
    asyncio.run(main(args.username, args.password))
