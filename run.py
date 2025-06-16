"""
SheetScrape Backend Starter

This script runs the SheetScrape backend API locally.
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set default port or use environment variable
PORT = int(os.getenv("PORT", 8000))

if __name__ == "__main__":
    print(f"Starting SheetScrape API on port {PORT}...")
    print(f"API documentation will be available at http://localhost:{PORT}/docs")
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT, reload=True) 