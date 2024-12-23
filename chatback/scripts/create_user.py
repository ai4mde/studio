#!/usr/bin/env python3

import sys
import os
import getpass

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings

def prompt_input(prompt: str, secret: bool = False) -> str:
    try:
        if secret:
            value = getpass.getpass(prompt)
        else:
            value = input(prompt)
        return value.strip()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)

def create_user():
    # Connect to database
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Get user input
        username = prompt_input("Enter username: ")
        email = prompt_input("Enter email: ")
        password = prompt_input("Enter password: ", secret=True)
        password_confirm = prompt_input("Confirm password: ", secret=True)

        # Validate input
        if not username or not email or not password:
            print("Error: All fields are required")
            sys.exit(1)

        if password != password_confirm:
            print("Error: Passwords do not match")
            sys.exit(1)

        # Check if user already exists
        if db.query(User).filter(User.email == email).first():
            print("Error: User with this email already exists")
            sys.exit(1)

        if db.query(User).filter(User.username == username).first():
            print("Error: Username already taken")
            sys.exit(1)

        # Create user
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            is_active=True
        )

        db.add(user)
        db.commit()
        print(f"\nUser {username} created successfully!")

    except Exception as e:
        print(f"Error creating user: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    create_user() 