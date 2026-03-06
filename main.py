"""
AI-Powered Document Analysis Agent
Main entry point for the application.
"""

import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Run the FastAPI server."""
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()

