from database import SessionLocal
from models import User

def seed_admin():
    db = SessionLocal()
    # Check if admin already exists so we don't create duplicates
    admin = db.query(User).filter(User.username == "admin_Polo").first()

    if not admin:
        new_admin = User(
            username="admin_Polo",
            password="superuser123",
            email="admin@stockanalyst.com",
            balance=999999.0,
            is_admin=True  # This user gets all the power
        )
        db.add(new_admin)
        db.commit()
        print(db.query(User).all())
    db.close()

seed_admin()

def seed_users():
    db = SessionLocal()
    for i in range(5):
        user = db.query(User).filter(User.username == f"user{i}").first()
        if not user:
            new_user = User(
                username=f"user{i}",
                password="normaluser123",
                email=f"user{i}@stockanalyst.com",
                balance = 10000+i*100,
                is_admin=False
            )
            db.add(new_user)
            db.commit()
            print(db.query(User).all())
        db.close()

seed_users()
