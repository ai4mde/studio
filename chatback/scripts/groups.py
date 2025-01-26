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
from app.models import Group

# Constants
SCRIPT_NAME = "List Groups Script"
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

async def list_groups():
    """List all groups and their members."""
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    select(Group)
                    .options(selectinload(Group.users))
                    .order_by(Group.name)
                )
                groups = result.scalars().all()

                if not groups:
                    print_color("No groups found.", YELLOW)
                    return

                print("\nGroups:")
                print("=" * 80)
                print(f"{'ID':<5} {'Name':<15} {'Description':<30} {'Members':<15}")
                print("-" * 80)

                for group in groups:
                    member_count = len(group.users)
                    description = group.description or '(none)'
                    if len(description) > 27:
                        description = description[:27] + "..."
                    
                    print(
                        f"{group.id:<5} {group.name:<15} {description:<30} "
                        f"{member_count} users"
                    )
                print("-" * 80)

    except Exception as e:
        print_color(f"Error listing groups: {str(e)}", RED)
        sys.exit(1)

if __name__ == "__main__":
    try:
        print_color(f"\n=== {SCRIPT_NAME} v{SCRIPT_VERSION} ===\n", BLUE)
        asyncio.run(list_groups())
    except KeyboardInterrupt:
        print_color("\nOperation cancelled by user.", YELLOW)
        sys.exit(0) 