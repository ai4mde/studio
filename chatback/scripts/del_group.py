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
from typing import Optional, List

from app.db.session import AsyncSessionLocal
from app.models import Group, User  # Import from models package

# ANSI color codes
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ENDC = '\033[0m'

def print_color(message: str, color: str) -> None:
    """Print a colored message."""
    print(f"{color}{message}{ENDC}")

def prompt_input(message: str, required: bool = True, default: str = None) -> str:
    """Prompt for input with optional default value."""
    if default:
        message = f"{message} [{default}]: "
    else:
        message = f"{message}: "
    
    while True:
        value = input(message).strip()
        if not value:
            if default:
                return default
            if not required:
                return None
            print_color("This field is required.", RED)
            continue
        return value

async def list_available_groups() -> None:
    """List all groups for selection."""
    async with AsyncSessionLocal() as session:
        stmt = select(Group).options(selectinload(Group.users)).order_by(Group.name)
        result = await session.execute(stmt)
        groups = result.scalars().all()

        if not groups:
            print_color("\nNo groups found.", YELLOW)
            return

        print_color("\nAvailable groups:", BLUE)
        for group in groups:
            member_count = len(group.users)
            status = "🔒 " if member_count > 0 else "  "
            print(f"{status}{group.name} ({member_count} members)")

async def delete_group(name: str) -> None:
    """Delete a group if it has no members."""
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                # Find the group
                stmt = select(Group).options(selectinload(Group.users)).where(Group.name == name)
                result = await session.execute(stmt)
                group = result.scalar_one_or_none()

                if not group:
                    print_color(f"\nError: Group '{name}' not found.", RED)
                    return

                # Check if group has members
                if group.users:
                    print_color(f"\nError: Cannot delete group '{name}' because it has {len(group.users)} members.", RED)
                    print("Remove all members first.")
                    return

                # Delete the group
                await session.delete(group)
                await session.commit()
                print_color(f"\nSuccessfully deleted group '{name}'", GREEN)

    except Exception as e:
        print_color(f"Error deleting group: {str(e)}", RED)
        sys.exit(1)

async def main():
    print_color("\n=== Delete Group ===\n", BLUE)
    
    # Show available groups
    await list_available_groups()
    
    # Get group name
    name = prompt_input("\nGroup name to delete")
    
    # Confirm deletion
    confirm = prompt_input(f"Are you sure you want to delete '{name}'? (y/N)", required=False, default="n")
    if confirm.lower() != 'y':
        print_color("Operation cancelled.", YELLOW)
        return

    await delete_group(name)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_color("\nOperation cancelled by user.", YELLOW)
        sys.exit(0) 