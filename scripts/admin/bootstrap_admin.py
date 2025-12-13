"""
Bootstrap First Admin User Script
Creates or updates a user to have admin privileges.
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select


async def bootstrap_admin(email: str, password: str = None):
    """
    Create or update user to admin.
    
    Args:
        email: Email of user to make admin
        password: New password (optional, only for new users)
    """
    # Import after adding project to path
    from app.core.config import settings
    from app.models.user_model import User
    from app.core.security import hash_password
    
    print(f"\n{'='*70}")
    print("🔧 ADMIN BOOTSTRAP SCRIPT")
    print(f"{'='*70}\n")
    
    # Create engine
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update existing user
            print(f"📧 Found existing user: {user.email}")
            print(f"   Current role: {user.role}")
            print(f"   Current superuser: {user.is_superuser}")
            print()
            
            user.role = "admin"
            user.is_superuser = True
            user.is_active = True
            
            print(f"✅ Updated user to admin:")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Role: {user.role}")
            print(f"   Superuser: {user.is_superuser}")
            print(f"   Active: {user.is_active}")
            
        else:
            # Create new admin user
            if not password:
                print(f"❌ Error: User {email} not found and no password provided")
                print(f"   To create a new admin, provide a password:")
                print(f"   python bootstrap_admin.py {email} YourSecurePassword123")
                return False
            
            # Generate username from email
            username = email.split('@')[0].lower()
            
            # Check if username exists
            result = await session.execute(
                select(User).where(User.username == username)
            )
            if result.scalar_one_or_none():
                username = f"{username}_admin"
            
            user = User(
                email=email.lower(),
                username=username,
                full_name="System Administrator",
                hashed_password=hash_password(password),
                role="admin",
                is_superuser=True,
                is_active=True,
                is_verified=True
            )
            session.add(user)
            
            print(f"✅ Created new admin user:")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Password: {password}")
            print(f"   Role: admin")
            print(f"   Superuser: True")
        
        await session.commit()
        
        print(f"\n{'='*70}")
        print("🎉 SUCCESS! Admin user is ready")
        print(f"{'='*70}\n")
        print("Next steps:")
        print("1. Start your server: python -m uvicorn app.main:app --reload")
        print("2. Login with these credentials:")
        print(f"   Email: {user.email}")
        if password:
            print(f"   Password: {password}")
        print("3. Get your access token from the response")
        print("4. Use admin endpoints to manage other users")
        print()
        
        return True


async def list_admins():
    """List all admin users."""
    from app.core.config import settings
    from app.models.user_model import User
    
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                (User.role == "admin") | (User.is_superuser == True)
            )
        )
        admins = result.scalars().all()
        
        if not admins:
            print("\n❌ No admin users found\n")
            return
        
        print(f"\n{'='*70}")
        print(f"👑 ADMIN USERS ({len(admins)})")
        print(f"{'='*70}\n")
        
        for admin in admins:
            print(f"ID: {admin.id}")
            print(f"Email: {admin.email}")
            print(f"Username: {admin.username}")
            print(f"Full Name: {admin.full_name or 'N/A'}")
            print(f"Role: {admin.role}")
            print(f"Superuser: {admin.is_superuser}")
            print(f"Active: {admin.is_active}")
            print(f"Verified: {admin.is_verified}")
            print(f"Created: {admin.created_at}")
            print("-" * 70)
        print()


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("\n" + "="*70)
        print("🔧 ADMIN BOOTSTRAP SCRIPT - Usage")
        print("="*70 + "\n")
        print("Option 1: Make existing user admin")
        print("  python bootstrap_admin.py user@example.com")
        print()
        print("Option 2: Create new admin user")
        print("  python bootstrap_admin.py newadmin@example.com SecurePass123")
        print()
        print("Option 3: List all admin users")
        print("  python bootstrap_admin.py --list")
        print()
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        asyncio.run(list_admins())
    else:
        email = sys.argv[1]
        password = sys.argv[2] if len(sys.argv) > 2 else None
        
        try:
            success = asyncio.run(bootstrap_admin(email, password))
            sys.exit(0 if success else 1)
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()

