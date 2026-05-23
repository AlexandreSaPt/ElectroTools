#!/usr/bin/env python3
"""
Tool Launcher - A GUI app to manage and run your Python scripts
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import subprocess
import sys
import uuid
import platform
from pathlib import Path

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
JSON_FILE   = SCRIPT_DIR / "tools.json"

# ---------------------------------------------------------------------------
# Cross-platform font
# ---------------------------------------------------------------------------
_sys = platform.system()
FONT = "SF Pro Display" if _sys == "Darwin" else ("Segoe UI" if _sys == "Windows" else "Ubuntu Sans")

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
BG           = "#F5F5F7"
CARD_BG      = "#FFFFFF"
HEADER_BG    = "#1D1D1F"
ACCENT       = "#0071E3"
ACCENT_H     = "#005BBB"
TEXT         = "#1D1D1F"
TEXT_MUTED   = "#6E6E73"
BORDER       = "#D2D2D7"
IMG_BG       = "#EBEBF0"
RUN_BG       = "#34C759"
RUN_H        = "#28A745"
DEL_FG       = "#FF3B30"


# ===========================================================================
# Main Application
# ===========================================================================
class ToolLauncherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Tool Launcher")
        self.root.geometry("1060x700")
        self.root.minsize(500, 400)
        self.root.configure(bg=BG)

        self.tools: list[dict] = []
        self.cards: list[tk.Frame] = []
        self.photo_cache: dict = {}   # keeps PhotoImage refs alive
        self._resize_job = None

        self._load_tools()
        self._build_ui()
        self._render_tools()

    # -----------------------------------------------------------------------
    # JSON helpers
    # -----------------------------------------------------------------------
    def _load_tools(self):
        if JSON_FILE.exists():
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as fh:
                    self.tools = json.load(fh)
            except Exception:
                self.tools = []
        else:
            self.tools = []

    def _save_tools(self):
        with open(JSON_FILE, "w", encoding="utf-8") as fh:
            json.dump(self.tools, fh, indent=2, ensure_ascii=False)

    # -----------------------------------------------------------------------
    # UI construction
    # -----------------------------------------------------------------------
    def _build_ui(self):
        # ── Header bar ──────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=HEADER_BG, height=62)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="🛠   Tool Launcher",
            bg=HEADER_BG, fg="white",
            font=(FONT, 17, "bold"),
        ).pack(side="left", padx=22, pady=14)

        add_btn = tk.Button(
            header, text="  ＋  Add Tool",
            bg=ACCENT, fg="white",
            font=(FONT, 11, "bold"),
            relief="flat", bd=0,
            padx=18, pady=7,
            cursor="hand2",
            command=self._open_add_dialog,
        )
        add_btn.pack(side="right", padx=20, pady=12)
        add_btn.bind("<Enter>", lambda _: add_btn.config(bg=ACCENT_H))
        add_btn.bind("<Leave>", lambda _: add_btn.config(bg=ACCENT))

        # ── Scrollable canvas ───────────────────────────────────────────────
        container = tk.Frame(self.root, bg=BG)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = tk.Frame(self.canvas, bg=BG)
        self._cw = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        self.grid_frame.bind("<Configure>", lambda _: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # Mouse-wheel scrolling (Windows / macOS / Linux)
        self.canvas.bind_all("<MouseWheel>", self._scroll)
        self.canvas.bind_all("<Button-4>",   self._scroll)
        self.canvas.bind_all("<Button-5>",   self._scroll)

    def _scroll(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self._cw, width=event.width)
        # Debounce reflow
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(80, self._reflow)

    def _reflow(self):
        w = self.canvas.winfo_width()
        if w < 10 or not self.cards:
            return
        cols = max(1, w // 250)
        for c in range(cols):
            self.grid_frame.columnconfigure(c, weight=1)
        for i, card in enumerate(self.cards):
            r, c = divmod(i, cols)
            card.grid(row=r, column=c, padx=14, pady=14, sticky="nsew")

    # -----------------------------------------------------------------------
    # Rendering
    # -----------------------------------------------------------------------
    def _render_tools(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.cards.clear()
        self.photo_cache.clear()

        if not self.tools:
            self._show_empty()
            return

        for tool in self.tools:
            self.cards.append(self._make_card(tool))

        self.root.after(60, self._reflow)

    def _show_empty(self):
        f = tk.Frame(self.grid_frame, bg=BG)
        f.pack(expand=True, fill="both", pady=100)
        tk.Label(f, text="🗂️",    bg=BG, font=(FONT, 52)).pack()
        tk.Label(f, text="No tools yet",
                 bg=BG, fg=TEXT, font=(FONT, 16, "bold")).pack(pady=(8, 4))
        tk.Label(f, text='Press  "+ Add Tool"  to register your first script',
                 bg=BG, fg=TEXT_MUTED, font=(FONT, 12)).pack()

    def _make_card(self, tool: dict) -> tk.Frame:
        card = tk.Frame(
            self.grid_frame, bg=CARD_BG,
            highlightthickness=1, highlightbackground=BORDER,
        )

        # ── Image thumbnail ─────────────────────────────────────────────────
        img_frame = tk.Frame(card, bg=IMG_BG, height=126)
        img_frame.pack(fill="x")
        img_frame.pack_propagate(False)

        img_lbl = tk.Label(img_frame, bg=IMG_BG)
        img_lbl.pack(expand=True, fill="both")
        self._load_thumb(tool.get("image_path", ""), img_lbl)

        # Hover highlight on image
        for w in (card, img_frame, img_lbl):
            w.bind("<Enter>", lambda _, c=card: c.config(highlightbackground=ACCENT))
            w.bind("<Leave>", lambda _, c=card: c.config(highlightbackground=BORDER))

        # ── Text info ────────────────────────────────────────────────────────
        info = tk.Frame(card, bg=CARD_BG, padx=14, pady=10)
        info.pack(fill="both", expand=True)

        tk.Label(
            info, text=tool.get("title", "Untitled"),
            bg=CARD_BG, fg=TEXT,
            font=(FONT, 12, "bold"),
            anchor="w", wraplength=195, justify="left",
        ).pack(fill="x")

        desc = tool.get("description", "").strip()
        if desc:
            tk.Label(
                info, text=desc,
                bg=CARD_BG, fg=TEXT_MUTED,
                font=(FONT, 10),
                anchor="nw", justify="left", wraplength=195,
            ).pack(fill="x", pady=(4, 0))

        script_name = Path(tool.get("script_path", "")).name
        tk.Label(
            info, text=f"📄 {script_name}",
            bg=CARD_BG, fg=TEXT_MUTED,
            font=(FONT, 9),
            anchor="w",
        ).pack(fill="x", pady=(6, 0))

        # ── Button row ───────────────────────────────────────────────────────
        btn_row = tk.Frame(card, bg=CARD_BG, padx=14, pady=10)
        btn_row.pack(fill="x")

        run = tk.Button(
            btn_row, text="▶  Run",
            bg=RUN_BG, fg="white",
            font=(FONT, 10, "bold"),
            relief="flat", bd=0,
            padx=14, pady=5,
            cursor="hand2",
            command=lambda t=tool: self._run(t),
        )
        run.pack(side="left")
        run.bind("<Enter>", lambda _, b=run: b.config(bg=RUN_H))
        run.bind("<Leave>", lambda _, b=run: b.config(bg=RUN_BG))

        edit = tk.Button(
            btn_row, text="✎",
            bg=CARD_BG, fg=ACCENT,
            font=(FONT, 13),
            relief="flat", bd=0,
            padx=8, pady=5,
            cursor="hand2",
            command=lambda t=tool: self._open_edit_dialog(t),
        )
        edit.pack(side="right", padx=(4, 0))

        delete = tk.Button(
            btn_row, text="✕",
            bg=CARD_BG, fg=DEL_FG,
            font=(FONT, 11),
            relief="flat", bd=0,
            padx=8, pady=5,
            cursor="hand2",
            command=lambda t=tool: self._delete(t),
        )
        delete.pack(side="right")

        return card

    # -----------------------------------------------------------------------
    # Image loading
    # -----------------------------------------------------------------------
    def _load_thumb(self, image_path: str, label: tk.Label):
        if not image_path:
            label.config(text="🐍", font=(FONT, 38))
            return
        if not PIL_AVAILABLE:
            label.config(text="🖼️", font=(FONT, 38))
            return

        abs_path = SCRIPT_DIR / image_path
        if not abs_path.exists():
            label.config(text="🖼️", font=(FONT, 38))
            return

        try:
            img = Image.open(abs_path).convert("RGBA")
            img.thumbnail((220, 122), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            label.config(image=photo, text="")
            self.photo_cache[image_path] = photo      # keep ref alive!
        except Exception:
            label.config(text="🖼️", font=(FONT, 38))

    # -----------------------------------------------------------------------
    # Actions
    # -----------------------------------------------------------------------
    def _run(self, tool: dict):
        path = SCRIPT_DIR / tool.get("script_path", "")
        if not path.exists():
            messagebox.showerror("Script not found", f"Could not find:\n{path}")
            return
        script_dir = path.parent
        try:
            if sys.platform == "win32":
                # sys.executable may be pythonw.exe (no console) — swap it for
                # python.exe so child scripts get their own terminal window.
                python_exe = sys.executable.replace("pythonw.exe", "python.exe")
                subprocess.Popen(
                    [python_exe, str(path)],
                    cwd=script_dir,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:
                subprocess.Popen([sys.executable, str(path)], cwd=script_dir)
        except Exception as exc:
            messagebox.showerror("Launch error", str(exc))

    def _delete(self, tool: dict):
        if messagebox.askyesno(
            "Remove tool",
            f'Remove "{tool.get("title")}" from the launcher?\n'
            "(The script file will NOT be deleted.)",
        ):
            self.tools = [t for t in self.tools if t.get("id") != tool.get("id")]
            self._save_tools()
            self._render_tools()

    def _open_add_dialog(self):
        ToolDialog(self.root, self._on_tool_saved)

    def _open_edit_dialog(self, tool: dict):
        ToolDialog(self.root, self._on_tool_saved, existing=tool)

    def _on_tool_saved(self, data: dict):
        if "id" not in data:                          # new tool
            data["id"] = str(uuid.uuid4())
            self.tools.append(data)
        else:                                         # edit existing
            for i, t in enumerate(self.tools):
                if t["id"] == data["id"]:
                    self.tools[i] = data
                    break
        self._save_tools()
        self._render_tools()


# ===========================================================================
# Add / Edit Dialog
# ===========================================================================
class ToolDialog(tk.Toplevel):
    def __init__(self, parent, callback, existing: dict | None = None):
        super().__init__(parent)
        self.callback  = callback
        self.existing  = existing
        self.edit_mode = existing is not None

        self.title("Edit Tool" if self.edit_mode else "Add New Tool")
        self.geometry("500x450")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.grab_set()
        self.transient(parent)

        self._build()
        if self.edit_mode:
            self._populate()

        # Center over parent
        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        self.geometry(f"+{px + pw//2 - 250}+{py + ph//2 - 225}")

    # -----------------------------------------------------------------------
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=HEADER_BG, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(
            hdr,
            text="Edit Tool" if self.edit_mode else "Add New Tool",
            bg=HEADER_BG, fg="white",
            font=(FONT, 13, "bold"),
        ).pack(side="left", padx=18, pady=10)

        # Form body
        body = tk.Frame(self, bg=BG, padx=26, pady=18)
        body.pack(fill="both", expand=True)

        # Title
        self._lbl(body, "Tool Title *")
        self.v_title = tk.StringVar()
        self._entry(body, self.v_title).pack(fill="x", pady=(2, 14))

        # Description
        self._lbl(body, "Description")
        self.w_desc = tk.Text(
            body, height=3,
            font=(FONT, 11), relief="flat", bd=0,
            highlightthickness=1, highlightbackground=BORDER,
            bg="white", fg=TEXT, padx=8, pady=6,
        )
        self.w_desc.pack(fill="x", pady=(2, 14))

        # Script path
        self._lbl(body, "Script Path (relative) *")
        self.v_script = tk.StringVar()
        self._browse_row(body, self.v_script, self._browse_script).pack(fill="x", pady=(2, 14))

        # Image path
        self._lbl(body, "Image Path (relative, optional)")
        self.v_image = tk.StringVar()
        self._browse_row(body, self.v_image, self._browse_image).pack(fill="x", pady=(2, 14))

        # Save button
        tk.Button(
            body,
            text="Save  ✓",
            bg=ACCENT, fg="white",
            font=(FONT, 11, "bold"),
            relief="flat", bd=0,
            padx=22, pady=8,
            cursor="hand2",
            command=self._save,
        ).pack(side="right", pady=(4, 0))

    def _populate(self):
        self.v_title.set(self.existing.get("title", ""))
        self.w_desc.insert("1.0", self.existing.get("description", ""))
        self.v_script.set(self.existing.get("script_path", ""))
        self.v_image.set(self.existing.get("image_path", ""))

    # -----------------------------------------------------------------------
    # Widget helpers
    # -----------------------------------------------------------------------
    def _lbl(self, parent, text):
        tk.Label(parent, text=text, bg=BG, fg=TEXT_MUTED,
                 font=(FONT, 10, "bold"), anchor="w").pack(fill="x")

    def _entry(self, parent, var):
        return tk.Entry(
            parent, textvariable=var,
            font=(FONT, 11), relief="flat", bd=0,
            highlightthickness=1, highlightbackground=BORDER,
            bg="white", fg=TEXT, insertbackground=TEXT,
        )

    def _browse_row(self, parent, var, cmd):
        row = tk.Frame(parent, bg=BG)
        self._entry(row, var).pack(side="left", fill="x", expand=True)
        btn = tk.Button(
            row, text="Browse",
            bg=ACCENT, fg="white", relief="flat", bd=0,
            font=(FONT, 10), padx=12, pady=6,
            cursor="hand2", command=cmd,
        )
        btn.pack(side="right", padx=(8, 0))
        btn.bind("<Enter>", lambda _: btn.config(bg=ACCENT_H))
        btn.bind("<Leave>", lambda _: btn.config(bg=ACCENT))
        return row

    # -----------------------------------------------------------------------
    # Browse callbacks
    # -----------------------------------------------------------------------
    def _browse_script(self):
        path = filedialog.askopenfilename(
            initialdir=SCRIPT_DIR,
            title="Select Python script",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
        )
        if path:
            self.v_script.set(self._rel(path))

    def _browse_image(self):
        path = filedialog.askopenfilename(
            initialdir=SCRIPT_DIR,
            title="Select image",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.ico"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.v_image.set(self._rel(path))

    def _rel(self, abs_path: str) -> str:
        try:
            return os.path.relpath(abs_path, SCRIPT_DIR)
        except ValueError:
            return abs_path  # different drive on Windows — keep absolute

    # -----------------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------------
    def _save(self):
        title  = self.v_title.get().strip()
        script = self.v_script.get().strip()

        if not title:
            messagebox.showwarning("Missing field", "Please enter a title.", parent=self)
            return
        if not script:
            messagebox.showwarning("Missing field", "Please select a script.", parent=self)
            return
        if not (SCRIPT_DIR / script).exists():
            if not messagebox.askyesno(
                "Script not found",
                f"No file found at:\n  {script}\n\nSave anyway?",
                parent=self,
            ):
                return

        data = {
            "title":       title,
            "description": self.w_desc.get("1.0", "end-1c").strip(),
            "script_path": script,
            "image_path":  self.v_image.get().strip(),
        }
        if self.edit_mode:
            data["id"] = self.existing["id"]

        self.callback(data)
        self.destroy()


# ===========================================================================
# Entry point
# ===========================================================================
def main():
    root = tk.Tk()
    if platform.system() == "Darwin":
        root.tk.call("::tk::unsupported::MacWindowStyle", "style", root._w, "document", "closeBox")
    app = ToolLauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
