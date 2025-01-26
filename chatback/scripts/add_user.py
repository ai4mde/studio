#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, project_root)

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from app.db.session import AsyncSessionLocal
from app.models import User, Group
from app.core.security import get_password_hash

# Constants
SCRIPT_NAME = "Add User Script"
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

async def get_available_groups():
    """Get list of available groups."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Group).order_by(Group.name)
            )
            return list(result.scalars().all())
    except Exception as e:
        print_color(f"Error fetching groups: {str(e)}", RED)
        raise

async def create_user(username: str, email: str, password: str, group_name: str = None):
    """Create a new user."""
    try:
        print_color(f"\nCreating user '{username}'...", BLUE)
        
        async with AsyncSessionLocal() as session:
            # Check if username or email already exists
            result = await session.execute(
                select(User).where(
                    (User.username == username) | (User.email == email)
                )
            )
            existing_user = result.scalar_one_or_none()
            if existing_user:
                if existing_user.username == username:
                    print_color(f"\nError: Username '{username}' already exists.", RED)
                else:
                    print_color(f"\nError: Email '{email}' already exists.", RED)
                return

            # Get group if specified
            group = None
            if group_name:
                result = await session.execute(
                    select(Group).where(Group.name == group_name)
                )
                group = result.scalar_one_or_none()
                if not group:
                    print_color(f"Group '{group_name}' not found.", YELLOW)
                    return

            # Create user
            user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash(password),
                is_active=True,
                group=group
            )
            session.add(user)
            await session.commit()
            
            print_color(f"\nSuccessfully created user:", GREEN)
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Group: {user.group.name if user.group else 'No Group'}")
            print(f"Active: Yes")

    except Exception as e:
        print_color(f"Error creating user: {str(e)}", RED)
        raise

async def main():
    """Main script execution flow."""
    try:
        print_color(f"\n=== {SCRIPT_NAME} v{SCRIPT_VERSION} ===\n", BLUE)
        
        # Get user details
        username = prompt_input("Username")
        email = prompt_input("Email")
        password = prompt_input("Password")
        
        # Show available groups and prompt for group assignment
        groups = await get_available_groups()
        if groups:
            print("\nAvailable groups:")
            for group in groups:
                print(f"- {group.name}")
            
            if prompt_input("\nAssign to a group? (y/N)", required=False, default="n").lower() == "y":
                group_name = prompt_input("Group name")
            else:
                group_name = None
        else:
            print_color("\nNo groups available.", YELLOW)
            group_name = None

        # Confirm the inputs
        print_color("\nPlease confirm the following:", BLUE)
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Group: {group_name or '(none)'}")
        
        confirm = prompt_input("\nSave? (Y/n)", required=False, default="y")
        if confirm.lower() != "y":
            print_color("Operation cancelled.", YELLOW)
            return

        await create_user(username, email, password, group_name)

    except Exception as e:
        print_color(f"Error in main execution: {str(e)}", RED)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_color("\nOperation cancelled by user.", YELLOW)
        sys.exit(0) 