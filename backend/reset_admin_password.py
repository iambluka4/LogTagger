import os
import sys

# Add the parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, UserRole
from services.auth import hash_password

def reset_admin_password(new_password="admin"):
    """Reset the admin password or create admin if it doesn't exist."""
    app = create_app('development')
    
    with app.app_context():
        # Try to find admin user
        admin = User.query.filter_by(role=UserRole.ADMIN).first()
        
        if admin:
            # Reset password for existing admin
            print(f"Found admin user: {admin.username}")
            admin.password = hash_password(new_password)
            db.session.commit()
            print(f"Password reset to '{new_password}' for admin user")
        else:
            # Create new admin if none exists
            print("No admin user found, creating new admin user")
            new_admin = User(
                username="admin",
                password=hash_password(new_password),
                description="Default administrator account",
                role=UserRole.ADMIN
            )
            db.session.add(new_admin)
            db.session.commit()
            print(f"Created new admin user with password '{new_password}'")

if __name__ == "__main__":
    reset_admin_password()
    print("Admin password reset complete. You can now login with username 'admin' and password 'admin'.")
