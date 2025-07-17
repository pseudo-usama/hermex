"""
adaptive_delay.py

Interruptible sleep controlled from the same console your program logs to.

Usage:
    import adaptive_delay as ad

    ad.start_console_listener()  # call once near program start

    # between tasks:
    ad.wait_minutes(5)           # wait up to 5 minutes unless console override

Console commands (while waiting):
    <ENTER> / now / skip    -> continue immediately
    2m                      -> wait 2 minutes total (from *now*)
    30s                     -> wait 30 seconds total (from *now*)
    0                       -> continue immediately
    1.5                     -> 1.5 minutes (default unit = minutes)
Invalid input is ignored with a log message.

Thread-safe; works cross-platform.
"""

import sys
import threading
import time
from typing import Optional

# ---------- shared state ----------
_override_lock = threading.Lock()
_override_secs: Optional[float] = None
_listener_started = False
_prompt_prefix = "[ctl]"  # change via start_console_listener(...)


# ---------- override helpers ----------
def _set_override(seconds: float):
    global _override_secs
    with _override_lock:
        _override_secs = max(0.0, seconds)
    print(f"{_prompt_prefix} override => {seconds:.1f}s", flush=True)


def _take_override() -> Optional[float]:
    global _override_secs
    with _override_lock:
        v = _override_secs
        _override_secs = None
    return v


# ---------- duration parsing ----------
def parse_duration(spec: str, default_unit: str = "m") -> float:
    """
    Parse a duration string to *seconds*.

    Accepts:
        '30s'   -> 30 sec
        '2m'    -> 120 sec
        '1.5h'  -> 5400 sec
        '1.5m'  -> 90 sec
        '90'    -> 90 *default_unit* (default minutes => 5400 sec if 'h'? no; 90m)
    """
    spec = spec.strip().lower()
    if not spec:
        raise ValueError("empty duration")

    unit = default_unit
    if spec[-1] in ("s", "m", "h"):
        unit = spec[-1]
        num = spec[:-1]
    else:
        num = spec

    val = float(num)
    mult = {"s": 1, "m": 60, "h": 3600}[unit]
    return val * mult


# ---------- console listener thread ----------
def _input_thread(default_unit: str):
    print(
        f"{_prompt_prefix} Commands: <ENTER>/now=run | <num>[s|m|h] (default {default_unit}) "
        f"| e.g. 2m, 30s, 0, 0.5m.",
        flush=True,
    )
    for line in sys.stdin:
        line = line.strip().lower()
        if line in ("", "now", "skip"):
            _set_override(0)
            continue
        try:
            secs = parse_duration(line, default_unit=default_unit)
        except Exception as e:  # noqa: BLE001
            print(f"{_prompt_prefix} ignoring {line!r}: {e}", flush=True)
        else:
            _set_override(secs)


# ---------- public startup ----------
def start_console_listener(*, default_unit: str = "m", prompt_prefix: str = "[ctl]"):
    """
    Launch the background console command reader once (safe to call multiple times).
    """
    global _listener_started, _prompt_prefix
    if _listener_started:
        return
    _prompt_prefix = prompt_prefix
    t = threading.Thread(target=_input_thread, args=(default_unit,), daemon=True)
    t.start()
    _listener_started = True


# ---------- wait functions ----------
def wait(default_seconds: float, *, poll: float = 1.0) -> float:
    """
    Wait up to `default_seconds`, but allow a runtime override from the console.
    Returns the *actual* seconds waited.

    Implementation: sleeps in small `poll` chunks; on each loop, checks for override.
    An override resets the deadline to "now + override_seconds".
    """
    start = time.time()
    deadline = start + max(0.0, default_seconds)

    while True:
        # see if console changed things
        new = _take_override()
        if new is not None:
            deadline = time.time() + new

        remaining = deadline - time.time()
        if remaining <= 0:
            break

        time.sleep(min(poll, remaining))

    return time.time() - start


def wait_minutes(default_minutes: float, *, poll: float = 1.0) -> float:
    """Convenience wrapper: wait minutes -> seconds."""
    return wait(default_minutes * 60.0, poll=poll)
