"""Entry point for multi-mode deployment of the Incident Response OpenEnv server."""

import sys
import os

# Allow imports from project root (src package)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.server import app  # noqa: F401  re-exported for uvicorn


def main(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the Incident Response OpenEnv server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
