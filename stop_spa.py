"""CLI entrypoint to stop running Corpus Analysis SPA servers."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PID_FILE = CURRENT_DIR / ".spa.pid"


def find_pids_by_port(port: int) -> list[int]:
    """Find process IDs listening on the specified TCP port."""
    pids: set[int] = set()

    # 1. Try lsof
    try:
        out = subprocess.check_output(
            ["lsof", "-t", f"-i:{port}"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        for line in out.strip().splitlines():
            pid_str = line.strip()
            if pid_str.isdigit():
                pids.add(int(pid_str))
    except Exception:
        pass

    # 2. Try fuser if lsof returned nothing
    if not pids:
        try:
            out = subprocess.check_output(
                ["fuser", f"{port}/tcp"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            for part in out.strip().split():
                if part.isdigit():
                    pids.add(int(part))
        except Exception:
            pass

    return sorted(pids)


def find_pids_by_cmd(pattern: str = "run_spa.py") -> list[int]:
    """Find process IDs running a script matching pattern."""
    pids: set[int] = set()
    my_pid = os.getpid()
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid,cmd"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        for line in out.strip().splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and parts[0].isdigit():
                pid = int(parts[0])
                cmd = parts[1]
                if pattern in cmd and pid != my_pid and "stop_spa.py" not in cmd:
                    pids.add(pid)
    except Exception:
        pass
    return sorted(pids)


def get_cmd_for_pid(pid: int) -> str:
    """Retrieve command line for a PID."""
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().replace(b"\x00", b" ").decode(errors="replace").strip()
    except Exception:
        return "unknown"


def stop_process(pid: int, force: bool = False, timeout: float = 3.0) -> bool:
    """Stop a process by PID, escalating to SIGKILL if necessary."""
    cmd = get_cmd_for_pid(pid)
    print(f"🛑 Terminating PID {pid} [{cmd[:60]}]...")

    try:
        # First send SIGCONT in case the process is stopped/suspended (STAT T/Tl)
        try:
            os.kill(pid, signal.SIGCONT)
        except OSError:
            pass

        if force:
            os.kill(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGTERM)

        # Wait for termination
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                os.kill(pid, 0)
                time.sleep(0.1)
            except OSError:
                print(f"✓ Process {pid} terminated successfully.")
                return True

        # Escalate to SIGKILL if still running
        print(f"⚠️ PID {pid} did not terminate after {timeout}s; sending SIGKILL...")
        os.kill(pid, signal.SIGKILL)
        time.sleep(0.2)
        return True
    except ProcessLookupError:
        print(f"✓ PID {pid} is no longer running.")
        return True
    except PermissionError:
        print(f"❌ Permission denied when terminating PID {pid}.")
        return False
    except Exception as exc:
        print(f"❌ Error terminating PID {pid}: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stop running Corpus Analysis SPA server(s)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Target port to check and free (default: 5000)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force kill with SIGKILL immediately",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check status without stopping processes",
    )
    args = parser.parse_args()

    # Collect candidate PIDs
    candidates: set[int] = set()

    # From PID file
    if PID_FILE.exists():
        try:
            file_pid = int(PID_FILE.read_text().strip())
            candidates.add(file_pid)
        except Exception:
            pass

    # From target port
    port_pids = find_pids_by_port(args.port)
    candidates.update(port_pids)

    # From process name
    cmd_pids = find_pids_by_cmd("run_spa.py")
    candidates.update(cmd_pids)

    # Filter live PIDs
    live_pids: list[int] = []
    for pid in sorted(candidates):
        try:
            os.kill(pid, 0)
            live_pids.append(pid)
        except OSError:
            pass

    if args.status:
        if not live_pids:
            print(f"ℹ️ No running Corpus Analysis SPA processes found on port {args.port}.")
        else:
            print(f"🔍 Found {len(live_pids)} active process(es):")
            for pid in live_pids:
                print(f"  - PID {pid}: {get_cmd_for_pid(pid)}")
        return

    if not live_pids:
        print(f"ℹ️ No running Corpus Analysis SPA or processes on port {args.port} found.")
        if PID_FILE.exists():
            PID_FILE.unlink(missing_ok=True)
        return

    print(f"🔎 Found {len(live_pids)} process(es) to terminate: {live_pids}")
    success = True
    for pid in live_pids:
        if not stop_process(pid, force=args.force):
            success = False

    # Clean up PID file
    if PID_FILE.exists():
        PID_FILE.unlink(missing_ok=True)

    # Verify port is free
    remaining_port = find_pids_by_port(args.port)
    if remaining_port:
        print(f"⚠️ Warning: Port {args.port} is still occupied by: {remaining_port}")
        sys.exit(1)
    else:
        print(f"✨ Port {args.port} is now free.")
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
