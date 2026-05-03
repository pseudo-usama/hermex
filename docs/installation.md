# Installation

## Requirements

- Python 3.11 or higher
- Google Chrome installed on your system

## Install

```bash
pip install hermex
```

## Data directory

Hermex stores its browser profile and session data in a platform-specific directory:

| Platform | Path |
|---|---|
| macOS | `~/Library/Application Support/hermex` |
| Linux | `~/.local/share/hermex` |
| Windows | `C:\Users\<user>\AppData\Local\hermex` |

You can override this by passing `data_dir` to the constructor or to `setup()`.

## Next step

Run first-time setup before using Hermex for the first time — see [Quickstart](quickstart.md).
