"""
CSV Visualizer — interactive data explorer for serial logger CSV files.

Features:
  - File picker dialog
  - Variable selector: group signals into separate subplots or overlay them
  - Synchronized vertical crosshair across all subplots on hover
  - Zoom / pan on one plot syncs to all others (shared X axis)

Dependencies:
    pip install pandas matplotlib
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Button as MplButton
import numpy as np


# ══════════════════════════════════════════════════════════
#  CSV loading
# ══════════════════════════════════════════════════════════

def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    # Add a plain integer index column for the X axis if there's no timestamp
    df.insert(0, "__index__", range(len(df)))
    return df


# ══════════════════════════════════════════════════════════
#  Selector GUI  (tkinter)
# ══════════════════════════════════════════════════════════

class SelectorApp(tk.Tk):
    """
    Shows all column names.  The user builds an ordered list of "plot groups":
    each group is a set of columns that share one subplot.
    """

    def __init__(self, columns: list[str]):
        super().__init__()
        self.title("CSV Visualizer — Variable Selector")
        self.resizable(True, True)
        self.configure(bg="#1e1e2e")

        # result: list of lists of column names  (one inner list = one subplot)
        self.plot_groups: list[list[str]] = []
        self.confirmed = False

        self._columns = [c for c in columns if c != "__index__"]
        self._groups: list[list[str]] = []   # built up by the user
        self._current_group: list[str] = []  # staging area

        self._build_ui()

    # ── UI construction ───────────────────────────────────

    def _build_ui(self):
        PAD = 8
        BG  = "#1e1e2e"
        FG  = "#cdd6f4"
        ACC = "#89b4fa"
        BTN_BG = "#313244"

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame",       background=BG)
        style.configure("TLabel",       background=BG, foreground=FG, font=("Segoe UI", 10))
        style.configure("TButton",      background=BTN_BG, foreground=FG,
                        font=("Segoe UI", 9, "bold"), padding=5)
        style.map("TButton",
                  background=[("active", "#45475a")],
                  foreground=[("active", ACC)])
        style.configure("Accent.TButton", background="#313244", foreground=ACC,
                        font=("Segoe UI", 9, "bold"), padding=5)
        style.configure("TLabelframe",  background=BG, foreground=ACC,
                        font=("Segoe UI", 9, "bold"))
        style.configure("TLabelframe.Label", background=BG, foreground=ACC)
        style.configure("TListbox",     background="#313244", foreground=FG)

        root_frame = ttk.Frame(self, padding=PAD)
        root_frame.pack(fill="both", expand=True)

        # ── Top: instructions ─────────────────────────────
        ttk.Label(root_frame,
                  text="① Select variables  ② Add to group  ③ Confirm group  ④ Repeat  ⑤ Plot",
                  font=("Segoe UI", 9, "italic")).grid(row=0, column=0, columnspan=3,
                                                        sticky="w", pady=(0, PAD))

        # ── Left: available columns ───────────────────────
        avail_frame = ttk.LabelFrame(root_frame, text=" Available Variables ", padding=PAD)
        avail_frame.grid(row=1, column=0, sticky="nsew", padx=(0, PAD))

        self._avail_box = tk.Listbox(
            avail_frame, selectmode="multiple", exportselection=False,
            bg="#313244", fg=FG, selectbackground=ACC, selectforeground="#1e1e2e",
            font=("Consolas", 9), width=28, height=30, bd=0, highlightthickness=1,
            highlightcolor=ACC, activestyle="none"
        )
        avail_scroll = ttk.Scrollbar(avail_frame, orient="vertical",
                                     command=self._avail_box.yview)
        self._avail_box.configure(yscrollcommand=avail_scroll.set)
        self._avail_box.pack(side="left", fill="both", expand=True)
        avail_scroll.pack(side="right", fill="y")

        for col in self._columns:
            self._avail_box.insert("end", col)

        # ── Middle: buttons ───────────────────────────────
        mid_frame = ttk.Frame(root_frame, padding=PAD)
        mid_frame.grid(row=1, column=1, sticky="ns")

        btn_cfg = dict(width=20)

        ttk.Button(mid_frame, text="→  Add to group",
                   command=self._add_to_group, **btn_cfg).pack(pady=4)
        ttk.Button(mid_frame, text="✖  Remove from group",
                   command=self._remove_from_group, **btn_cfg).pack(pady=4)

        ttk.Label(mid_frame, text="").pack(pady=6)

        ttk.Button(mid_frame, text="✔  Confirm group\n   (new subplot)",
                   command=self._confirm_group, style="Accent.TButton",
                   **btn_cfg).pack(pady=4)
        ttk.Button(mid_frame, text="✖  Discard group",
                   command=self._discard_group, **btn_cfg).pack(pady=4)

        ttk.Label(mid_frame, text="").pack(pady=6)

        ttk.Button(mid_frame, text="⬆  Move group up",
                   command=lambda: self._move_group(-1), **btn_cfg).pack(pady=4)
        ttk.Button(mid_frame, text="⬇  Move group down",
                   command=lambda: self._move_group(+1), **btn_cfg).pack(pady=4)
        ttk.Button(mid_frame, text="🗑  Delete group",
                   command=self._delete_group, **btn_cfg).pack(pady=4)

        ttk.Label(mid_frame, text="").pack(pady=10)

        ttk.Button(mid_frame, text="📊  PLOT",
                   command=self._plot, style="Accent.TButton",
                   **btn_cfg).pack(pady=4)

        # ── Right: current group staging + confirmed groups ─
        right_frame = ttk.Frame(root_frame)
        right_frame.grid(row=1, column=2, sticky="nsew")

        staging_frame = ttk.LabelFrame(right_frame,
                                        text=" Current Group (staging) ", padding=PAD)
        staging_frame.pack(fill="both", expand=True, pady=(0, PAD))

        self._staging_box = tk.Listbox(
            staging_frame, selectmode="single", exportselection=False,
            bg="#313244", fg="#a6e3a1", selectbackground="#a6e3a1",
            selectforeground="#1e1e2e", font=("Consolas", 9), width=28, height=10,
            bd=0, highlightthickness=1, highlightcolor="#a6e3a1", activestyle="none"
        )
        stg_scroll = ttk.Scrollbar(staging_frame, orient="vertical",
                                   command=self._staging_box.yview)
        self._staging_box.configure(yscrollcommand=stg_scroll.set)
        self._staging_box.pack(side="left", fill="both", expand=True)
        stg_scroll.pack(side="right", fill="y")

        groups_frame = ttk.LabelFrame(right_frame,
                                       text=" Confirmed Plot Groups ", padding=PAD)
        groups_frame.pack(fill="both", expand=True)

        self._groups_box = tk.Listbox(
            groups_frame, selectmode="single", exportselection=False,
            bg="#313244", fg="#fab387", selectbackground="#fab387",
            selectforeground="#1e1e2e", font=("Consolas", 9), width=28, height=18,
            bd=0, highlightthickness=1, highlightcolor="#fab387", activestyle="none"
        )
        grp_scroll = ttk.Scrollbar(groups_frame, orient="vertical",
                                   command=self._groups_box.yview)
        self._groups_box.configure(yscrollcommand=grp_scroll.set)
        self._groups_box.pack(side="left", fill="both", expand=True)
        grp_scroll.pack(side="right", fill="y")

        # ── Column weights ────────────────────────────────
        root_frame.columnconfigure(0, weight=1)
        root_frame.columnconfigure(1, weight=0)
        root_frame.columnconfigure(2, weight=1)
        root_frame.rowconfigure(1, weight=1)

    # ── Actions ───────────────────────────────────────────

    def _add_to_group(self):
        sel = self._avail_box.curselection()
        for i in sel:
            col = self._avail_box.get(i)
            if col not in self._current_group:
                self._current_group.append(col)
                self._staging_box.insert("end", col)

    def _remove_from_group(self):
        sel = self._staging_box.curselection()
        if not sel:
            return
        idx = sel[0]
        self._current_group.pop(idx)
        self._staging_box.delete(idx)

    def _confirm_group(self):
        if not self._current_group:
            messagebox.showwarning("Empty group", "Add at least one variable first.")
            return
        self._groups.append(list(self._current_group))
        label = " + ".join(self._current_group)
        self._groups_box.insert("end", f"[{len(self._groups)}] {label}")
        self._current_group.clear()
        self._staging_box.delete(0, "end")

    def _discard_group(self):
        self._current_group.clear()
        self._staging_box.delete(0, "end")

    def _move_group(self, direction: int):
        sel = self._groups_box.curselection()
        if not sel:
            return
        idx = sel[0]
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self._groups):
            return
        self._groups[idx], self._groups[new_idx] = self._groups[new_idx], self._groups[idx]
        self._refresh_groups_box()
        self._groups_box.selection_set(new_idx)

    def _delete_group(self):
        sel = self._groups_box.curselection()
        if not sel:
            return
        idx = sel[0]
        self._groups.pop(idx)
        self._refresh_groups_box()

    def _refresh_groups_box(self):
        self._groups_box.delete(0, "end")
        for i, g in enumerate(self._groups, 1):
            label = " + ".join(g)
            self._groups_box.insert("end", f"[{i}] {label}")

    def _plot(self):
        if not self._groups:
            messagebox.showwarning("No groups", "Confirm at least one plot group first.")
            return
        self.plot_groups = self._groups
        self.confirmed = True
        self.destroy()


# ══════════════════════════════════════════════════════════
#  Plotting with synchronised crosshair
# ══════════════════════════════════════════════════════════

COLORS = [
    "#89b4fa", "#a6e3a1", "#fab387", "#f38ba8",
    "#cba6f7", "#f9e2af", "#94e2d5", "#eba0ac",
    "#b4befe", "#89dceb", "#74c7ec", "#cdd6f4",
]

def plot_groups(df: pd.DataFrame, groups: list[list[str]]):
    n = len(groups)
    fig = plt.figure(figsize=(14, 3.5 * n), facecolor="#1e1e2e")
    fig.subplots_adjust(hspace=0.35, left=0.07, right=0.97, top=0.95, bottom=0.06)

    gs = gridspec.GridSpec(n, 1, figure=fig)
    axes = []

    x = df["__index__"].values

    for i, group in enumerate(groups):
        if i == 0:
            ax = fig.add_subplot(gs[i])
        else:
            ax = fig.add_subplot(gs[i], sharex=axes[0])

        ax.set_facecolor("#181825")
        ax.tick_params(colors="#cdd6f4", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#45475a")
        ax.yaxis.label.set_color("#cdd6f4")
        ax.xaxis.label.set_color("#cdd6f4")
        ax.grid(True, color="#313244", linewidth=0.6, linestyle="--", alpha=0.7)

        for j, col in enumerate(group):
            if col not in df.columns:
                continue
            y = pd.to_numeric(df[col], errors="coerce").values
            color = COLORS[j % len(COLORS)]
            ax.plot(x, y, color=color, linewidth=1.2, label=col)

        ax.legend(loc="upper right", fontsize=7.5,
                  facecolor="#313244", edgecolor="#45475a",
                  labelcolor="#cdd6f4", framealpha=0.9)

        if i == n - 1:
            ax.set_xlabel("Sample index", color="#cdd6f4", fontsize=9)

        axes.append(ax)

    # ── Synchronised vertical crosshair ──────────────────
    vlines = [ax.axvline(x=0, color="#f5c2e7", linewidth=0.8,
                         linestyle="--", visible=False)
              for ax in axes]

    annots = []
    for ax in axes:
        ann = ax.annotate(
            "", xy=(0, 0), xytext=(6, 6), textcoords="offset points",
            fontsize=7.5,
            color="#1e1e2e",
            bbox=dict(boxstyle="round,pad=0.3", fc="#f5c2e7", ec="#f5c2e7", alpha=0.9),
            visible=False
        )
        annots.append(ann)

    def on_move(event):
        if event.inaxes is None:
            for vl in vlines:
                vl.set_visible(False)
            for ann in annots:
                ann.set_visible(False)
            fig.canvas.draw_idle()
            return

        xdata = event.xdata
        if xdata is None:
            return

        # snap to nearest sample
        idx = int(round(xdata))
        idx = max(0, min(idx, len(x) - 1))

        for vl in vlines:
            vl.set_xdata([idx, idx])
            vl.set_visible(True)

        for k, (ax, ann) in enumerate(zip(axes, annots)):
            group = groups[k]
            parts = []
            for col in group:
                if col in df.columns:
                    val = df[col].iloc[idx]
                    try:
                        parts.append(f"{col}: {float(val):.4g}")
                    except (ValueError, TypeError):
                        parts.append(f"{col}: {val}")
            label = "\n".join(parts)

            # position annotation inside axes
            ax_xlim = ax.get_xlim()
            ax_ylim = ax.get_ylim()
            tx = ax_xlim[1] - (ax_xlim[1] - ax_xlim[0]) * 0.01
            ty = ax_ylim[1] - (ax_ylim[1] - ax_ylim[0]) * 0.05
            ann.set_position((tx, ty))
            ann.xy = (idx, ty)
            ann.set_text(label)
            ann.set_visible(True)

        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_move)

    fig.suptitle("CSV Visualizer", color="#cdd6f4", fontsize=13,
                 fontweight="bold", y=0.98)

    plt.show()


# ══════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════

def pick_file() -> str | None:
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Select CSV file",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    root.destroy()
    return path or None


def main():
    # 1 — pick CSV
    path = pick_file()
    if not path:
        print("No file selected. Exiting.")
        sys.exit(0)

    print(f"Loading: {path}")
    try:
        df = load_csv(path)
    except Exception as e:
        print(f"Failed to load CSV: {e}")
        sys.exit(1)

    cols = [c for c in df.columns if c != "__index__"]
    print(f"Detected {len(cols)} columns: {', '.join(cols)}")

    # 2 — variable selector
    app = SelectorApp(cols)
    app.mainloop()

    if not app.confirmed or not app.plot_groups:
        print("No groups confirmed. Exiting.")
        sys.exit(0)

    # 3 — plot
    print(f"\nPlotting {len(app.plot_groups)} subplot(s):")
    for i, g in enumerate(app.plot_groups, 1):
        print(f"  Subplot {i}: {', '.join(g)}")

    plot_groups(df, app.plot_groups)


if __name__ == "__main__":
    main()
