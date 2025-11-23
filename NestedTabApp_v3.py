import sys
import os
import datetime
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

import ttkbootstrap as tb
from tkinter import ttk
from ttkbootstrap.constants import *

# Optional data libs
APP_DATA = {
    "dataframe": None,
    "filename": None,
    "rows": 0,
    "cols": 0,
}

HAS_PANDAS = False
HAS_MATPLOTLIB = False

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    pd = None
    np = None

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except ImportError:
    plt = None
    FigureCanvasTkAgg = None

# Colors for toasts / highlight
HIGHLIGHT_COLOR = "#f39c12"
TOAST_ACCENT = "#375a7f"
TOAST_SUCCESS = "#00bc8c"


# ---------------------------------------------------------------------------
# Utility widgets: ToolTip & Toast
# ---------------------------------------------------------------------------

class ToolTip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return

        bbox = self.widget.bbox("insert")
        if bbox is None:
            x = self.widget.winfo_rootx() + 25
            y = self.widget.winfo_rooty() + 25
        else:
            x, y, _, _ = bbox
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 25

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        tk.Label(
            tw,
            text=self.text,
            justify="left",
            bg="#ffffe0",
            fg="#000000",
            relief="solid",
            bd=1,
            font=("tahoma", 8),
        ).pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window is not None:
            self.tip_window.destroy()
            self.tip_window = None


class ToastNotification:
    def __init__(self, master, title, message, duration=3000, bg=TOAST_ACCENT):
        self.window = tk.Toplevel(master)
        self.window.wm_overrideredirect(True)
        frame = tk.Frame(self.window, bg=bg, bd=2, relief="raised")
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text=title,
            font=("Segoe UI", 10, "bold"),
            bg=bg,
            fg="white",
            anchor="w",
        ).pack(fill="x", padx=10, pady=(5, 0))

        tk.Label(
            frame,
            text=message,
            font=("Segoe UI", 9),
            bg=bg,
            fg="white",
            anchor="w",
        ).pack(fill="x", padx=10, pady=5)

        self.window.update_idletasks()
        width, height = 260, 70
        x = master.winfo_rootx() + master.winfo_width() - width - 20
        y = master.winfo_rooty() + master.winfo_height() - height - 40
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        self.window.after(duration, self.window.destroy)


# ---------------------------------------------------------------------------
# Data module helpers (import/export) with threaded loading
# ---------------------------------------------------------------------------

def _show_loader(root, filename: str):
    """Small modal window with indeterminate progress bar."""
    win = tb.Toplevel(root)
    win.title("Loading dataset...")
    win.resizable(False, False)
    win.transient(root)
    win.grab_set()

    frm = ttk.Frame(win, padding=15)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text=f"Loading: {os.path.basename(filename)}").pack(
        anchor="w", pady=(0, 8)
    )
    pb = ttk.Progressbar(frm, mode="indeterminate", bootstyle=INFO)
    pb.pack(fill="x")
    pb.start(10)

    win.update_idletasks()
    w, h = 320, 100
    x = root.winfo_rootx() + (root.winfo_width() - w) // 2
    y = root.winfo_rooty() + (root.winfo_height() - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")
    return win, pb


def load_file(parent_frame):
    if not HAS_PANDAS:
        messagebox.showerror(
            "Missing Library",
            "Please install pandas:\n\npip install pandas openpyxl",
        )
        return

    root = parent_frame.winfo_toplevel()
    file_path = filedialog.askopenfilename(
        filetypes=[
            ("Data Files", "*.csv *.xlsx *.json"),
            ("All Files", "*.*"),
        ]
    )
    if not file_path:
        return

    loader_win, _ = _show_loader(root, file_path)

    def worker():
        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_path.endswith(".xlsx"):
                df = pd.read_excel(file_path)
            elif file_path.endswith(".json"):
                df = pd.read_json(file_path)
            else:
                raise ValueError("Unsupported file format")

            rows, cols = df.shape

        except Exception as e:
            def on_error():
                loader_win.destroy()
                messagebox.showerror("Import Error", f"Failed to read file:\n{e}")
            root.after(0, on_error)
            return

        def on_success():
            loader_win.destroy()
            APP_DATA["dataframe"] = df
            APP_DATA["filename"] = os.path.basename(file_path)
            APP_DATA["rows"] = rows
            APP_DATA["cols"] = cols

            if hasattr(root, "switch_page"):
                root.switch_page("Data")
                if hasattr(root, "notebook"):
                    root.notebook.select(1)  # Explore tab

            if hasattr(root, "show_toast"):
                root.show_toast(
                    "Import Successful",
                    f"Loaded {rows} rows × {cols} columns.",
                    bg=TOAST_SUCCESS,
                )

        root.after(0, on_success)

    threading.Thread(target=worker, daemon=True).start()


def save_file(parent_frame, fmt: str):
    if APP_DATA["dataframe"] is None:
        messagebox.showwarning("No Data", "No data loaded to export.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=f".{fmt}",
        filetypes=[(f"{fmt.upper()} File", f"*.{fmt}")],
    )
    if not file_path:
        return

    try:
        df = APP_DATA["dataframe"]
        if fmt == "csv":
            df.to_csv(file_path, index=False)
        elif fmt == "xlsx":
            df.to_excel(file_path, index=False)
        elif fmt == "json":
            df.to_json(file_path, orient="records")

        root = parent_frame.winfo_toplevel()
        if hasattr(root, "show_toast"):
            root.show_toast("Export Successful", "File saved.", bg=TOAST_SUCCESS)

    except Exception as e:
        messagebox.showerror("Export Error", str(e))


# ---------------------------------------------------------------------------
# Overview / Data / Settings modules
# ---------------------------------------------------------------------------

class OverviewModule:
    HAS_ACTION = True
    TABS = ["Welcome", "Release Notes", "Shortcuts"]

    @staticmethod
    def get_content(tab_name: str) -> str:
        if tab_name == "Welcome":
            return """
            This is the central hub for your application.
            Use the sidebar to navigate between different modules.
            Current Version: 1.0.2 (Std Lib Edition)
            """
        elif tab_name == "Release Notes":
            return """
            - v1.0.2: Separated logic into modules.
            - v1.0.1: Added Dark Theme support.
            - v1.0.0: Initial Release.
            """
        elif tab_name == "Shortcuts":
            return """
            [Ctrl + N] : New Project
            [Ctrl + O] : Open Project
            [Ctrl + F] : Focus Search Bar
            """
        return "Content not found."

    @staticmethod
    def perform_module_action(tab_name: str) -> str:
        return f"Overview module processed action for: {tab_name}"


class DataModule:
    HAS_ACTION = False
    TABS = ["Import", "Explore", "Visualize", "Export"]

    @staticmethod
    def render_tab(parent, tab_name: str):
        if tab_name == "Import":
            container = ttk.Frame(parent)
            center = ttk.Frame(container)
            center.pack(expand=True)

            ttk.Label(center, text="📂", font=("Segoe UI", 48)).pack(pady=(0, 20))
            ttk.Label(center, text="Import Dataset", font=("Segoe UI", 14, "bold")).pack()
            ttk.Label(center, text="CSV, Excel, JSON").pack(pady=(5, 20))

            ttk.Button(
                center,
                text="Browse Files...",
                command=lambda: load_file(container),
                bootstyle=PRIMARY,
            ).pack(ipadx=20, ipady=5)

            if APP_DATA["filename"]:
                ttk.Label(
                    center,
                    text=f"Loaded: {APP_DATA['filename']}",
                    bootstyle=SUCCESS,
                ).pack(pady=20)

            return container

        elif tab_name == "Explore":
            container = ttk.Frame(parent)
            df = APP_DATA["dataframe"]
            if df is None:
                ttk.Label(container, text="No Data Loaded", font=("Segoe UI", 16)).pack(
                    pady=20
                )
                return container

            # Stats panel
            stats_frame = ttk.Frame(container)
            stats_frame.pack(fill="x", pady=(0, 10))

            rows = APP_DATA["rows"]
            cols = APP_DATA["cols"]
            numeric_cols = len(df.select_dtypes(include=[np.number]).columns) if HAS_PANDAS else "n/a"
            non_numeric_cols = cols - numeric_cols if isinstance(numeric_cols, int) else "n/a"
            missing_vals = int(df.isna().sum().sum()) if HAS_PANDAS else "n/a"
            mem_bytes = int(df.memory_usage(deep=True).sum()) if HAS_PANDAS else 0
            mem_mb = mem_bytes / (1024 * 1024) if mem_bytes else 0

            stats_text = (
                f"Rows: {rows} | Columns: {cols} | "
                f"Numeric: {numeric_cols} | Non-numeric: {non_numeric_cols} | "
                f"Missing values: {missing_vals} | Memory: {mem_mb:.2f} MB"
            )
            ttk.Label(stats_frame, text=stats_text, bootstyle=INFO).pack(anchor="w")

            info = ttk.Frame(container)
            info.pack(fill="x", pady=(5, 10))
            ttk.Label(
                info,
                text=f"File: {APP_DATA['filename']}",
                font=("Segoe UI", 10, "bold"),
            ).pack(side="left")

            tree_frame = ttk.Frame(container)
            tree_frame.pack(fill="both", expand=True)

            scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
            scroll_y.pack(side="right", fill="y")
            scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
            scroll_x.pack(side="bottom", fill="x")

            cols_list = list(df.columns)
            tree = ttk.Treeview(
                tree_frame,
                columns=cols_list,
                show="headings",
                yscrollcommand=scroll_y.set,
                xscrollcommand=scroll_x.set,
            )
            scroll_y.config(command=tree.yview)
            scroll_x.config(command=tree.xview)

            for col in cols_list:
                tree.heading(col, text=col)
                tree.column(col, width=120, minwidth=60)

            for row in df.head(500).to_numpy().tolist():
                tree.insert("", "end", values=[str(v) for v in row])

            tree.pack(side="left", fill="both", expand=True)
            return container

        elif tab_name == "Visualize":
            container = ttk.Frame(parent)

            if APP_DATA["dataframe"] is None:
                ttk.Label(container, text="Load data to visualize.", font=("Segoe UI", 12)).pack(
                    pady=20
                )
                return container

            if not HAS_MATPLOTLIB:
                ttk.Label(
                    container,
                    text="Matplotlib not installed.\nRun: pip install matplotlib",
                    bootstyle=DANGER,
                ).pack(pady=20)
                return container

            df = APP_DATA["dataframe"]
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_cols:
                ttk.Label(
                    container,
                    text="No numeric columns found to plot.",
                    bootstyle=WARNING,
                ).pack(pady=20)
                return container

            controls = ttk.Frame(container)
            controls.pack(fill="x", pady=10)

            # Column dropdown
            ttk.Label(controls, text="Column: ").pack(side="left")
            col_var = tk.StringVar(value=numeric_cols[0])
            col_menu = ttk.OptionMenu(controls, col_var, numeric_cols[0], *numeric_cols)
            col_menu.pack(side="left")

            # Plot type dropdown
            ttk.Label(controls, text="  Plot type: ").pack(side="left", padx=(10, 0))
            plot_types = ["Histogram", "Value Counts (Bar)", "Box Plot", "Line (head)"]
            plot_type_var = tk.StringVar(value=plot_types[0])
            plot_type_menu = ttk.OptionMenu(
                controls, plot_type_var, plot_types[0], *plot_types
            )
            plot_type_menu.pack(side="left")

            # Histogram bins
            ttk.Label(controls, text="  Bins: ").pack(side="left", padx=(10, 0))
            bins_var = tk.IntVar(value=20)
            bins_spin = ttk.Spinbox(
                controls, from_=5, to=100, textvariable=bins_var, width=5
            )
            bins_spin.pack(side="left")

            plot_frame = ttk.Frame(container)
            plot_frame.pack(fill="both", expand=True)

            def generate_plot(*args):
                for widget in plot_frame.winfo_children():
                    widget.destroy()

                col_name = col_var.get()
                plot_type = plot_type_var.get()
                series = df[col_name].dropna()

                fig, ax = plt.subplots(figsize=(5, 4), dpi=100)

                if plot_type == "Histogram":
                    bins = max(5, int(bins_var.get()))
                    series.plot(
                        kind="hist",
                        bins=bins,
                        ax=ax,
                        edgecolor="white",
                    )
                    ax.set_title(f"Histogram of {col_name}")

                elif plot_type == "Value Counts (Bar)":
                    vc = series.value_counts().sort_index()
                    vc.plot(kind="bar", ax=ax)
                    ax.set_title(f"Value counts of {col_name}")

                elif plot_type == "Box Plot":
                    ax.boxplot(series.dropna(), vert=True)
                    ax.set_title(f"Box plot of {col_name}")
                    ax.set_xticklabels([col_name])

                elif plot_type == "Line (head)":
                    series.head(200).plot(kind="line", ax=ax)
                    ax.set_title(f"Line plot (first 200) of {col_name}")

                ax.set_xlabel(col_name)

                canvas = FigureCanvasTkAgg(fig, master=plot_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)

            ttk.Button(
                controls,
                text="Plot",
                command=generate_plot,
                bootstyle=PRIMARY,
            ).pack(side="left", padx=10)

            generate_plot()
            return container

        elif tab_name == "Export":
            container = ttk.Frame(parent)
            if APP_DATA["dataframe"] is None:
                ttk.Label(container, text="No data available.", font=("Segoe UI", 12)).pack(
                    pady=20
                )
                return container

            ttk.Label(
                container,
                text="Export Data",
                font=("Segoe UI", 14, "bold"),
            ).pack(anchor="w", pady=(0, 20))

            btn_frame = ttk.Frame(container)
            btn_frame.pack(fill="x", pady=10)

            for fmt, style in [("xlsx", PRIMARY), ("csv", SECONDARY), ("json", INFO)]:
                ttk.Button(
                    btn_frame,
                    text=f"Export to {fmt.upper()}",
                    command=lambda f=fmt: save_file(container, f),
                    bootstyle=style,
                ).pack(anchor="w", pady=5)

            return container

        return None

    @staticmethod
    def get_content(tab_name: str) -> str:
        return ""

    @staticmethod
    def perform_module_action(tab_name: str) -> str:
        if APP_DATA["dataframe"] is not None:
            return f"Processed {APP_DATA['rows']} rows."
        return "No data."


class SettingsModule:
    HAS_ACTION = True
    TABS = ["Appearance", "Preferences", "About"]

    @staticmethod
    def render_tab(parent, tab_name: str):
        if tab_name == "Preferences":
            container = ttk.Frame(parent)

            form = ttk.Frame(container)
            form.pack(fill="x", pady=10)

            var1 = tk.BooleanVar(value=True)
            var2 = tk.BooleanVar(value=False)

            ttk.Label(
                form, text="General Options", font=("Segoe UI", 11, "bold")
            ).pack(anchor="w", pady=(0, 5))
            ttk.Checkbutton(
                form, text="Enable Auto-Save on Exit", variable=var1
            ).pack(anchor="w", pady=2)
            ttk.Checkbutton(
                form, text="Show Tips on Startup", variable=var2
            ).pack(anchor="w", pady=2)
            ttk.Checkbutton(
                form, text="Send Anonymous Usage Statistics"
            ).pack(anchor="w", pady=2)

            ttk.Separator(form, orient="horizontal").pack(fill="x", pady=15)

            ttk.Label(
                form, text="Account Settings", font=("Segoe UI", 11, "bold")
            ).pack(anchor="w", pady=(0, 5))

            f1 = ttk.Frame(form)
            f1.pack(fill="x", pady=2)
            ttk.Label(f1, text="Username:", width=15).pack(side="left")
            ttk.Entry(f1).pack(side="left", fill="x", expand=True)

            f2 = ttk.Frame(form)
            f2.pack(fill="x", pady=2)
            ttk.Label(f2, text="API Key:", width=15).pack(side="left")
            ttk.Entry(f2, show="*").pack(side="left", fill="x", expand=True)

            btn_frame = ttk.Frame(container)
            btn_frame.pack(fill="x", pady=20)
            ttk.Button(
                btn_frame, text="Save Preferences", bootstyle=SUCCESS
            ).pack(side="right")

            return container

        # Appearance / About fall back to text content
        return None

    @staticmethod
    def get_content(tab_name: str) -> str:
        if tab_name == "Appearance":
            return "Settings for Theme and Fonts."
        elif tab_name == "About":
            return "Version 2.0 - Interactive Module Edition."
        return ""

    @staticmethod
    def perform_module_action(tab_name: str) -> str:
        return f"Settings Saved: {tab_name}"


MODULE_REGISTRY = {
    "Overview": OverviewModule,
    "Data": DataModule,
    "Settings": SettingsModule,
}


# ---------------------------------------------------------------------------
# Main App (ttkbootstrap.Window, darkly theme)
# ---------------------------------------------------------------------------

class NestedTabApp(tb.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Modular GUI - ttkbootstrap Edition")
        self.geometry("1000x600")
        self.minsize(800, 500)

        self.app_state = tk.StringVar(value="Status: Ready")
        self.clock_var = tk.StringVar()
        self.current_page = None
        self.text_widgets = []
        self.search_entry = None

        self._build_menu()
        self._build_header()
        self._build_main_layout()
        self._build_statusbar()
        self._bind_shortcuts()
        self._start_clock()

        first_page = next(iter(MODULE_REGISTRY))
        self.switch_page(first_page)

    # ---------------- Layout ----------------

    def _build_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="New Project", command=self.new_project, accelerator="Ctrl+N"
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

    def _build_header(self):
        header = ttk.Frame(self, padding=10)
        header.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            header,
            text="MODULAR APP",
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        search_frame = ttk.Frame(header)
        search_frame.pack(side="right")

        self.search_entry = ttk.Entry(search_frame, width=25)
        self.search_entry.pack(side="left", padx=5)
        ToolTip(self.search_entry, "Search across modules & tabs")

        ttk.Button(
            search_frame,
            text="🔍",
            width=3,
            command=self.perform_search,
            bootstyle=PRIMARY,
        ).pack(side="left")
        ttk.Button(
            search_frame,
            text="✕",
            width=3,
            command=self.clear_search,
            bootstyle=SECONDARY,
        ).pack(side="left")

    def _build_main_layout(self):
        container = ttk.Frame(self)
        container.grid(row=1, column=0, sticky="nsew")

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        # Sidebar (left)
        sidebar = ttk.Frame(container, padding=(5, 10))
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)
        sidebar.configure(width=180)

        ttk.Label(
            sidebar,
            text=" MODULES",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 5))

        for name in MODULE_REGISTRY.keys():
            ttk.Button(
                sidebar,
                text=f"  {name}",
                bootstyle=SECONDARY,
                command=lambda p=name: self.switch_page(p),
            ).pack(fill="x", pady=2, padx=5)

        # Content (right)
        content = ttk.Frame(container, padding=10)
        content.grid(row=0, column=1, sticky="nsew")

        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill="both", expand=True)

    def _build_statusbar(self):
        bar = ttk.Frame(self)
        bar.grid(row=2, column=0, sticky="ew")

        ttk.Label(
            bar,
            textvariable=self.app_state,
            font=("Consolas", 9),
        ).pack(side="left", padx=10, pady=2)

        ttk.Label(
            bar,
            textvariable=self.clock_var,
            font=("Consolas", 9),
        ).pack(side="right", padx=10, pady=2)

    # ---------------- Tabs / Modules ----------------

    def create_tab_content(self, module_obj, page_name: str, tab_name: str):
        frame = ttk.Frame(self.notebook, padding=15)

        ttk.Label(
            frame,
            text=f"{page_name} / {tab_name}",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        custom = None
        if hasattr(module_obj, "render_tab"):
            try:
                custom = module_obj.render_tab(frame, tab_name)
            except Exception as e:
                print(f"Error rendering {page_name}::{tab_name}: {e}", file=sys.stderr)

        if custom is not None:
            custom.pack(fill="both", expand=True)
        else:
            st = ScrolledText(frame, wrap="word", font=("Segoe UI", 10), height=14)
            st.pack(fill="both", expand=True)
            self.text_widgets.append(st)
            try:
                content = module_obj.get_content(tab_name)
            except AttributeError:
                content = "Content unavailable."
            st.insert("1.0", content.strip())
            st.config(state="disabled")

        # Only Overview & Settings get a Run Action
        if getattr(module_obj, "HAS_ACTION", False):
            footer = ttk.Frame(frame)
            footer.pack(fill="x", pady=(10, 0))

            def run_action():
                try:
                    msg = module_obj.perform_module_action(tab_name)
                    self.show_toast("Action", msg, bg=TOAST_SUCCESS)
                except AttributeError:
                    pass

            ttk.Button(
                footer,
                text="Run Action",
                bootstyle=SUCCESS,
                command=run_action,
            ).pack(side="left")

        return frame

    def switch_page(self, page_name: str):
        if self.current_page == page_name:
            return

        self.current_page = page_name
        self.app_state.set(f"Status: Opened {page_name}")
        self.text_widgets.clear()

        for tab in self.notebook.tabs():
            self.notebook.forget(tab)

        module = MODULE_REGISTRY.get(page_name)
        if module and hasattr(module, "TABS"):
            for tab_name in module.TABS:
                tab = self.create_tab_content(module, page_name, tab_name)
                self.notebook.add(tab, text=tab_name)
        else:
            self.show_toast("Error", f"Module {page_name} has no TABS", bg="#e74c3c")

    # ---------------- Search / Highlight ----------------

    def perform_search(self):
        query = self.search_entry.get().strip()
        if not query:
            return

        found = False
        for page_name, module in MODULE_REGISTRY.items():
            if query.lower() in page_name.lower():
                self.switch_page(page_name)
                found = True
                break

            if hasattr(module, "TABS"):
                for idx, tab_name in enumerate(module.TABS):
                    if query.lower() in tab_name.lower():
                        self.switch_page(page_name)
                        self.notebook.select(idx)
                        found = True
                        break
            if found:
                break

        if found:
            self.highlight_text(query)
            self.app_state.set(f"Found: '{query}'")
        else:
            self.show_toast("Search", f"No results for '{query}'", bg="#e74c3c")

    def highlight_text(self, query: str):
        try:
            idx = self.notebook.index("current")
            if idx < len(self.text_widgets):
                widget = self.text_widgets[idx]
                widget.config(state="normal")
                widget.tag_remove("search", "1.0", "end")
                start = "1.0"
                while True:
                    start = widget.search(query, start, stopindex="end", nocase=True)
                    if not start:
                        break
                    end = f"{start}+{len(query)}c"
                    widget.tag_add("search", start, end)
                    start = end
                widget.tag_config("search", background=HIGHLIGHT_COLOR, foreground="black")
                widget.config(state="disabled")
        except Exception:
            pass

    def clear_search(self):
        self.search_entry.delete(0, "end")
        for w in self.text_widgets:
            w.config(state="normal")
            w.tag_remove("search", "1.0", "end")
            w.config(state="disabled")

    # ---------------- Misc ----------------

    def show_toast(self, title, message, bg=TOAST_ACCENT):
        ToastNotification(self, title, message, bg=bg)

    def new_project(self):
        # Reset dataset + move back to Overview
        APP_DATA["dataframe"] = None
        APP_DATA["filename"] = None
        APP_DATA["rows"] = 0
        APP_DATA["cols"] = 0

        self.switch_page("Overview")
        self.app_state.set("Status: New project initialized")
        self.show_toast(
            "New Project",
            "Workspace reset. Load a new dataset via Data → Import.",
            bg=TOAST_SUCCESS,
        )

    def _start_clock(self):
        self.clock_var.set(datetime.datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._start_clock)

    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self.new_project())
        self.bind("<Control-f>", lambda e: self.search_entry.focus_set())

        self.notebook.bind("<Button-4>", lambda e: self._scroll_tabs(-1))  # Linux wheel up
        self.notebook.bind("<Button-5>", lambda e: self._scroll_tabs(1))   # Linux wheel down
        self.notebook.bind(
            "<MouseWheel>",
            lambda e: self._scroll_tabs(-1 if e.delta > 0 else 1),
        )

    def _scroll_tabs(self, direction: int):
        try:
            curr = self.notebook.index(self.notebook.select())
            nxt = curr + direction
            if 0 <= nxt < self.notebook.index("end"):
                self.notebook.select(nxt)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        app = NestedTabApp()
        app.mainloop()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
