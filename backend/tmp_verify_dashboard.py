import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.db.session import SessionLocal
from app.services.dashboard_service import build_dashboard

db = SessionLocal()
try:
    dashboard = build_dashboard(db, -1)
    print("Dashboard Data:")
    print(dashboard)
except Exception as e:
    print("Error:", e)
finally:
    db.close()
