#!/usr/bin/env python3

import sys
import os
from typing import List

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.config import settings

def format_user_row(user: User) -> str:
    """Format a single user row for display"""
    return f"{user.id:<5} | {user.username:<20} | {user.email:<30} | {'Active' if user.is_active else 'Inactive'}"

def list_users() -> None:
    # Connect to database
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Get all users
        users: List[User] = db.query(User).order_by(User.id).all()

        if not users:
            print("\nNo users found in the database.")
            return

        # Print header
        print("\nUser List:")
        print("-" * 70)
        print(f"{'ID':<5} | {'Username':<20} | {'Email':<30} | {'Status'}")
        print("-" * 70)

        # Print each user
        for user in users:
            print(format_user_row(user))

        print("-" * 70)
        print(f"Total users: {len(users)}")

    except Exception as e:
        print(f"Error listing users: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    list_users() 