from app.database import SessionLocal
from app.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            admin = User(
                username="admin",
                email="admin@portal.com",
                password_hash=pwd_context.hash("admin123"),
                full_name="Administrador",
                role="admin",
                avatar_color="#6366f1",
            )
            db.add(admin)

            editor = User(
                username="editor",
                email="editor@portal.com",
                password_hash=pwd_context.hash("editor123"),
                full_name="Editor de Conteudo",
                role="editor",
                avatar_color="#ec4899",
            )
            db.add(editor)
            db.commit()
    finally:
        db.close()
