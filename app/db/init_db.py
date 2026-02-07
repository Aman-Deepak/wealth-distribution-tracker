from app.db.models import Base
from app.db.session import engine


def init_db():
    print("🔧 Creating tables in DB...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")

if __name__ == "__main__":
    init_db()

# Set a single variable
# $env:DATABASE_URL = ""
# Then run the script
# python -m app.db.init_db