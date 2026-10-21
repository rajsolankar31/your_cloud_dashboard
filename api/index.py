import sys
from pathlib import Path

# Add the backend app directory to sys.path so we can import the FastAPI app.
backend_app_path = Path(__file__).resolve().parent.parent / "backend" / "app"
sys.path.append(str(backend_app_path))

# Import the FastAPI app instance defined in backend/app/main.py
from main import app

# Vercel expects a callable named `handler`.
from mangum import Mangum
handler = Mangum(app)
