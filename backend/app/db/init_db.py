from app.db.session import engine
from app.models.models import Base

def init_db():
    print("Creating database tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("All database tables created successfully!")

if __name__ == "__main__":
    init_db()