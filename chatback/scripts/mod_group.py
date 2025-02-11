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
from typing import Optional, List, Set

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

def prompt_emails() -> List[str]:
    """Prompt for email addresses."""
    emails = []
    print_color("\nEnter user emails (one per line, empty line to finish):", BLUE)
    while True:
        email = input("Email (empty to finish): ").strip()
        if not email:
            break
        emails.append(email)
    return emails if emails else None

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
            print(f"  {group.name} ({len(group.users)} members)")

async def show_group_details(group: Group) -> None:
    """Show detailed information about a group."""
    print_color("\nCurrent group details:", BLUE)
    print(f"Name: {group.name}")
    print(f"Description: {group.description or '(none)'}")
    print(f"Created: {group.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Updated: {group.updated_at.strftime('%Y-%m-%d %H:%M:%S') if group.updated_at else 'never'}")
    
    if group.users:
        print("\nMembers:")
        for user in sorted(group.users, key=lambda x: x.email):
            print(f"  - {user.email}")
    else:
        print("\nMembers: (none)")

async def modify_group(name: str) -> None:
    """Modify a group's details and members."""
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

                # Show current details
                await show_group_details(group)

                # Modify basic details
                print_color("\nModify group details (press Enter to keep current value):", BLUE)
                new_name = prompt_input("New name", required=False, default=group.name)
                new_description = prompt_input("New description", required=False, default=group.description or "")

                # Update if changed
                if new_name != group.name:
                    group.name = new_name
                if new_description != (group.description or ""):
                    group.description = new_description or None

                # Member management
                while True:
                    print_color("\nMember management:", BLUE)
                    print("1. Add members")
                    print("2. Remove members")
                    print("3. Done")
                    
                    choice = prompt_input("\nChoice", default="3")
                    
                    if choice == "1":
                        # Add members
                        emails = prompt_emails()
                        if emails:
                            stmt = select(User).where(User.email.in_(emails))
                            result = await session.execute(stmt)
                            users = result.scalars().all()
                            
                            found_emails = {user.email for user in users}
                            missing_emails = set(emails) - found_emails
                            
                            if missing_emails:
                                print_color(f"Warning: Users not found: {', '.join(missing_emails)}", YELLOW)
                            
                            group.users.extend([u for u in users if u not in group.users])
                            print_color(f"Added {len(found_emails)} users to group", GREEN)
                    
                    elif choice == "2":
                        # Remove members
                        if not group.users:
                            print_color("No members to remove.", YELLOW)
                            continue
                            
                        print_color("\nCurrent members:", BLUE)
                        for i, user in enumerate(sorted(group.users, key=lambda x: x.email), 1):
                            print(f"{i}. {user.email}")
                        
                        to_remove = prompt_input("Enter numbers to remove (comma-separated, empty to cancel)", required=False)
                        if to_remove:
                            try:
                                indices = [int(i.strip()) - 1 for i in to_remove.split(",")]
                                users_to_remove = [sorted(group.users, key=lambda x: x.email)[i] for i in indices if 0 <= i < len(group.users)]
                                for user in users_to_remove:
                                    group.users.remove(user)
                                print_color(f"Removed {len(users_to_remove)} members", GREEN)
                            except (ValueError, IndexError):
                                print_color("Invalid input. Please enter valid numbers.", RED)
                    
                    else:  # Done
                        break

                await session.commit()
                print_color("\nGroup updated successfully!", GREEN)

    except IntegrityError as e:
        print_color(f"Error: Group name '{new_name}' might already exist", RED)
        print_color(f"Details: {str(e)}", RED)
        sys.exit(1)
    except Exception as e:
        print_color(f"Error modifying group: {str(e)}", RED)
        sys.exit(1)

async def main():
    print_color("\n=== Modify Group ===\n", BLUE)
    
    # Show available groups
    await list_available_groups()
    
    # Get group name
    name = prompt_input("\nGroup name to modify")
    
    await modify_group(name)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_color("\nOperation cancelled by user.", YELLOW)
        sys.exit(0) 