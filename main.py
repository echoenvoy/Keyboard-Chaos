#!/usr/bin/env python3
"""
main.py — launch Keyboard Chaos.

Usage:
    python main.py                    # opens GUI (default)
    python main.py --interval 5       # GUI, remap every 5s
    python main.py --no-gui           # headless CLI mode
    python main.py --no-gui -i 15     # headless, remap every 15s
"""

import sys
import os

# Make sure both modules are importable from this directory
sys.path.insert(0, os.path.dirname(__file__))

import keyboard_chaos

if __name__ == '__main__':
    keyboard_chaos.cli_main()
