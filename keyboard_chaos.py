"""
keyboard_chaos.py
─────────────────
The engine. Intercepts every keypress and remaps it to a random key.
Remaps shuffle every N seconds (default 10).

Platform notes:
  • Linux  — uses /dev/uinput via the `keyboard` library (needs sudo or uinput group)
  • macOS  — uses the `keyboard` library (needs Accessibility permissions)
  • Windows — uses the `keyboard` library (needs to run as administrator for global hooks)

The `keyboard` library handles the cross-platform heavy lifting.
We suppress the real key and emit the mapped one instead.
"""

import keyboard
import random
import threading
import time
import json
import os
import sys
import signal
from datetime import datetime

# ── Mappable keys ──────────────────────────────────────────────────────────────
# We keep special keys like Ctrl, Alt, Win/Cmd out of the pool.
# The last thing anyone needs is Ctrl becoming Delete mid-sentence.

MAPPABLE_KEYS = [
    # Letters
    'a','b','c','d','e','f','g','h','i','j','k','l','m',
    'n','o','p','q','r','s','t','u','v','w','x','y','z',
    # Numbers row
    '1','2','3','4','5','6','7','8','9','0',
    # Punctuation / symbols (the chaotic seasoning)
    '-','=','[',']',';',"'",',','.','/',
    '`','\\',
    # Function keys (optional spice)
    'f1','f2','f3','f4','f5','f6',
    # Navigation
    'home','end','page up','page down',
    'insert',
    # Whitespace & editing
    'space','backspace','tab','delete',
    # Arrows
    'up','down','left','right',
    # Enter — the big one
    'enter',
]

# Panic key combination — always works, not remapped
PANIC_COMBO = 'ctrl+shift+r'

# ── State ──────────────────────────────────────────────────────────────────────
class ChaosState:
    def __init__(self):
        self.mapping: dict[str, str] = {}
        self.active = False
        self.interval = 10          # seconds between remaps
        self.remap_count = 0
        self.history: list[dict] = []
        self.lock = threading.Lock()
        self.on_remap_callback = None   # GUI can hook in here
        self.on_status_callback = None
        self._hooks = []
        self._timer_thread = None

state = ChaosState()


# ── Mapping logic ──────────────────────────────────────────────────────────────

def generate_mapping() -> dict[str, str]:
    """
    Create a random permutation of MAPPABLE_KEYS.
    Every key maps to a *different* key (no identity mappings).
    """
    keys = MAPPABLE_KEYS.copy()
    shuffled = keys.copy()

    # Ensure no key maps to itself (derangement-ish, good enough)
    while True:
        random.shuffle(shuffled)
        if all(k != s for k, s in zip(keys, shuffled)):
            break

    return dict(zip(keys, shuffled))


def apply_mapping():
    """Unhook old handlers, generate new mapping, register new handlers."""
    with state.lock:
        # Clear previous hooks
        for h in state._hooks:
            try:
                keyboard.unhook(h)
            except Exception:
                pass
        state._hooks.clear()

        # New mapping
        mapping = generate_mapping()
        state.mapping = mapping
        state.remap_count += 1

        timestamp = datetime.now().strftime('%H:%M:%S')
        state.history.insert(0, {
            'time': timestamp,
            'mapping': dict(list(mapping.items())[:8]),  # store first 8 for display
            'remap_number': state.remap_count,
        })
        # Keep history manageable
        if len(state.history) > 50:
            state.history = state.history[:50]

        # Register hooks for each key
        for src_key in mapping:
            # We need a closure to capture the current src/dst pair
            _register_hook(src_key, mapping[src_key])

    if state.on_remap_callback:
        state.on_remap_callback(state.mapping, state.remap_count)


def _register_hook(src: str, dst: str):
    """Register a suppress+emit hook for one key pair."""
    def handler(event):
        if event.event_type == keyboard.KEY_DOWN:
            keyboard.send(dst)
        # We suppress the original event either way
    try:
        h = keyboard.on_press_key(src, handler, suppress=True)
        state._hooks.append(h)
    except Exception as e:
        # Some keys may not be hookable on every platform — skip silently
        pass


# ── Timer loop ────────────────────────────────────────────────────────────────

def _remap_loop():
    """Background thread: remap every `state.interval` seconds while active."""
    while state.active:
        apply_mapping()
        # Sleep in small increments so we can stop promptly
        for _ in range(state.interval * 10):
            if not state.active:
                break
            time.sleep(0.1)


def start_chaos(interval: int = 10):
    """Start the chaos. Call from main thread or GUI."""
    if state.active:
        return
    state.active = True
    state.interval = max(3, interval)  # minimum 3s to avoid seizure-inducing speeds

    # Register panic restore combo (not suppressed)
    keyboard.add_hotkey(PANIC_COMBO, panic_restore, suppress=False)

    state._timer_thread = threading.Thread(target=_remap_loop, daemon=True)
    state._timer_thread.start()

    if state.on_status_callback:
        state.on_status_callback('running')

    print(f"[chaos] Started. Remap every {state.interval}s. Panic: {PANIC_COMBO}")


def stop_chaos():
    """Stop remapping and restore keyboard."""
    if not state.active:
        return
    state.active = False

    with state.lock:
        for h in state._hooks:
            try:
                keyboard.unhook(h)
            except Exception:
                pass
        state._hooks.clear()
        state.mapping = {}

    try:
        keyboard.remove_hotkey(PANIC_COMBO)
    except Exception:
        pass

    if state.on_status_callback:
        state.on_status_callback('stopped')

    print("[chaos] Stopped. Keyboard restored.")


def panic_restore():
    """Emergency restore — called by hotkey or GUI panic button."""
    print("[chaos] PANIC RESTORE triggered!")
    stop_chaos()
    if state.on_status_callback:
        state.on_status_callback('panic')


# ── CLI mode ──────────────────────────────────────────────────────────────────

def cli_main():
    """Run in terminal without GUI."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Keyboard Chaos — randomly remaps your keys every N seconds.',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        '--interval', '-i', type=int, default=10,
        help='Seconds between remaps (default: 10, min: 3)'
    )
    parser.add_argument(
        '--no-gui', action='store_true',
        help='Run in headless CLI mode'
    )
    args = parser.parse_args()

    if not args.no_gui:
        # Launch GUI by default
        from gui import launch_gui
        launch_gui(args.interval)
        return

    # Headless mode
    print("=" * 52)
    print("  KEYBOARD CHAOS — headless mode")
    print(f"  Remapping every {args.interval}s")
    print(f"  Panic restore: {PANIC_COMBO}")
    print("  Ctrl+C to quit cleanly")
    print("=" * 52)

    def on_remap(mapping, count):
        print(f"\n[remap #{count}] New mapping (sample):")
        for src, dst in list(mapping.items())[:6]:
            print(f"   {src:12s} → {dst}")

    state.on_remap_callback = on_remap

    # Graceful exit on Ctrl+C
    def handle_sigint(sig, frame):
        print("\n[chaos] Ctrl+C received. Restoring keyboard...")
        stop_chaos()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    start_chaos(args.interval)

    # Keep main thread alive
    while state.active:
        time.sleep(0.5)


if __name__ == '__main__':
    cli_main()
