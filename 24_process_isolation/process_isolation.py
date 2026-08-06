"""
Module 24 — Multi-Process Tab Isolation
===========================================
Proves: each tab runs as a REAL, separate OS process (verified by real,
distinct process IDs) — and when one tab's process crashes with an
unhandled error, the other tabs' processes, and the main "chrome"
process, are provably still alive and still responsive afterward.

Uses `multiprocessing`, not `threading` — see
prereqs/processes_and_threads.html for why that specific choice is what
makes real crash isolation possible at all.
"""

import multiprocessing as mp
import os


def tab_worker(tab_id: str, cmd_queue: mp.Queue, result_queue: mp.Queue, should_crash: bool) -> None:
    """Runs in its own OS process. Reports its OWN real pid — not the
    parent's — so the parent can verify these are genuinely separate
    processes, not just separate function calls."""
    result_queue.put((tab_id, "started", os.getpid()))
    while True:
        cmd = cmd_queue.get()
        if cmd == "stop":
            break
        if cmd == "ping":
            if should_crash:
                result_queue.put((tab_id, "crashing", os.getpid()))
                raise RuntimeError(f"simulated renderer crash in tab {tab_id!r}")
            result_queue.put((tab_id, "pong", os.getpid()))


if __name__ == "__main__":
    main_pid = os.getpid()
    result_queue = mp.Queue()
    tabs = {}

    print("=" * 70)
    print("Starting 3 tabs, each as a REAL separate OS process")
    print("=" * 70)
    for tab_id, should_crash in [("tab_a", False), ("tab_b", True), ("tab_c", False)]:
        cmd_queue = mp.Queue()
        proc = mp.Process(target=tab_worker, args=(tab_id, cmd_queue, result_queue, should_crash), daemon=True)
        proc.start()
        tabs[tab_id] = {"process": proc, "cmd_queue": cmd_queue}

    started_pids = {}
    for _ in range(3):
        tab_id, status, pid = result_queue.get(timeout=10)
        started_pids[tab_id] = pid

    print(f"  main (chrome) process pid: {main_pid}")
    for tab_id, pid in started_pids.items():
        print(f"  {tab_id} process pid: {pid}")
    all_pids = [main_pid] + list(started_pids.values())
    print(f"\nall 4 pids are genuinely distinct: {len(set(all_pids)) == 4}")

    print()
    print("=" * 70)
    print("Pinging all 3 tabs — tab_b is configured to crash instead of responding")
    print("=" * 70)
    for tab_id, info in tabs.items():
        info["cmd_queue"].put("ping")

    first_round = {}
    for _ in range(3):
        tab_id, status, pid = result_queue.get(timeout=10)
        first_round[tab_id] = status
    print(f"  responses: {first_round}")

    tabs["tab_b"]["process"].join(timeout=10)   # wait for the crash to actually finish

    print()
    print("=" * 70)
    print("AFTER the crash")
    print("=" * 70)
    print(f"  tab_b exit code (non-zero == it really crashed): {tabs['tab_b']['process'].exitcode}")
    print(f"  tab_a still alive: {tabs['tab_a']['process'].is_alive()}")
    print(f"  tab_c still alive: {tabs['tab_c']['process'].is_alive()}")
    print(f"  main (chrome) process pid, unchanged, still executing this "
          f"very line: {os.getpid() == main_pid}")

    print()
    print("=" * 70)
    print("Proving tab_a and tab_c are not just 'alive' but genuinely still")
    print("RESPONSIVE — pinging them again, AFTER tab_b's crash")
    print("=" * 70)
    tabs["tab_a"]["cmd_queue"].put("ping")
    tabs["tab_c"]["cmd_queue"].put("ping")
    second_round = {}
    for _ in range(2):
        tab_id, status, pid = result_queue.get(timeout=10)
        second_round[tab_id] = (status, pid)
    print(f"  post-crash responses: {second_round}")

    tabs["tab_a"]["cmd_queue"].put("stop")
    tabs["tab_c"]["cmd_queue"].put("stop")
    tabs["tab_a"]["process"].join(timeout=10)
    tabs["tab_c"]["process"].join(timeout=10)

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"all 4 processes (main + 3 tabs) had genuinely distinct pids: "
          f"{len(set(all_pids)) == 4}")
    print(f"tab_b actually crashed (non-zero exit code): "
          f"{tabs['tab_b']['process'].exitcode not in (0, None)}")
    print(f"tab_a and tab_c survived tab_b's crash and later exited CLEANLY "
          f"(exitcode 0, not a crash): "
          f"tab_a={tabs['tab_a']['process'].exitcode}, tab_c={tabs['tab_c']['process'].exitcode}  "
          f"-> {tabs['tab_a']['process'].exitcode == 0 and tabs['tab_c']['process'].exitcode == 0}")
    print(f"tab_a responded 'pong' to a SECOND ping issued AFTER tab_b crashed: "
          f"{second_round.get('tab_a', (None,))[0] == 'pong'}")
    print(f"tab_c responded 'pong' to a SECOND ping issued AFTER tab_b crashed: "
          f"{second_round.get('tab_c', (None,))[0] == 'pong'}")
    print(f"the pid tab_a responded with post-crash MATCHES its original pid "
          f"(same process, not silently respawned): "
          f"{second_round.get('tab_a', (None, None))[1] == started_pids['tab_a']}")
