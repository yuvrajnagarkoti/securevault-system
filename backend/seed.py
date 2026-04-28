import os
from sqlalchemy.orm import Session
from app.utils import init_database
from app.models import User, Role, File
from app.auth import hash_password

def seed_db():
    print("Seeding database...")
    engine = init_database()
    
    with Session(engine) as db:
        # Create Roles
        admin_role = db.query(Role).filter_by(name="Admin").first()
        if not admin_role:
            admin_role = Role(name="Admin", permissions=["upload", "download", "rename", "delete", "view_logs", "manage_roles"])
            db.add(admin_role)
            
        manager_role = db.query(Role).filter_by(name="Manager").first()
        if not manager_role:
            manager_role = Role(name="Manager", permissions=["upload", "download", "rename", "delete", "view_logs"])
            db.add(manager_role)
            
        user_role = db.query(Role).filter_by(name="Standard User").first()
        if not user_role:
            user_role = Role(name="Standard User", permissions=["upload", "download"])
            db.add(user_role)
            
        db.commit()
        
        # Create Admin User if not exists
        admin = db.query(User).filter_by(username="admin_seed").first()
        if not admin:
            hashed_password = hash_password("Admin@123")
            admin = User(
                username="admin_seed",
                password_hash=hashed_password,
                role_id=admin_role.role_id
            )
            db.add(admin)
        
        # Create Manager User
        manager = db.query(User).filter_by(username="manager_seed").first()
        if not manager:
            hashed_password = hash_password("Manager@123")
            manager = User(
                username="manager_seed",
                password_hash=hashed_password,
                role_id=manager_role.role_id
            )
            db.add(manager)
            
        # Create Standard User
        user = db.query(User).filter_by(username="user_seed").first()
        if not user:
            hashed_password = hash_password("User@123")
            user = User(
                username="user_seed",
                password_hash=hashed_password,
                role_id=user_role.role_id
            )
            db.add(user)
            
        db.commit()
        print("Database seeded with default Roles and Users.")

if __name__ == "__main__":
    seed_db()
