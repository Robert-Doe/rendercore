"""
Module 17 — The Event Loop
=============================
Proves three specific guarantees, each independently verified:
  1. Tasks run in FIFO order — first posted, first run.
  2. A task posted WHILE another task is running never jumps the queue —
     it goes to the back, and only runs after every task already queued.
  3. A task always runs to COMPLETION before the next one starts — no
     other task can observe a "half-finished" mutation.

These three properties, together, are what make it safe for later
modules (19, 20) to let script mutate the DOM without the render
pipeline ever seeing an inconsistent, half-updated tree.
"""

from collections import deque


class EventLoop:
    def __init__(self):
        self.queue = deque()
        self.run_log = []   # records task labels in the order they actually ran

    def post(self, label: str, task, *args):
        """Queue a task for later execution — never runs immediately,
        no matter when post() is called."""
        self.queue.append((label, task, args))

    def run_until_empty(self, max_iterations: int = 10_000) -> int:
        """The loop itself: pop the front task, run it to completion,
        repeat. `max_iterations` exists purely as a TEST safety net for
        this module's own demo — see DECISIONS.md; a real event loop has
        no such cap and would simply hang forever on a runaway handler,
        exactly as prereqs/event_driven_programming.html describes."""
        iterations = 0
        while self.queue and iterations < max_iterations:
            label, task, args = self.queue.popleft()
            self.run_log.append(label)
            task(*args)              # <- runs to completion; nothing else runs meanwhile
            iterations += 1
        return iterations


if __name__ == "__main__":
    print("=" * 70)
    print("CASE 1 — strict FIFO order")
    print("=" * 70)
    loop1 = EventLoop()
    loop1.post("A", lambda: None)
    loop1.post("B", lambda: None)
    loop1.post("C", lambda: None)
    loop1.run_until_empty()
    print(f"run order: {loop1.run_log}")
    print(f"ran in exactly the order posted: {loop1.run_log == ['A', 'B', 'C']}")

    print()
    print("=" * 70)
    print("CASE 2 — a task posted mid-handler goes to the BACK, not the front")
    print("=" * 70)
    loop2 = EventLoop()

    def handler_b():
        # while B is running, it posts a brand-new task D
        loop2.post("D", lambda: None)

    loop2.post("A", lambda: None)
    loop2.post("B", handler_b)
    loop2.post("C", lambda: None)
    loop2.run_until_empty()
    print(f"run order: {loop2.run_log}")
    print(f"D (posted mid-run by B) ran AFTER C, not right after B: "
          f"{loop2.run_log == ['A', 'B', 'C', 'D']}")

    print()
    print("=" * 70)
    print("CASE 3 — a task always runs to completion before the next one sees its effects")
    print("=" * 70)
    loop3 = EventLoop()
    shared_state = []
    observations = []

    def handler_mutates():
        shared_state.append(1)
        shared_state.append(2)
        shared_state.append(3)   # if anything could interrupt this, a later
                                    # task might see shared_state mid-way through

    def handler_observes():
        observations.append(list(shared_state))   # snapshot at the moment it runs

    loop3.post("mutate", handler_mutates)
    loop3.post("observe", handler_observes)
    loop3.run_until_empty()
    print(f"shared_state after mutate: {shared_state}")
    print(f"what 'observe' actually saw: {observations[0]}")
    print(f"observe saw the FULLY completed mutation, never a partial one: "
          f"{observations[0] == [1, 2, 3]}")

    print()
    print("=" * 70)
    print("CASE 4 — a 'render' task between two DOM-mutating tasks only ever")
    print("sees fully-settled state, never mid-mutation (foreshadows Module 20)")
    print("=" * 70)
    loop4 = EventLoop()
    dom = {"text": "initial"}
    render_snapshots = []

    def set_text(value):
        dom["text"] = value

    def render():
        render_snapshots.append(dom["text"])

    loop4.post("set-a", set_text, "A")
    loop4.post("render-1", render)
    loop4.post("set-b", set_text, "B")
    loop4.post("render-2", render)
    loop4.run_until_empty()
    print(f"render snapshots, in order: {render_snapshots}")
    print(f"each render saw a clean, settled value — never a mix of A and B: "
          f"{render_snapshots == ['A', 'B']}")
