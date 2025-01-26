#!/usr/bin/env python3
import asyncio
import random
import sys
import os
from pathlib import Path
import json
import argparse
import traceback
import uuid

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

# Keep the PlantUML diagrams but comment out the ones we're not using yet
CLASS_DIAGRAM = """@startuml
class User {
  + userId: int
  + name: String
  + email: String
  + password: String
  + register()
  + login()
}

class Product {
  + productId: int
  + name: String
  + description: String
  + price: float
  + stock: int
  + displayDetails()
}

class Cart {
  + cartId: int
  + userId: int
  + addItem(product: Product, quantity: int)
  + removeItem(product: Product)
  + calculateTotal(): float
}

class Order {
  + orderId: int
  + userId: int
  + orderDate: Date
  + totalAmount: float
  + placeOrder()
}

class Payment {
  + paymentId: int
  + orderId: int
  + paymentDate: Date
  + amount: float
  + processPayment()
}

User "1" -- "0..*" Cart
Cart "1" -- "0..*" Product
User "1" -- "0..*" Order
Order "1" -- "1" Payment
@enduml"""

USE_CASE_DIAGRAM = """@startuml
left to right direction

actor Customer
actor Admin

rectangle "E-commerce System" {
  usecase "Register" as UC1
  usecase "Login" as UC2
  usecase "Browse Products" as UC3
  usecase "Add to Cart" as UC4
  usecase "Checkout" as UC5
  usecase "Manage Products" as UC6
  usecase "View Orders" as UC7
}

Customer --> UC1
Customer --> UC2
Customer --> UC3
Customer --> UC4
Customer --> UC5
Customer --> UC7

Admin --> UC2
Admin --> UC6
Admin --> UC7
@enduml"""

'''
ACTIVITY_DIAGRAM = """@startuml
start
:Customer browses products;
:Customer adds items to cart;

if (Cart empty?) then (yes)
  :Display empty cart message;
  stop
else (no)
  :Proceed to checkout;
  if (User logged in?) then (yes)
    :Show shipping details;
  else (no)
    :Prompt for login;
    :User logs in;
  endif
  :Enter shipping details;
  :Select payment method;
  :Process payment;
  if (Payment successful?) then (yes)
    :Create order;
    :Send confirmation email;
    :Empty cart;
  else (no)
    :Show payment error;
    :Return to payment;
  endif
endif
stop
@enduml"""
'''

async def test_authentication_and_project(username: str, password: str):
    """Test authentication and project creation with ACC API."""
    try:
        # Initialize the UML converter agent
        agent = UMLConverterAgent(session_id="test_auth")
        
        print(colored("\n=== Testing ACC API Authentication ===", "cyan"))
        print(colored(f"Username: {username}", "yellow"))
        
        # Step 1: Authentication
        print(colored("\n1. Attempting to authenticate...", "cyan"))
        token = await agent.authenticate(username, password)
        print(colored("✓ Authentication successful", "green"))
        print(colored(f"Access token received: {token[:20]}...", "yellow"))
        
        # Step 2: Create Project
        print(colored("\n2. Creating test project...", "cyan"))
        project_num = random.randint(1000, 9999)
        project_name = f"test_project_{project_num}"
        project_description = f"Test project created by test_studio.py ({project_num})"
        
        project_id = await agent.create_project(
            name=project_name,
            description=project_description
        )
        print(colored("✓ Project created successfully", "green"))
        print(colored(f"Project name: {project_name}", "yellow"))
        print(colored(f"Project ID: {project_id}", "yellow"))
        
        # Step 3: Create System
        print(colored("\n3. Creating test system...", "cyan"))
        system_num = random.randint(1000, 9999)
        system_name = f"test_system_{system_num}"
        system_description = f"Test system created by test_studio.py ({system_num})"
        
        system_id = await agent.create_system(
            project_id=project_id,
            name=system_name,
            description=system_description
        )
        print(colored("✓ System created successfully", "green"))
        print(colored(f"System name: {system_name}", "yellow"))
        print(colored(f"System ID: {system_id}", "yellow"))
        
        # Step 4: Create class diagram
        print("\n4. Creating class diagram...")
        try:
            # Generate random 4-digit number for class name
            class_num = random.randint(1000, 9999)
            class_name = f"testClass_{class_num}"
            
            # Create the class diagram
            diagram = await agent.create_diagram(
                system_id=system_id,
                plantuml_code="",  # Empty for now
                diagram_type="classes"
            )
            
            # Extract and store the diagram ID
            diagram_id = diagram["id"]
            print(f"✅ Created class diagram '{class_name}' with ID: {diagram_id}")
            print(f"Project ID: {diagram['project']}")
            print(f"System ID: {diagram['system']}")
            
            # Create nodes for each class in the PlantUML diagram
            print("\n4.1 Creating nodes for classes...")
            
            # Extract class names from PlantUML
            class_lines = [line.strip() for line in CLASS_DIAGRAM.split('\n') if line.strip().startswith('class ')]
            class_names = [line.split(' ')[1] for line in class_lines]
            
            # Create a node for each class
            for class_name in class_names:
                # Extract attributes and methods for this class
                class_content = CLASS_DIAGRAM.split(f"class {class_name}")[1].split("}")[0]
                
                # Extract attributes
                attributes = []
                for line in class_content.split('\n'):
                    line = line.strip()
                    if line and ':' in line and not line.endswith(')'):
                        # Skip lines that look like method parameters
                        if '(' not in line:
                            parts = line.split(':')
                            name = parts[0].replace('+', '').replace('-', '').strip()
                            type_info = parts[1].strip()
                            # Normalize type to match API requirements
                            if type_info.lower() in ['string', 'str']:
                                type_info = 'str'
                            elif type_info.lower() in ['integer', 'int']:
                                type_info = 'int'
                            elif type_info.lower() in ['boolean', 'bool']:
                                type_info = 'bool'
                            elif type_info.lower() in ['date', 'datetime']:
                                type_info = 'datetime'
                            elif type_info.lower() in ['float', 'double', 'decimal']:
                                type_info = 'str'  # Use str for numeric types
                            else:
                                type_info = 'str'  # default to string for unknown types
                                
                            attributes.append({
                                "name": name,
                                "type": type_info,
                                "enum": None,
                                "derived": False,
                                "description": None,
                                "body": None
                            })
                
                # Extract methods
                methods = []
                for line in class_content.split('\n'):
                    line = line.strip()
                    if '(' in line and ')' in line:
                        # Extract method name (everything before the first parenthesis)
                        name = line.split('(')[0].replace('+', '').replace('-', '').strip()
                        
                        # Extract return type if specified after ':'
                        return_type = 'str'  # default return type
                        if ':' in line.split(')')[-1]:
                            type_part = line.split(')')[-1].split(':')[-1].strip()
                            if type_part.lower() in ['string', 'str']:
                                return_type = 'str'
                            elif type_part.lower() in ['integer', 'int']:
                                return_type = 'int'
                            elif type_part.lower() in ['boolean', 'bool']:
                                return_type = 'bool'
                            elif type_part.lower() in ['date', 'datetime']:
                                return_type = 'datetime'
                            elif type_part.lower() in ['float', 'double', 'decimal']:
                                return_type = 'str'  # Use str for numeric types
                            elif type_part.lower() == 'void':
                                return_type = 'str'  # Use str for void
                        
                        methods.append({
                            "name": name,
                            "description": "",
                            "type": return_type,
                            "body": ""
                        })
                
                # Create node with extracted data
                node = await agent.add_node(
                    diagram_id=diagram_id,
                    name=class_name,
                    node_type="class",
                    properties={
                        "attributes": attributes,
                        "methods": methods
                    }
                )
                print(f"✅ Created node for class '{class_name}' with ID: {node['id']}")
                print(f"   Attributes: {[attr['name'] for attr in attributes]}")
                print(f"   Methods: {[method['name'] for method in methods]}")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            traceback.print_exc()
            raise

        # Step 5: Create use case diagram
        print("\n5. Creating use case diagram...")
        try:
            # Create the use case diagram
            usecase_diagram = await agent.create_diagram(
                system_id=system_id,
                plantuml_code="",  # Empty for now
                diagram_type="usecase"
            )
            
            # Extract and store the diagram ID
            usecase_diagram_id = usecase_diagram["id"]
            print(f"✅ Created use case diagram with ID: {usecase_diagram_id}")
            print(f"Project ID: {usecase_diagram['project']}")
            print(f"System ID: {usecase_diagram['system']}")
            
            # Create actors
            print("\n5.1 Creating actors...")
            actor_lines = [line.strip() for line in USE_CASE_DIAGRAM.split('\n') if line.strip().startswith('actor ')]
            actor_names = [line.split(' ')[1] for line in actor_lines]
            
            actors = {}
            for actor_name in actor_names:
                actor = await agent.add_actor(
                    diagram_id=usecase_diagram_id,
                    name=actor_name,
                    description=f"Actor representing {actor_name}"
                )
                # Store the node ID from the response
                actors[actor_name] = actor["data"]["id"]
                print(f"✅ Created actor '{actor_name}' with ID: {actor['data']['id']}")
            
            # Create use cases
            print("\n5.2 Creating use cases...")
            usecase_lines = [line.strip() for line in USE_CASE_DIAGRAM.split('\n') if 'usecase' in line]
            usecases = {}
            usecase_aliases = {}  # Map between alias (UC1) and full name
            
            for line in usecase_lines:
                try:
                    # Extract use case name and alias
                    name = line.split('"')[1]  # Get text between first pair of quotes
                    # Extract alias after 'as', handling potential whitespace
                    alias = line.split(' as ')[-1].strip() if ' as ' in line else str(uuid.uuid4())
                    usecase_aliases[alias] = name
                    
                    usecase = await agent.add_use_case(
                        diagram_id=usecase_diagram_id,
                        name=name,
                        description=f"Use case for {name}"
                    )
                    # Store the node ID from the response
                    usecases[alias] = usecase["data"]["id"]
                    print(f"✅ Created use case '{name}' (alias: {alias}) with ID: {usecase['data']['id']}")
                except Exception as e:
                    print(f"⚠️ Warning: Failed to process use case line: {line}")
                    print(f"Error: {str(e)}")
                    continue
            
            # Create relationships
            print("\n5.3 Creating relationships...")
            relationship_lines = [line.strip() for line in USE_CASE_DIAGRAM.split('\n') if '-->' in line]
            
            for line in relationship_lines:
                try:
                    source, target = line.split('-->')
                    source = source.strip()
                    target = target.strip()
                    
                    # Handle actor to use case relationships
                    if source in actors:
                        if target not in usecases:
                            print(f"⚠️ Warning: Could not find use case for target {target}")
                            continue
                            
                        await agent.add_actor_association(
                            diagram_id=usecase_diagram_id,
                            actor_id=actors[source],
                            use_case_id=usecases[target],
                            description=f"Association between {source} and {usecase_aliases[target]}"
                        )
                        print(f"✅ Created association between actor '{source}' and use case '{usecase_aliases[target]}'")
                    
                    # Handle use case relationships (include/extend)
                    elif source in usecases and target in usecases:
                        await agent.add_use_case_relationship(
                            diagram_id=usecase_diagram_id,
                            source_use_case=usecases[source],
                            target_use_case=usecases[target],
                            relationship_type="include",  # Default to include, can be modified based on PlantUML syntax
                            description=f"Relationship between {usecase_aliases[source]} and {usecase_aliases[target]}"
                        )
                        print(f"✅ Created relationship between use cases '{usecase_aliases[source]}' and '{usecase_aliases[target]}'")
                    else:
                        print(f"⚠️ Warning: Could not process relationship between {source} and {target}")
                except Exception as e:
                    print(f"⚠️ Warning: Failed to process relationship line: {line}")
                    print(f"Error: {str(e)}")
                    continue
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            traceback.print_exc()
            raise
        
        print(colored("\n=== Test Completed Successfully ===", "green"))

    except Exception as e:
        print(colored(f"\n❌ Error: {str(e)}", "red"))
        raise

def main():
    parser = argparse.ArgumentParser(description="Test ACC API authentication and project creation")
    parser.add_argument("username", help="Username for ACC API authentication")
    parser.add_argument("password", help="Password for ACC API authentication")
    args = parser.parse_args()

    asyncio.run(test_authentication_and_project(args.username, args.password))

if __name__ == "__main__":
    main() 