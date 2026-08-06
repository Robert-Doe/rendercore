"""
Module 25 — the RENDERER side of the broker/target pair.

Runs as a separate OS process (launched via subprocess.Popen by
sandboxing.py). Communicates with the broker over its own stdin/stdout —
real OS pipes, not a shared-memory shortcut.

This file deliberately implements TWO different behaviors so this
module can honestly show both sides of the story:

  "cooperative_read" — the renderer follows the intended protocol: it
  NEVER opens the file itself. It asks the broker, waits for a reply,
  and only knows what the broker chooses to tell it.

  "malicious_read" — the renderer ignores the protocol entirely and
  opens the file directly, itself, exactly as a compromised or hostile
  renderer process would. See sandboxing.py's DECISIONS.md for why this
  succeeding is the most important, most honest fact this module
  demonstrates: a polite protocol is not a security boundary.
"""

import json
import sys


def send(obj) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def recv():
    line = sys.stdin.readline()
    return json.loads(line) if line else None


def main():
    while True:
        instruction = recv()
        if instruction is None or instruction.get("action") == "exit":
            break

        action = instruction["action"]
        path = instruction.get("path")

        if action == "cooperative_read":
            # Ask the broker. Do NOT touch the filesystem ourselves.
            send({"request": "read_file", "path": path})
            reply = recv()   # blocks until the broker replies
            send({"result": "cooperative_read", **reply})

        elif action == "malicious_read":
            # Ignore the protocol. Just open the file ourselves.
            try:
                with open(path, "r") as f:
                    data = f.read()
                send({"result": "malicious_read", "ok": True, "data": data})
            except OSError as e:
                send({"result": "malicious_read", "ok": False, "error": str(e)})

        else:
            send({"result": "error", "ok": False, "error": f"unknown action {action!r}"})


if __name__ == "__main__":
    main()
