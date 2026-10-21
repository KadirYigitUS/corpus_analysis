"""CLI entrypoint to launch Corpus Analysis SPA server."""

from __future__ import annotations

import argparse
import atexit
import os
import signal
import socket
import sys
from pathlib import Path

# Ensure scripts/corpus_analysis is in python path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from SPA.app import create_app  # noqa: E402
from stop_spa import PID_FILE, find_pids_by_port, get_cmd_for_pid, stop_process  # noqa: E402


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is currently open and bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def cleanup_pid_file() -> None:
    """Remove PID file on shutdown if it belongs to current process."""
    try:
        if PID_FILE.exists():
            content = PID_FILE.read_text().strip()
            if content == str(os.getpid()):
                PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def register_signal_handlers() -> None:
    """Register cleanup handlers for graceful termination."""
    atexit.register(cleanup_pid_file)

    def handle_signal(sig, frame):
        cleanup_pid_file()
        sys.exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, handle_signal)
        except (ValueError, OSError):
            pass


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
        "--restart",
        "-r",
        action="store_true",
        help="Automatically stop any existing process on target port before starting",
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help="Optional custom corpus data root directory",
    )
    args = parser.parse_args()

    # Port conflict detection
    if is_port_in_use(args.port, host=args.host):
        pids = find_pids_by_port(args.port)
        if args.restart:
            print(f"🔄 Restart requested: terminating process(es) on port {args.port}: {pids}")
            for p in pids:
                stop_process(p, force=True)
        else:
            print(f"❌ Error: Port {args.port} is already in use by process(es):")
            for p in pids:
                print(f"   - PID {p}: {get_cmd_for_pid(p)}")
            print("\n💡 Suggestions:")
            print(f"   - Run: python stop_spa.py --port {args.port}")
            print(f"   - Or run: python run_spa.py --port {args.port} --restart")
            sys.exit(1)

    # Save PID file
    try:
        PID_FILE.write_text(str(os.getpid()))
    except Exception:
        pass
    register_signal_handlers()

    app = create_app(data_root=args.data_root)
    print(f"🚀 Corpus Analysis SPA starting at http://{args.host}:{args.port}")
    print("ℹ️ Press Ctrl+C to stop the server (or run 'python stop_spa.py')\n")
    try:
        app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
    finally:
        cleanup_pid_file()


if __name__ == "__main__":
    main()
