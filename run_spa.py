"""CLI entrypoint to launch Corpus Analysis SPA server."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Ensure scripts/corpus_analysis is in python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from SPA.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Launch Corpus Analysis Single-Page Application (SPA)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port number to listen on (default: 5000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run Flask in debug mode",
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help="Optional custom corpus data root directory",
    )
    args = parser.parse_args()

    app = create_app(data_root=args.data_root)
    print(f"🚀 Corpus Analysis SPA starting at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
