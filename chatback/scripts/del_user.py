#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, project_root)

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.models import User

# Constants
SCRIPT_NAME = "Delete User Script"
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

async def list_available_users():
    """List all available users."""
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    select(User)
                    .options(selectinload(User.group))
                    .order_by(User.email)
                )
                users = result.scalars().all()

                if not users:
                    print_color("No users found.", YELLOW)
                    return

                print("\nAvailable Users:")
                print("=" * 120)
                print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Group':<20} {'Active'}")
                print("-" * 120)

                for user in users:
                    group_name = user.group.name if user.group else 'No Group'
                    active_status = "Yes" if user.is_active else "No"
                    print(
                        f"{user.id:<5} {user.username:<20} {user.email:<30} "
                        f"{group_name:<20} {active_status}"
                    )
                print("-" * 120)
                print()

    except Exception as e:
        print_color(f"Error listing users: {str(e)}", RED)
        raise

async def get_user_by_username(session, username: str):
    """Get user by username with group preloaded."""
    try:
        result = await session.execute(
            select(User)
            .options(selectinload(User.group))
            .where(User.username == username)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        print_color(f"Error looking up user: {str(e)}", RED)
        raise

async def delete_user(username: str):
    """Delete a user by username."""
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                user = await get_user_by_username(session, username)
                if not user:
                    print_color(f"No user found with username '{username}'", YELLOW)
                    return False

                # Show user details before deletion
                print("\nUser to delete:")
                print(f"ID: {user.id}")
                print(f"Username: {user.username}")
                print(f"Email: {user.email}")
                print(f"Group: {user.group.name if user.group else 'No Group'}")
                print(f"Active: {'Yes' if user.is_active else 'No'}")

                confirm = prompt_input("\nAre you sure you want to delete this user? (y/N)", required=False, default="n")
                if confirm.lower() != "y":
                    print_color("Operation cancelled.", YELLOW)
                    return False

                await session.delete(user)
                await session.commit()
                print_color(f"\nUser {user.username} successfully deleted.", GREEN)
                return True

    except Exception as e:
        print_color(f"Error deleting user: {str(e)}", RED)
        raise

async def main():
    """Main script execution flow."""
    try:
        print_color(f"\n=== {SCRIPT_NAME} v{SCRIPT_VERSION} ===\n", BLUE)
        
        await list_available_users()
        
        username = prompt_input("Enter username to delete")
        await delete_user(username)

    except Exception as e:
        print_color(f"Error in main execution: {str(e)}", RED)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_color("\nOperation cancelled by user.", YELLOW)
        sys.exit(0) 