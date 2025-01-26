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
from app.core.security import verify_password

# ANSI color codes
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ENDC = '\033[0m'

def print_color(message: str, color: str = BLUE) -> None:
    """Print a colored message."""
    print(f"{color}{message}{ENDC}")

async def verify_credentials(username: str, password: str):
    """Verify user credentials directly."""
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                # Get user with group preloaded
                result = await session.execute(
                    select(User)
                    .options(selectinload(User.group))
                    .where(User.username == username)
                )
                user = result.scalar_one_or_none()

                if not user:
                    print_color(f"No user found with username: {username}", RED)
                    return

                print("\nUser found:")
                print(f"Username: {user.username}")
                print(f"Email: {user.email}")
                print(f"Stored password hash: {user.hashed_password}")
                print(f"Active: {'Yes' if user.is_active else 'No'}")
                print(f"Group: {user.group.name if user.group else 'No Group'}")

                # Verify password
                if verify_password(password, user.hashed_password):
                    print_color("\nPassword verification successful!", GREEN)
                else:
                    print_color("\nPassword verification failed!", RED)

    except Exception as e:
        print_color(f"Error verifying credentials: {str(e)}", RED)
        raise

async def main():
    if len(sys.argv) != 3:
        print("Usage: python verify_user.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    print_color(f"\n=== Verifying Credentials ===\n", BLUE)
    await verify_credentials(username, password)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_color("\nOperation cancelled by user.", YELLOW)
        sys.exit(0) 