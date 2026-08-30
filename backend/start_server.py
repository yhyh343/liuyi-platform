import os
import sys
os.environ["DATABASE_URL"] = "sqlite://liuyy_dev.db"
sys.path.insert(0, os.getcwd())
from app import app
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8000)