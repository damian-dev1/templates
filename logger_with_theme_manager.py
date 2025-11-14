import logging
import tkinter as tk
from tkinter import ttk, Menu, filedialog, messagebox
from datetime import datetime
import json
import os
CONFIG_FILE = "logger_config.json"
class ToolTip:
    """Minimal tooltip that follows theme colors."""
    def __init__(self, widget, get_palette, text, delay=400, wraplength=340, padx=10, pady=6):
        self.widget = widget
        self.get_palette = get_palette  # callable -> dict with colors
        self.text = text
        self.delay = delay
        self.wraplength = wraplength
        self.padx = padx
        self.pady = pady
        self._id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._cancel)
        widget.bind("<ButtonPress>", self._cancel)
    def _schedule(self, _=None):
        self._cancel()
        self._id = self.widget.after(self.delay, self._show)
    def _cancel(self, _=None):
        if self._id:
            self.widget.after_cancel(self._id)
            self._id = None
        self._hide()
    def _show(self):
        if self._tip or not self.text:
            return
        colors = self.get_palette()
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.attributes("-topmost", True)
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._tip.wm_geometry(f"+{x}+{y}")
        frame = tk.Frame(
            self._tip,
            bg=colors["tooltip_bg"],
            highlightbackground=colors["tooltip_border"],
            highlightcolor=colors["tooltip_border"],
            highlightthickness=1,
            bd=0,
        )
        frame.pack(fill="both", expand=True)
        lbl = tk.Label(
            frame,
            text=self.text,
            justify="left",
            wraplength=self.wraplength,
            bg=colors["tooltip_bg"],
            fg=colors["tooltip_fg"],
            padx=self.padx,
            pady=self.pady,
        )
        lbl.pack()
    def _hide(self):
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None
class ThemeManager:
    """Professional, reusable theme system with full widget coverage."""
    THEMES = {
        "light": {
            "name": "Light",
            "root_bg": "#ffffff",
            "fg": "#000000",
            "frame_bg": "#ffffff",
            "button_bg": "#f0f0f0",
            "button_fg": "#000000",
            "button_active_bg": "#e0e0e0",
            "entry_bg": "#ffffff",
            "tree_bg": "#ffffff",
            "tree_fg": "#000000",
            "tree_field_bg": "#ffffff",
            "tree_select_bg": "#0078d4",
            "tree_select_fg": "#ffffff",
            "status_bg": "#f3f3f3",
            "status_fg": "#000000",
            "tab_bg": "#f0f0f0",
            "tab_selected_bg": "#ffffff",
            "tab_fg": "#000000",
            "menu_bg": "#ffffff",
            "menu_fg": "#000000",
            "labelframe_bg": "#ffffff",
            "labelframe_fg": "#4a4a4a",
            "tooltip_bg": "#fffff7",
            "tooltip_fg": "#111111",
            "tooltip_border": "#d7d7d7",
        },
        "dark": {
            "name": "Dark",
            "root_bg": "#1e1e1e",
            "fg": "#e0e0e0",
            "frame_bg": "#1e1e1e",
            "button_bg": "#3a3a3a",
            "button_fg": "#ffffff",
            "button_active_bg": "#4a4a4a",
            "entry_bg": "#2d2d2d",
            "tree_bg": "#2d2d2d",
            "tree_fg": "#e0e0e0",
            "tree_field_bg": "#2d2d2d",
            "tree_select_bg": "#0078d4",
            "tree_select_fg": "#ffffff",
            "status_bg": "#252526",
            "status_fg": "#cccccc",
            "tab_bg": "#3a3a3a",
            "tab_selected_bg": "#2d2d2d",
            "tab_fg": "#ffffff",
            "menu_bg": "#2a2a2a",
            "menu_fg": "#e0e0e0",
            "labelframe_bg": "#1e1e1e",
            "labelframe_fg": "#b9b9b9",
            "tooltip_bg": "#2b2b2b",
            "tooltip_fg": "#f0f0f0",
            "tooltip_border": "#3d3d3d",
        }
    }
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style(root)
        self.current = "light"
        self._setup_base_styles()
    def _setup_base_styles(self):
        self.style.theme_use('default')
    def apply(self, theme_name):
        if theme_name not in self.THEMES:
            theme_name = "light"
        self.current = theme_name
        t = self.THEMES[theme_name]
        self.root.configure(bg=t["root_bg"])
        self.style.configure(".", background=t["frame_bg"], foreground=t["fg"])
        self.style.configure("TFrame", background=t["frame_bg"])
        self.style.configure("TLabel", background=t["frame_bg"], foreground=t["fg"])
        self.style.configure("TLabelframe", background=t["labelframe_bg"], borderwidth=1)
        self.style.configure("TLabelframe.Label", background=t["labelframe_bg"], foreground=t["labelframe_fg"])
        self.style.configure("TButton",
                             background=t["button_bg"],
                             foreground=t["button_fg"],
                             borderwidth=1,
                             focuscolor=t["button_bg"])
        self.style.map("TButton",
                       background=[("active", t["button_active_bg"]), ("pressed", t["button_active_bg"])],
                       foreground=[("active", t["button_fg"])])
        self.style.configure("TEntry", fieldbackground=t["entry_bg"], foreground=t["fg"])
        self.style.configure("TCombobox", fieldbackground=t["entry_bg"], foreground=t["fg"], background=t["entry_bg"])
        self.style.configure("TComboboxPopdownFrame", background=t["frame_bg"])
        self.style.configure("Treeview",
                             background=t["tree_bg"],
                             foreground=t["tree_fg"],
                             fieldbackground=t["tree_field_bg"],
                             rowheight=22,
                             borderwidth=1)
        self.style.map("Treeview",
                       background=[("selected", t["tree_select_bg"])],
                       foreground=[("selected", t["tree_select_fg"])])
        self.style.configure("TNotebook", background=t["frame_bg"])
        self.style.configure("TNotebook.Tab", background=t["tab_bg"], foreground=t["tab_fg"], padding=[12, 6])
        self.style.map("TNotebook.Tab",
                       background=[("selected", t["tab_selected_bg"])],
                       foreground=[("selected", t["fg"])])
        self.style.configure("Status.TLabel",
                             background=t["status_bg"],
                             foreground=t["status_fg"],
                             padding=6,
                             font=("Segoe UI", 9))
        self.root.update_idletasks()
        self.style.configure(
            "TCombobox",
            fieldbackground=t["entry_bg"],
            foreground=t["fg"],
            background=t["entry_bg"],
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", t["entry_bg"]), ("!readonly", t["entry_bg"])],
            foreground=[("readonly", t["fg"]), ("!readonly", t["fg"])],
            background=[("readonly", t["entry_bg"]), ("!readonly", t["entry_bg"])],
        )
        self.root.option_add("*TCombobox*Listbox.background", t["entry_bg"])
        self.root.option_add("*TCombobox*Listbox.foreground", t["fg"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", t["tree_select_bg"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", t["tree_select_fg"])
        self.root.option_add("*TCombobox*Listbox.highlightThickness", 0)
    def get(self, key):
        return self.THEMES[self.current].get(key)
    def palette(self):
        """Expose current theme colors to others (e.g., ToolTip)."""
        return self.THEMES[self.current]
class TTKLogger(logging.Handler):
    def __init__(self, treeview: ttk.Treeview, level=logging.INFO, autoscroll=True, on_emit=None):
        super().__init__(level)
        self.treeview = treeview
        self.autoscroll = autoscroll
        self.on_emit = on_emit
        self._setup_treeview()
        self._setup_tags()
    def _setup_treeview(self):
        self.treeview["columns"] = ("time", "level", "message")
        self.treeview.heading("#0", text="")
        self.treeview.column("#0", width=0, stretch=False)
        self.treeview.heading("time", text="Time", anchor="w")
        self.treeview.column("time", width=170, anchor="w")
        self.treeview.heading("level", text="Level", anchor="w")
        self.treeview.column("level", width=90, anchor="w")
        self.treeview.heading("message", text="Message", anchor="w")
        self.treeview.column("message", width=600, anchor="w")
    def _setup_tags(self):
        self.treeview.tag_configure("INFO", foreground="#00c853")
        self.treeview.tag_configure("WARNING", foreground="#ffb300")
        self.treeview.tag_configure("ERROR", foreground="#ff5252")
        self.treeview.tag_configure("DEBUG", foreground="#9e9e9e")
    def emit(self, record):
        try:
            msg = self.format(record)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            iid = self.treeview.insert("", "end", values=(ts, record.levelname, msg), tags=(record.levelname,))
            if self.autoscroll:
                self.treeview.yview_moveto(1.0)
            if self.on_emit:
                self.on_emit(iid, {"time": ts, "level": record.levelname, "message": msg})
        except Exception:
            self.handleError(record)
class LoggerApp(tk.Tk):
    PADX = 12
    PADY = 8
    def __init__(self):
        super().__init__()
        self.title("TTK Logger — Professional Theme & UI")
        self.geometry("960x620")
        self.minsize(800, 500)
        self.all_items = {}
        self.detached_items = set()
        self.theme = ThemeManager(self)
        main = ttk.Frame(self, padding=0)
        main.pack(fill="both", expand=True)
        top_bar = ttk.Frame(main)
        top_bar.pack(fill="x", padx=self.PADX, pady=(self.PADY, self.PADY // 2))
        search_frame = ttk.Frame(top_bar)
        search_frame.pack(side="left")
        ttk.Label(search_frame, text="Search:", font=("Segoe UI", 10)).pack(side="left")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(search_frame, textvariable=self.search_var, width=38, font=("Segoe UI", 10))
        entry.pack(side="left", padx=(6, 4))
        entry.bind("<KeyRelease>", lambda e: self._apply_filter())
        ttk.Button(search_frame, text="Go", width=5, command=self._apply_filter).pack(side="left", padx=2)
        ttk.Button(search_frame, text="Clear", width=6, command=self._reset_filter).pack(side="left", padx=2)
        btn_frame = ttk.Frame(top_bar)
        btn_frame.pack(side="right")
        for text, cmd in [
            ("Info", lambda: self.logger.info("Info message")),
            ("Warn", lambda: self.logger.warning("Warning message")),
            ("Error", lambda: self.logger.error("Error message")),
            ("Debug", lambda: self.logger.debug("Debug details")),
            ("Clear", self._clear_logs)
        ]:
            b = ttk.Button(btn_frame, text=text, width=7, command=cmd)
            b.pack(side="left", padx=2)
        content = ttk.Frame(main)
        content.pack(fill="both", expand=True, padx=self.PADX, pady=(self.PADY // 2, self.PADY))
        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill="both", expand=True)
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text=" Logs ")
        tree_container = ttk.Frame(log_frame)
        tree_container.pack(fill="both", expand=True, padx=4, pady=4)
        self.tree = ttk.Treeview(tree_container, style="Treeview")
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main, textvariable=self.status_var, style="Status.TLabel", anchor="w")
        self.status_label.pack(fill="x", side="bottom")
        self.menu = Menu(self, tearoff=0)
        self._restyle_context_menu()
        self.menu.add_command(label="Copy Message", command=self._copy_message)
        self.menu.add_command(label="Copy Full Row", command=self._copy_row)
        self.tree.bind("<Button-3>", self._show_context_menu)
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text=" Settings ")
        self._setup_settings(settings_frame)
        self.logger = logging.getLogger("TTKLogger")
        self.logger.setLevel(logging.DEBUG)
        self.handler = TTKLogger(self.tree, on_emit=self._on_emit_record)
        self.handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(self.handler)
        self.file_handler = logging.FileHandler("app.log", mode="a")
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(self.file_handler)
        self._load_settings()
        self._set_status("Logger initialized")
    def _restyle_context_menu(self):
        t = self.theme.palette()
        try:
            self.menu.configure(bg=t["menu_bg"], fg=t["menu_fg"],
                                activebackground=t["button_active_bg"],
                                activeforeground=t["button_fg"],
                                tearoff=0)
        except Exception:
            pass
    def _show_context_menu(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self.menu.tk_popup(event.x_root, event.y_root)
    def _copy_message(self):
        sel = self.tree.selection()
        if sel:
            msg = self.tree.item(sel[0], "values")[2]
            self.clipboard_clear(); self.clipboard_append(msg)
            self._set_status("Message copied")
    def _copy_row(self):
        sel = self.tree.selection()
        if sel:
            v = self.tree.item(sel[0], "values")
            row = f"{v[0]} [{v[1]}] {v[2]}"
            self.clipboard_clear(); self.clipboard_append(row)
            self._set_status("Row copied")
    def _setup_settings(self, parent):
        outer = ttk.Frame(parent, padding=(16, 16))
        outer.pack(fill="both", expand=True)
        grp_log = ttk.LabelFrame(outer, text="Logging", padding=(12, 10))
        grp_log.pack(fill="x", expand=False, pady=(0, 12))
        self._build_logging_group(grp_log)
        grp_files = ttk.LabelFrame(outer, text="Files", padding=(12, 10))
        grp_files.pack(fill="x", expand=False, pady=(0, 12))
        self._build_files_group(grp_files)
        grp_theme = ttk.LabelFrame(outer, text="Appearance", padding=(12, 10))
        grp_theme.pack(fill="x", expand=False, pady=(0, 12))
        self._build_appearance_group(grp_theme)
        footer = ttk.Frame(outer)
        footer.pack(fill="x", expand=False, pady=(4, 0))
        footer.columnconfigure(0, weight=1)
        btns = ttk.Frame(footer)
        btns.grid(row=0, column=1, sticky="e")
        ttk.Button(btns, text="Save Settings", command=self._save_settings).pack(side="right", padx=(8, 0))
        ttk.Button(btns, text="Reset Filter", command=self._reset_filter).pack(side="right")
    def _build_logging_group(self, frame):
        f = frame
        for col, w in [(0, 0), (1, 1), (2, 0), (3, 0)]:  # label, control(expand), apply, help
            f.columnconfigure(col, weight=w)
        r = 0
        lbl = ttk.Label(f, text="Log Level:", font=("Segoe UI", 10, "bold"))
        lbl.grid(row=r, column=0, sticky="w", pady=(0, 8))
        self.level_var = tk.StringVar(value="DEBUG")
        self.level_combo = ttk.Combobox(f, textvariable=self.level_var, state="readonly",
                                        values=("DEBUG", "INFO", "WARNING", "ERROR"), width=16)
        self.level_combo.grid(row=r, column=1, sticky="w", padx=(10, 0), pady=(0, 8))
        ttk.Button(f, text="Apply", command=lambda: self._change_log_level(self.level_var.get())).grid(row=r, column=2, sticky="e", padx=(8, 0), pady=(0, 8))
        help_btn = ttk.Button(f, text="?", width=2)
        help_btn.grid(row=r, column=3, sticky="e", pady=(0, 8))
        ToolTip(help_btn, self.theme.palette,
                "Controls the minimum severity shown and written to file.\n"
                "DEBUG: all messages; INFO: routine info; WARNING: potential issues; ERROR: failures.")
        r += 1
        self.autoscroll_var = tk.BooleanVar(value=True)
        autoscroll_cb = ttk.Checkbutton(f, text="Auto-scroll to new logs", variable=self.autoscroll_var, command=self._toggle_autoscroll)
        autoscroll_cb.grid(row=r, column=0, columnspan=3, sticky="w", pady=(0, 4))
        help_btn2 = ttk.Button(f, text="?", width=2)
        help_btn2.grid(row=r, column=3, sticky="e", pady=(0, 4))
        ToolTip(help_btn2, self.theme.palette,
                "When enabled, the view jumps to the newest log entry automatically.")
    def _build_files_group(self, frame):
        f = frame
        for col, w in [(0, 0), (1, 1), (2, 0), (3, 0)]:
            f.columnconfigure(col, weight=w)
        r = 0
        ttk.Label(f, text="Log File:", font=("Segoe UI", 10, "bold")).grid(row=r, column=0, sticky="w", pady=(0, 8))
        self.file_path_var = tk.StringVar(value="app.log")
        path_entry = ttk.Entry(f, textvariable=self.file_path_var)
        path_entry.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=(0, 8))
        ttk.Button(f, text="Browse…", command=self._choose_file).grid(row=r, column=2, sticky="e", padx=(8, 0), pady=(0, 8))
        help_btn = ttk.Button(f, text="?", width=2)
        help_btn.grid(row=r, column=3, sticky="e", pady=(0, 8))
        ToolTip(help_btn, self.theme.palette,
                "Choose where logs are persisted. Rotating/archiving can be done externally or added later.")
    def _build_appearance_group(self, frame):
        f = frame
        for col, w in [(0, 0), (1, 1), (2, 0), (3, 0)]:
            f.columnconfigure(col, weight=w)
        r = 0
        ttk.Label(f, text="Theme:", font=("Segoe UI", 10, "bold")).grid(row=r, column=0, sticky="w", pady=(0, 8))
        self.theme_var = tk.StringVar(value="light")
        self.theme_combo = ttk.Combobox(f, textvariable=self.theme_var, state="readonly", values=("light", "dark"), width=16)
        self.theme_combo.grid(row=r, column=1, sticky="w", padx=(10, 0), pady=(0, 8))
        ttk.Button(f, text="Apply", command=lambda: self._change_theme(self.theme_var.get())).grid(row=r, column=2, sticky="e", padx=(8, 0), pady=(0, 8))
        help_btn = ttk.Button(f, text="?", width=2)
        help_btn.grid(row=r, column=3, sticky="e", pady=(0, 8))
        ToolTip(help_btn, self.theme.palette,
                "Switch between light and dark palettes. Context menus and tooltips theme automatically.")
    def _change_log_level(self, level):
        lvl = getattr(logging, level)
        self.logger.setLevel(lvl)
        self.handler.setLevel(lvl)
        self.file_handler.setLevel(lvl)
        self._set_status(f"Level → {level}")
    def _toggle_autoscroll(self):
        self.handler.autoscroll = self.autoscroll_var.get()
        self._set_status(f"Autoscroll → {self.handler.autoscroll}")
    def _choose_file(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("All files", "*.*")],
            initialfile=os.path.basename(self.file_path_var.get())
        )
        if path:
            self._set_file_handler_path(path)
            self.file_path_var.set(path)
            self._set_status(f"File → {os.path.basename(path)}")
    def _set_file_handler_path(self, path):
        try:
            self.logger.removeHandler(self.file_handler)
        except Exception:
            pass
        self.file_handler = logging.FileHandler(path, mode="a")
        self.file_handler.setLevel(self.logger.level)
        self.file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(self.file_handler)
    def _change_theme(self, theme):
        self.theme.apply(theme)
        self._restyle_context_menu()
        self._set_status(f"Theme → {self.theme.THEMES[theme]['name']}")
    def _load_settings(self):
        defaults = {"level": "DEBUG", "autoscroll": True, "file_path": "app.log", "theme": "light"}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                defaults.update({k: data.get(k, v) for k, v in defaults.items()})
            except Exception as e:
                messagebox.showwarning("Settings", f"Failed to load: {e}")
        self.level_var.set(defaults["level"])
        self.autoscroll_var.set(defaults["autoscroll"])
        self.file_path_var.set(defaults["file_path"])
        self.theme_var.set(defaults["theme"])
        self._change_log_level(defaults["level"])
        self.handler.autoscroll = defaults["autoscroll"]
        self._set_file_handler_path(defaults["file_path"])
        self.theme.apply(defaults["theme"])
        self._restyle_context_menu()
    def _save_settings(self):
        data = {
            "level": self.level_var.get(),
            "autoscroll": self.autoscroll_var.get(),
            "file_path": self.file_path_var.get(),
            "theme": self.theme_var.get(),
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self._set_status("Settings saved")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")
    def _on_emit_record(self, iid, rec):
        self.all_items[iid] = rec
        self._apply_filter()
    def _match_filter(self, rec):
        q = self.search_var.get().strip().lower()
        if not q:
            return True
        return q in f"{rec['time']} {rec['level']} {rec['message']}".lower()
    def _apply_filter(self):
        for iid, rec in self.all_items.items():
            match = self._match_filter(rec)
            parent = self.tree.parent(iid)
            if match and iid in self.detached_items:
                self.tree.reattach(iid, "", "end")
                self.detached_items.remove(iid)
            elif not match and parent != "":
                self.tree.detach(iid)
                self.detached_items.add(iid)
        if self.handler.autoscroll:
            self.tree.yview_moveto(1.0)
    def _reset_filter(self):
        self.search_var.set("")
        for iid in list(self.detached_items):
            self.tree.reattach(iid, "", "end")
        self.detached_items.clear()
        self._set_status("Filter cleared")
    def _clear_logs(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.all_items.clear()
        self.detached_items.clear()
        self._set_status("Logs cleared")
    def _set_status(self, text):
        self.status_var.set(text)
        self.update_idletasks()
if __name__ == "__main__":
    app = LoggerApp()
    app.mainloop()
