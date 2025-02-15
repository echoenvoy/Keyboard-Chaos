# ⌨️ Keyboard Chaos

Randomly remaps every key on your keyboard every N seconds. Includes a GUI dashboard with a live mapping display, countdown timer, remap history log, and a big red PANIC RESTORE button for when things go sideways.

This is, objectively, a terrible idea. You will enjoy it.

---

## What it does

- **Remaps all keys** to random keys every 10 seconds (configurable)
- **Every key maps to a different key** — no identity mappings, no mercy
- **GUI dashboard** shows the current mapping in real time, countdown to next remap, and a full history log
- **Panic restore** — press `Ctrl+Shift+R` or click the button to instantly restore your keyboard
- **CLI / headless mode** for running without a GUI

### Example

```
Before remap:             After remap:
  a → q                     a → [
  s → w                     s → p
  enter → backspace         enter → f6
  space → delete            space → '
```

---

## Requirements

- Python 3.8+
- The `keyboard` library (listed in `requirements.txt`)
- tkinter (comes with Python on Windows/macOS; on Linux: `sudo apt install python3-tk`)

### Platform permissions

| Platform | Requirement |
|----------|-------------|
| **Windows** | Run as Administrator |
| **macOS** | Grant Accessibility permissions (System Preferences → Privacy → Accessibility) |
| **Linux** | Run with `sudo`, or add yourself to the `input` group |

The `keyboard` library needs low-level input access to intercept and suppress real keypresses. This is not optional.

---

## Setup

```bash
# 1. Clone / unzip the project
cd keyboard-chaos

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running

### GUI mode (default)

```bash
python main.py
```


### CLI / headless mode

```bash
python main.py --no-gui
python main.py --no-gui --interval 5
```

### Options

```
--interval N   Seconds between remaps (default: 10, minimum: 3)
--no-gui       Run without the GUI (terminal output only)
```

---

## GUI overview

```
┌─────────────────────────────────────────────┐
│          [ KEYBOARD CHAOS ]                 │
│    your keys are not your own anymore       │
├─────────────────────────────────────────────┤
│ STATUS: ● RUNNING          NEXT REMAP IN: 7s│
│ REMAPS SURVIVED: 3                          │
│ INTERVAL: ─────●──────── 10s                │
├─────────────────────────────────────────────┤
│ [ ▶ START CHAOS ] [ ■ STOP ] [⚠ PANIC ]    │
├─────────────────────────────────────────────┤
│ CURRENT MAPPING (sample)                    │
│   a → [     enter → f5    space → z         │
│   s → '     tab → page up  h → delete       │
│   ...                                       │
├─────────────────────────────────────────────┤
│ REMAP LOG                                   │
│ [14:02:11] Chaos started. Interval: 10s     │
│ [14:02:21] Remap #1 — 55 keys shuffled      │
│ [14:02:31] Remap #2 — 55 keys shuffled      │
└─────────────────────────────────────────────┘
```

---

## Project structure

```
keyboard-chaos/
├── main.py             # Entry point, CLI argument parsing
├── keyboard_chaos.py   # Core engine: key hooks, mapping, timer loop
├── gui.py              # Tkinter GUI dashboard
├── requirements.txt
└── README.md
```

---

## How it works

1. `keyboard_chaos.py` generates a random derangement of all mappable keys — a permutation where no key maps to itself
2. For each key in the mapping, it registers a `keyboard.on_press_key` hook that suppresses the real keypress and immediately emits the mapped key instead
3. A background thread fires every `interval` seconds: old hooks are removed, a new mapping is generated, new hooks are registered
4. The panic restore (`Ctrl+Shift+R` or GUI button) calls `stop_chaos()`, which unhooks everything and clears the mapping — keyboard is instantly normal again

The `keyboard` library handles the low-level OS-specific input interception on Windows, macOS, and Linux.

---

## A note on responsibility

This will confuse you, your coworkers, and anyone who touches your keyboard. It is completely reversible at any time via the panic button. Don't run it during anything important. I warned you.

