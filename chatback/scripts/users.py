#!/usr/bin/env python3
import asyncio
import sys
import logging
from pathlib import Path
from typing import List

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, project_root)

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.models import User

# Constants
SCRIPT_NAME = "List Users Script"
SCRIPT_VERSION = "1.0"

# ANSI color codes
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ENDC = '\033[0m'

# Disable SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

def print_color(message: str, color: str = BLUE) -> None:
    """Print a colored message."""
    print(f"{color}{message}{ENDC}")

async def get_all_users() -> List[User]:
    """Get all users ordered by username with their groups."""
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                # Use selectinload to eagerly load the group relationship
                result = await session.execute(
                    select(User)
                    .options(selectinload(User.group))
                    .order_by(User.username)
                )
                return list(result.scalars().all())
    except Exception as e:
        print_color(f"Database error: {str(e)}", RED)
        raise

async def display_users(users: List[User]) -> None:
    """Display users in a formatted table."""
    try:
        if not users:
            print_color("No users found.", YELLOW)
            return

        print("\nUsers:")
        print("=" * 80)
        print(f"{'ID':<5} {'Username':<15} {'Email':<30} {'Group':<15} {'Active'}")
        print("-" * 80)

        for user in users:
            try:
                group_name = user.group.name if user.group else 'No Group'
                active_status = "Yes" if user.is_active else "No"
                print(
                    f"{user.id:<5} {user.username:<15} {user.email:<30} "
                    f"{group_name:<15} {active_status}"
                )
            except Exception as e:
                print_color(f"Error displaying user {user.id}: {str(e)}", RED)

        print("-" * 80)
    except Exception as e:
        print_color(f"Error formatting user display: {str(e)}", RED)
        raise

async def list_users() -> None:
    """List all users with their group information."""
    try:
        print_color(f"\n=== {SCRIPT_NAME} v{SCRIPT_VERSION} ===\n", BLUE)
        print_color("Fetching users from database...", BLUE)
        
        users = await get_all_users()
        await display_users(users)

    except Exception as e:
        print_color(f"Error listing users: {str(e)}", RED)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(list_users())
    except KeyboardInterrupt:
        print_color("\nOperation cancelled by user.", YELLOW)
        sys.exit(0) 