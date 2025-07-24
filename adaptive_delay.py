# adaptive_wait.py
import sys
import time
import select

def _human(secs: float) -> str:
    secs = int(secs)
    if secs >= 3600:
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        return f"{h}h {m}m {s}s"
    if secs >= 60:
        m, s = divmod(secs, 60)
        return f"{m}m {s}s"
    return f"{secs}s"

def parse_duration(spec: str, default_unit: str = "m") -> float:
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
    return val * {"s": 1, "m": 60, "h": 3600}[unit]

def _read_line_nonblocking(timeout: float) -> str | None:
    r, _, _ = select.select([sys.stdin], [], [], timeout)
    if r:
        return sys.stdin.readline().rstrip("\n")
    return None

def _drain_stdin():
    """Remove any pending lines already typed before we start waiting."""
    # Option 1: termios flush (fastest)
    try:
        import termios
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
        return
    except Exception:
        pass
    # Option 2: select loop (fallback)
    while True:
        r, _, _ = select.select([sys.stdin], [], [], 0)
        if not r:
            break
        sys.stdin.readline()

def wait(seconds: float, *, poll: float = 0.5, default_unit: str = "m", clear_pending: bool = True) -> float:
    seconds = max(0.0, seconds)

    if clear_pending:
        _drain_stdin()   # <- NEW: swallow old Enters

    print(f"[wait] Waiting for {_human(seconds)} — (now, 2m, 30s)", flush=True, end=" ")

    start = time.time()
    deadline = start + seconds

    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            break

        chunk = min(poll, remaining)
        line = _read_line_nonblocking(chunk)

        if line is not None:
            cmd = line.strip().lower()
            if cmd in ("", "now", "skip"):
                deadline = time.time()
                print("[ctl] override => 0s", flush=True)
            else:
                try:
                    secs = parse_duration(cmd, default_unit=default_unit)
                except Exception as e:
                    print(f"[ctl] ignoring {cmd!r}: {e}", flush=True)
                else:
                    deadline = time.time() + secs
                    print(f"[ctl] override => {secs:.1f}s", flush=True)

    return time.time() - start

def wait_minutes(minutes: float, **kw) -> float:
    return wait(minutes * 60.0, **kw)
