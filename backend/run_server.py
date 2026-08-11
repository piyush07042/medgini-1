#!/usr/bin/env python
"""Server startup script."""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=9001,
        reload=False,
        log_level="info",
    )
