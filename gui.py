"""
gui.py
──────
Tkinter GUI for Keyboard Chaos.
Shows live key mapping, countdown timer, remap history, and the big red PANIC button.

Design direction: glitchy terminal / CRT monitor aesthetic.
Monospace everything. Green-on-black. Scanlines. Random flicker animations.
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
import time
import random
import sys

# We import the engine lazily inside launch_gui to avoid circular imports
# when this module is used standalone.


# ── Colour palette ─────────────────────────────────────────────────────────────
BG        = '#0b0e0b'
BG2       = '#111511'
GREEN     = '#39ff14'   # neon green — classic terminal
GREEN_DIM = '#1a7a08'
AMBER     = '#ffb300'
RED       = '#ff2222'
RED_DIM   = '#7a0808'
MUTED     = '#2a3a2a'
TEXT      = '#c8e6c9'
WHITE     = '#eeffee'


class ChaosGUI:
    def __init__(self, root: tk.Tk, engine):
        self.root = root
        self.engine = engine
        self.countdown = engine.state.interval
        self._countdown_job = None
        self._flicker_job = None
        self._build_ui()
        self._start_countdown()
        self._start_flicker()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = self.root
        root.title('KEYBOARD CHAOS v1.0')
        root.configure(bg=BG)
        root.geometry('720x640')
        root.resizable(False, False)
        root.protocol('WM_DELETE_WINDOW', self._on_close)

        # Try to load a monospace font; fall back gracefully
        mono_options = ['Courier New', 'Courier', 'Lucida Console', 'Consolas', 'monospace']
        self.mono = mono_options[0]  # tkinter will fall back if missing

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(root, bg=BG, pady=0)
        hdr.pack(fill='x', padx=20, pady=(18, 0))

        self.title_lbl = tk.Label(
            hdr,
            text='[ KEYBOARD CHAOS ]',
            bg=BG,
            fg=GREEN,
            font=(self.mono, 20, 'bold'),
        )
        self.title_lbl.pack()

        tk.Label(
            hdr,
            text='your keys are not your own anymore',
            bg=BG,
            fg=GREEN_DIM,
            font=(self.mono, 9),
        ).pack()

        # Divider
        self._divider(root)

        # ── Status row ────────────────────────────────────────────────────────
        status_row = tk.Frame(root, bg=BG)
        status_row.pack(fill='x', padx=20, pady=(10, 0))

        tk.Label(status_row, text='STATUS:', bg=BG, fg=MUTED,
                 font=(self.mono, 9)).pack(side='left')

        self.status_lbl = tk.Label(
            status_row, text='● IDLE',
            bg=BG, fg=AMBER,
            font=(self.mono, 9, 'bold'),
        )
        self.status_lbl.pack(side='left', padx=(6, 0))

        # Countdown on the right
        tk.Label(status_row, text='NEXT REMAP IN:', bg=BG, fg=MUTED,
                 font=(self.mono, 9)).pack(side='right', padx=(0, 6))

        self.countdown_lbl = tk.Label(
            status_row,
            text='--s',
            bg=BG, fg=GREEN,
            font=(self.mono, 14, 'bold'),
            width=5,
        )
        self.countdown_lbl.pack(side='right')

        # Remap counter
        counter_row = tk.Frame(root, bg=BG)
        counter_row.pack(fill='x', padx=20, pady=(4, 0))

        tk.Label(counter_row, text='REMAPS SURVIVED:', bg=BG, fg=MUTED,
                 font=(self.mono, 9)).pack(side='left')

        self.remap_count_lbl = tk.Label(
            counter_row, text='0',
            bg=BG, fg=AMBER,
            font=(self.mono, 9, 'bold'),
        )
        self.remap_count_lbl.pack(side='left', padx=6)

        # ── Interval slider ───────────────────────────────────────────────────
        slider_row = tk.Frame(root, bg=BG)
        slider_row.pack(fill='x', padx=20, pady=(10, 0))

        tk.Label(slider_row, text='REMAP INTERVAL:', bg=BG, fg=MUTED,
                 font=(self.mono, 9)).pack(side='left')

        self.interval_var = tk.IntVar(value=10)
        self.interval_lbl = tk.Label(
            slider_row, text='10s',
            bg=BG, fg=GREEN,
            font=(self.mono, 9, 'bold'),
            width=4,
        )
        self.interval_lbl.pack(side='right')

        self.slider = tk.Scale(
            slider_row,
            from_=3, to=60,
            orient='horizontal',
            variable=self.interval_var,
            bg=BG, fg=GREEN,
            troughcolor=MUTED,
            highlightthickness=0,
            bd=0,
            command=self._on_slider,
            showvalue=False,
            length=380,
        )
        self.slider.pack(side='left', padx=(10, 0))

        # ── Control buttons ───────────────────────────────────────────────────
        self._divider(root)

        btn_row = tk.Frame(root, bg=BG)
        btn_row.pack(fill='x', padx=20, pady=10)

        self.start_btn = tk.Button(
            btn_row,
            text='▶  START CHAOS',
            bg=GREEN_DIM,
            fg=WHITE,
            activebackground=GREEN,
            activeforeground=BG,
            font=(self.mono, 11, 'bold'),
            bd=0,
            padx=18, pady=10,
            cursor='hand2',
            command=self._start,
            relief='flat',
        )
        self.start_btn.pack(side='left', expand=True, fill='x', padx=(0, 6))

        self.stop_btn = tk.Button(
            btn_row,
            text='■  STOP',
            bg=MUTED,
            fg=TEXT,
            activebackground='#3a4a3a',
            activeforeground=WHITE,
            font=(self.mono, 11, 'bold'),
            bd=0,
            padx=18, pady=10,
            cursor='hand2',
            command=self._stop,
            state='disabled',
            relief='flat',
        )
        self.stop_btn.pack(side='left', expand=True, fill='x', padx=(0, 6))

        # PANIC BUTTON
        self.panic_btn = tk.Button(
            btn_row,
            text='⚠  PANIC RESTORE',
            bg=RED_DIM,
            fg=WHITE,
            activebackground=RED,
            activeforeground=WHITE,
            font=(self.mono, 11, 'bold'),
            bd=0,
            padx=18, pady=10,
            cursor='hand2',
            command=self._panic,
            relief='flat',
        )
        self.panic_btn.pack(side='left', expand=True, fill='x')

        # Panic hint
        tk.Label(
            root,
            text=f'keyboard shortcut: Ctrl+Shift+R',
            bg=BG, fg=MUTED,
            font=(self.mono, 8),
        ).pack()

        # ── Live key map ──────────────────────────────────────────────────────
        self._divider(root)

        map_hdr = tk.Frame(root, bg=BG)
        map_hdr.pack(fill='x', padx=20, pady=(6, 4))
        tk.Label(map_hdr, text='CURRENT MAPPING (sample)', bg=BG, fg=MUTED,
                 font=(self.mono, 8, 'bold')).pack(side='left')

        self.map_frame = tk.Frame(root, bg=BG2, bd=0)
        self.map_frame.pack(fill='x', padx=20)

        self.map_labels = []
        # 4 columns × 4 rows = 16 visible mappings
        for row in range(4):
            for col in range(4):
                cell = tk.Frame(self.map_frame, bg=BG2, padx=4, pady=3)
                cell.grid(row=row, column=col, sticky='w', padx=6)
                lbl = tk.Label(
                    cell, text='',
                    bg=BG2, fg=GREEN_DIM,
                    font=(self.mono, 9),
                    width=18, anchor='w',
                )
                lbl.pack()
                self.map_labels.append(lbl)

        # ── History log ───────────────────────────────────────────────────────
        self._divider(root)

        log_hdr = tk.Frame(root, bg=BG)
        log_hdr.pack(fill='x', padx=20, pady=(4, 4))
        tk.Label(log_hdr, text='REMAP LOG', bg=BG, fg=MUTED,
                 font=(self.mono, 8, 'bold')).pack(side='left')

        self.log_text = tk.Text(
            root,
            bg=BG2, fg=GREEN_DIM,
            font=(self.mono, 8),
            height=5,
            bd=0,
            padx=8, pady=6,
            state='disabled',
            wrap='word',
            insertbackground=GREEN,
            selectbackground=GREEN_DIM,
            highlightthickness=0,
        )
        self.log_text.pack(fill='x', padx=20, pady=(0, 16))

        self._log('System ready. Press START CHAOS to begin.')
        self._log('Panic restore hotkey: Ctrl+Shift+R')

    def _divider(self, parent):
        tk.Frame(parent, bg=MUTED, height=1).pack(fill='x', padx=20, pady=6)

    # ── Controls ───────────────────────────────────────────────────────────────

    def _start(self):
        interval = self.interval_var.get()
        self.countdown = interval
        self.engine.state.on_remap_callback = self._on_remap
        self.engine.state.on_status_callback = self._on_status
        self.engine.start_chaos(interval)
        self._set_status('running', GREEN)
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.slider.config(state='disabled')
        self._log(f'Chaos started. Interval: {interval}s')

    def _stop(self):
        self.engine.stop_chaos()
        self._set_status('stopped', AMBER)
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.slider.config(state='normal')
        self._clear_map()
        self._log('Chaos stopped. Keyboard restored.')

    def _panic(self):
        self.engine.panic_restore()
        self._set_status('PANIC — RESTORED', RED)
        self.root.after(200, self._flash_panic)
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.slider.config(state='normal')
        self._clear_map()
        self._log('⚠ PANIC RESTORE triggered!')

    def _flash_panic(self):
        """Flash the background red briefly."""
        original = BG
        self.root.configure(bg=RED_DIM)
        self.root.after(120, lambda: self.root.configure(bg=original))

    def _on_close(self):
        self.engine.stop_chaos()
        self.root.destroy()

    def _on_slider(self, val):
        self.interval_lbl.config(text=f'{val}s')

    # ── Callbacks from engine ──────────────────────────────────────────────────

    def _on_remap(self, mapping: dict, count: int):
        """Called from background thread — use after() to touch UI."""
        self.root.after(0, lambda: self._update_map(mapping, count))

    def _on_status(self, status: str):
        colours = {'running': GREEN, 'stopped': AMBER, 'panic': RED}
        colour = colours.get(status, AMBER)
        self.root.after(0, lambda: self._set_status(status.upper(), colour))

    # ── UI helpers ─────────────────────────────────────────────────────────────

    def _set_status(self, text: str, colour: str):
        self.status_lbl.config(text=f'● {text.upper()}', fg=colour)

    def _update_map(self, mapping: dict, count: int):
        self.remap_count_lbl.config(text=str(count))
        self.countdown = self.engine.state.interval  # reset countdown

        pairs = list(mapping.items())
        random.shuffle(pairs)  # show random subset each time for variety
        pairs = pairs[:16]

        for i, lbl in enumerate(self.map_labels):
            if i < len(pairs):
                src, dst = pairs[i]
                lbl.config(
                    text=f'{src:>10}  →  {dst}',
                    fg=GREEN,
                )
                # Animate: briefly flash bright then dim
                self.root.after(80 * i, lambda l=lbl: l.config(fg=WHITE))
                self.root.after(80 * i + 300, lambda l=lbl: l.config(fg=GREEN))
            else:
                lbl.config(text='', fg=GREEN_DIM)

        self._log(f'Remap #{count} — {len(mapping)} keys shuffled')

    def _clear_map(self):
        for lbl in self.map_labels:
            lbl.config(text='', fg=GREEN_DIM)

    def _log(self, msg: str):
        ts = time.strftime('%H:%M:%S')
        self.log_text.config(state='normal')
        self.log_text.insert('end', f'[{ts}] {msg}\n')
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    # ── Countdown timer ────────────────────────────────────────────────────────

    def _start_countdown(self):
        self._tick_countdown()

    def _tick_countdown(self):
        if self.engine.state.active:
            self.countdown = max(0, self.countdown - 1)
            colour = RED if self.countdown <= 3 else (AMBER if self.countdown <= 6 else GREEN)
            self.countdown_lbl.config(text=f'{self.countdown}s', fg=colour)
        else:
            self.countdown_lbl.config(text='--s', fg=MUTED)

        self._countdown_job = self.root.after(1000, self._tick_countdown)

    # ── Flicker effect ─────────────────────────────────────────────────────────

    def _start_flicker(self):
        self._flicker()

    def _flicker(self):
        """Occasionally flicker the title to sell the glitch aesthetic."""
        if random.random() < 0.07:  # 7% chance each cycle
            glitch_chars = '!@#$%^&*?<>|/\\'
            glitched = ''.join(
                random.choice(glitch_chars) if random.random() < 0.3 else c
                for c in '[ KEYBOARD CHAOS ]'
            )
            self.title_lbl.config(text=glitched)
            self.root.after(80, lambda: self.title_lbl.config(text='[ KEYBOARD CHAOS ]'))

        self._flicker_job = self.root.after(400, self._flicker)


# ── Entry point ────────────────────────────────────────────────────────────────

def launch_gui(interval: int = 10):
    import keyboard_chaos as engine

    root = tk.Tk()

    # Try to set a window icon (silently skip if it fails)
    try:
        root.iconbitmap('')
    except Exception:
        pass

    gui = ChaosGUI(root, engine)
    gui.interval_var.set(interval)
    gui.slider.set(interval)
    gui.interval_lbl.config(text=f'{interval}s')

    root.mainloop()


if __name__ == '__main__':
    launch_gui()
