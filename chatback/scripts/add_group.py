#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, project_root)

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.db.session import AsyncSessionLocal
from app.models import Group

# Constants
SCRIPT_NAME = "Add Group Script"
SCRIPT_VERSION = "1.0"

# ANSI color codes
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ENDC = '\033[0m'

def print_color(message: str, color: str = BLUE) -> None:
    """Print a colored message."""
    print(f"{color}{message}{ENDC}")

def prompt_input(message: str, required: bool = True, default: str = None) -> str:
    """
    Prompt for input with optional default value.
    Returns the user input or default value if provided.
    """
    try:
        if default:
            message = f"{message} [{default}]: "
        else:
            message = f"{message}: "
        
        while True:
            value = input(message).strip()
            if not value:
                if default:
                    print_color(f"Using default value: {default}", BLUE)
                    return default
                if not required:
                    return None
                print_color("This field is required.", RED)
                continue
            return value
    except Exception as e:
        print_color(f"Error in prompt_input: {str(e)}", RED)
        raise

async def create_group(name: str, description: Optional[str] = None) -> None:
    """Create a new group."""
    try:
        print_color(f"\nCreating group '{name}'...", BLUE)
        
        async with AsyncSessionLocal() as session:
            async with session.begin():
                # Create group
                group = Group(name=name, description=description)
                session.add(group)
                
                try:
                    await session.commit()
                    print_color(f"\nSuccessfully created group '{name}' with ID: {group.id}", GREEN)
                except IntegrityError:
                    print_color(f"\nError: Group with name '{name}' already exists.", RED)
                    return

    except Exception as e:
        print_color(f"Error creating group: {str(e)}", RED)
        sys.exit(1)

async def main():
    """Main script execution flow."""
    try:
        print_color(f"\n=== {SCRIPT_NAME} v{SCRIPT_VERSION} ===\n", BLUE)
        
        # Get group details
        name = prompt_input("Group name")
        description = prompt_input("Description (optional)", required=False)
        
        # Confirm the inputs
        print_color("\nPlease confirm the following:", BLUE)
        print(f"Group Name: {name}")
        print(f"Description: {description or '(none)'}")
        
        confirm = prompt_input("\nSave? (Y/n)", required=False, default="y")
        if confirm.lower() != "y":
            print_color("Operation cancelled.", YELLOW)
            return

        await create_group(name, description)

    except Exception as e:
        print_color(f"Error in main execution: {str(e)}", RED)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_color("\nOperation cancelled by user.", YELLOW)
        sys.exit(0) 