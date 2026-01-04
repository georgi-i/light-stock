#!/usr/bin/env python3
"""
Database initialization script
Creates tables and default data (roles, admin user)
"""
import sys
import secrets
from getpass import getpass
from app import create_app, db
from app.models import Role, User, Category

def init_database():
    """Initialize database with tables and default data"""
    app = create_app('development')

    with app.app_context():
        print("Creating database tables...")
        db.create_all()

        # Check if roles already exist
        if Role.query.count() == 0:
            print("Creating default roles...")

            # Create roles
            admin_role = Role(name='Admin', description='Administrator with full access')
            manager_role = Role(name='Manager', description='Manager with inventory management access')
            staff_role = Role(name='Staff', description='Staff with basic access')

            db.session.add(admin_role)
            db.session.add(manager_role)
            db.session.add(staff_role)
            db.session.commit()
            print("✓ Default roles created")
        else:
            print("✓ Roles already exist")

        # Check if admin user exists
        if User.query.filter_by(username='admin').first() is None:
            print("\nCreating admin user...")
            print("Please enter admin credentials:")

            username = input("Username [admin]: ").strip() or 'admin'
            email = input("Email [admin@ims.local]: ").strip() or 'admin@ims.local'

            # Password input
            while True:
                password = getpass("Password (min 12 chars): ")
                if len(password) < 12:
                    print("Password must be at least 12 characters long!")
                    continue

                password_confirm = getpass("Confirm password: ")
                if password != password_confirm:
                    print("Passwords don't match!")
                    continue

                break

            # Create admin user
            admin_user = User(
                username=username,
                email=email,
                fs_uniquifier=secrets.token_hex(16),
                active=True
            )
            admin_user.set_password(password)

            # Assign admin role
            admin_role = Role.query.filter_by(name='Admin').first()
            if not admin_role:
                print("Error: Admin role not found! Creating it now...")
                admin_role = Role(name='Admin', description='Administrator with full access')
                db.session.add(admin_role)
                db.session.flush()  # Ensure the role is available

            admin_user.roles.append(admin_role)

            db.session.add(admin_user)
            db.session.commit()

            print(f"✓ Admin user '{username}' created successfully!")
        else:
            print("✓ Admin user already exists")

        # Create default categories
        if Category.query.count() == 0:
            print("\nCreating default categories...")

            categories = [
                Category(name_en='Electronics', name_bg='Електроника', description='Electronic devices and components'),
                Category(name_en='Tools', name_bg='Инструменти', description='Tools and equipment'),
                Category(name_en='Office Supplies', name_bg='Офис материали', description='Office and stationery supplies'),
                Category(name_en='Hardware', name_bg='Хардуер', description='Hardware and construction materials'),
                Category(name_en='Other', name_bg='Друго', description='Miscellaneous items'),
            ]

            for category in categories:
                db.session.add(category)

            db.session.commit()
            print("✓ Default categories created")
        else:
            print("✓ Categories already exist")

        print("\n" + "="*50)
        print("Database initialization complete!")
        print("="*50)
        print("\nYou can now run the application with:")
        print("  python run.py")
        print("\nOr in development mode:")
        print("  flask run")
        print("\n")


if __name__ == '__main__':
    try:
        init_database()
    except KeyboardInterrupt:
        print("\n\nInitialization cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during initialization: {str(e)}")
        sys.exit(1)
