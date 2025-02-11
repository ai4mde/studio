#!/usr/bin/env python3
import asyncio
import random
import sys
import os
from pathlib import Path
import json
import argparse

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

# Test PlantUML diagrams
CLASS_DIAGRAM = '''@startuml
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
@enduml'''

USE_CASE_DIAGRAM = '''@startuml
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
@enduml'''

ACTIVITY_DIAGRAM = '''@startuml
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
@enduml'''

async def test_diagram_creation(username: str, password: str):
    """Test the creation of UML diagrams using the ACC API."""
    try:
        # Generate random numbers for project and system names
        project_num = random.randint(1000, 9999)
        system_num = random.randint(1000, 9999)
        
        # Initialize the UML converter agent
        agent = UMLConverterAgent(session_id=f"test_{project_num}")
        
        print(colored("\n=== Starting UML Diagram Creation Test ===", "cyan"))
        print(colored(f"Project Number: {project_num}", "yellow"))
        print(colored(f"System Number: {system_num}", "yellow"))

        # Create class diagram
        print(colored("\n1. Creating Class Diagram...", "cyan"))
        class_result = await agent.create_class_diagram_flow(
            username=username,
            password=password,
            system_name=f"testSystem_{system_num}",
            system_description="Test system for UML diagrams",
            plantuml_code=CLASS_DIAGRAM
        )
        print(colored("✓ Class diagram created successfully", "green"))
        print(colored(f"Project ID: {class_result['project_id']}", "yellow"))
        print(colored(f"System ID: {class_result['system_id']}", "yellow"))
        print(colored(f"Diagram ID: {class_result['diagram']['id']}", "yellow"))

        # Create use case diagram
        print(colored("\n2. Creating Use Case Diagram...", "cyan"))
        usecase_result = await agent.create_use_case_diagram_flow(
            username=username,
            password=password,
            system_name=f"testSystem_{system_num}",
            system_description="Test system for UML diagrams",
            plantuml_code=USE_CASE_DIAGRAM
        )
        print(colored("✓ Use case diagram created successfully", "green"))
        print(colored(f"Diagram ID: {usecase_result['diagram']['id']}", "yellow"))

        # Create activity diagram
        print(colored("\n3. Creating Activity Diagram...", "cyan"))
        activity_result = await agent.create_activity_diagram_flow(
            username=username,
            password=password,
            system_name=f"testSystem_{system_num}",
            system_description="Test system for UML diagrams",
            plantuml_code=ACTIVITY_DIAGRAM
        )
        print(colored("✓ Activity diagram created successfully", "green"))
        print(colored(f"Diagram ID: {activity_result['diagram']['id']}", "yellow"))

        print(colored("\n=== Test Completed Successfully ===", "green"))
        
        # Print summary of created diagrams
        print(colored("\nCreated Diagrams Summary:", "cyan"))
        print(colored(f"1. Class Diagram ID: {class_result['diagram']['id']}", "yellow"))
        print(colored(f"2. Use Case Diagram ID: {usecase_result['diagram']['id']}", "yellow"))
        print(colored(f"3. Activity Diagram ID: {activity_result['diagram']['id']}", "yellow"))

    except Exception as e:
        print(colored(f"\n❌ Error: {str(e)}", "red"))
        raise

def main():
    parser = argparse.ArgumentParser(description="Test UML diagram creation with ACC API")
    parser.add_argument("username", help="Username for ACC API authentication")
    parser.add_argument("password", help="Password for ACC API authentication")
    args = parser.parse_args()

    asyncio.run(test_diagram_creation(args.username, args.password))

if __name__ == "__main__":
    main() 