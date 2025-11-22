import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import sys
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import MessageDialog
from tkinter import scrolledtext

# -------------------------
# Example content module
# -------------------------
PAGES = {
    "Overview": ["Welcome", "Release Notes", "Shortcuts"],
    "Data": ["Import", "Explore", "Export"],
    "Settings": ["Appearance", "Preferences", "About"],
}

def create_tab_content(parent, page_name, tab_name, app_state_var):
    """Populate a tab frame with example content."""
    title = tb.Label(parent, text=f"{page_name} — {tab_name}", font=("Helvetica", 12, "bold"))
    title.pack(anchor="w", pady=(0, 8))

    content = scrolledtext.ScrolledText(parent, height=12, wrap="word")
    content.pack(fill="both", expand=True)

    sample_text = f"""
This is the '{tab_name}' tab under '{page_name}'.

- Use the search bar in the header.
- Try the keyboard shortcuts:
  * Ctrl+N (New Project)
  * Ctrl+O (Open Project)
  * Ctrl+F (Focus Search)
- Sidebar buttons switch pages.
- The status indicator updates for app actions.
"""
    content.insert("1.0", sample_text.strip())
    content.config(state="disabled")

    footer = tb.Frame(parent)
    footer.pack(fill="x", pady=(10, 0))
    tb.Button(footer, text="Update status", bootstyle=INFO,
              command=lambda: app_state_var.set("Status: Tab action completed")).pack(side="left")




class NestedTabApp(tb.Window):
    """
    Landscape GUI with nested sidebar tabs, menu, search bar, shortcuts, tooltips, and status.
    """
    def __init__(self, theme="cyborg"):
        super().__init__(themename=theme)
        self.title("Landscape GUI Template - ttkbootstrap")
        self.app_state = tb.StringVar(value="Status: Ready")

        # Window geometry
        self.geometry("900x560")
        self.minsize(700, 480)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Internal state
        self.current_page = None
        self.sidebar_buttons = {}
        self.search_entry = None

        # UI
        self._create_menu()
        self._create_header()
        self._create_main_layout()
        self._bind_shortcuts()

        # Load initial page
        first_page_name = next(iter(PAGES)) if PAGES else None
        if first_page_name:
            self.switch_page(first_page_name)
        else:
            self.app_state.set("Error: No pages available")

    # -------------------------
    # Menu
    # -------------------------
    def _create_menu(self):
        menubar = tb.Menu(self)
        self.config(menu=menubar)

        file_menu = tb.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Project", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_project, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tb.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
    def _style_scrollbars(self):
        style = tb.Style()
        style.configure("Vertical.TScrollbar", arrowsize=12, gripcount=0, width=10)
        style.configure("Horizontal.TScrollbar", arrowsize=12, gripcount=0, height=10)
    # -------------------------
    # Header
    # -------------------------
    def _create_header(self):
        header_frame = tb.Frame(self, padding=10)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        search_frame = tb.Frame(header_frame)
        search_frame.grid(row=0, column=0, sticky="w", padx=10)

        tb.Label(search_frame, text="Search:", font=("Helvetica", 10)).pack(side="left", padx=(0, 5))
        self.search_entry = tb.Entry(search_frame, width=24)
        self.search_entry.pack(side="left", fill="x", padx=(0, 10))
        tb.Button(search_frame, text="Go", bootstyle=PRIMARY, command=self.perform_search).pack(side="left")
        tb.Button(search_frame, text="Clear", bootstyle=LINK, command=self.clear_search).pack(side="left", padx=(8, 0))

        status_label = tb.Label(header_frame, textvariable=self.app_state,
                                font=("Helvetica", 9, "italic"), bootstyle=SECONDARY)
        status_label.grid(row=0, column=1, sticky="e")

    # -------------------------
    # Layout
    # -------------------------
    def _create_main_layout(self):
        main_layout_frame = tb.Frame(self)
        main_layout_frame.grid(row=1, column=0, columnspan=2, sticky="nswe")
        main_layout_frame.grid_rowconfigure(0, weight=1)
        main_layout_frame.grid_columnconfigure(1, weight=1)

        # Sidebar
        self._create_sidebar(main_layout_frame)

        # Notebook
        main_frame = tb.Frame(main_layout_frame, padding=10)
        main_frame.grid(row=0, column=1, sticky="nswe")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.notebook = tb.Notebook(main_frame, bootstyle=PRIMARY)
        self.notebook.grid(row=0, column=0, sticky="nswe")

    def _create_sidebar(self, parent_frame):
        sidebar = tb.Frame(parent_frame, bootstyle=SECONDARY, width=160)
        sidebar.grid(row=0, column=0, sticky="nswe")
        sidebar.grid_propagate(False)

        title_label = tb.Label(sidebar, text="APP MODULES", font=("Helvetica", 10, "bold"),
                               bootstyle=INVERSE)
        title_label.pack(fill="x", padx=5, pady=5)

        for page_name in PAGES.keys():
            btn = tb.Button(sidebar, text=page_name, bootstyle=INFO,
                            command=lambda name=page_name: self.switch_page(name))
            btn.pack(fill="x", padx=5, pady=3)
            self.sidebar_buttons[page_name] = btn
    def _create_statusbar(self):
        statusbar = tb.Frame(self, bootstyle=SECONDARY)
        statusbar.grid(row=2, column=0, columnspan=2, sticky="ew")
        tb.Label(statusbar, textvariable=self.app_state,
                 font=("Helvetica", 9, "italic"), bootstyle=SECONDARY).pack(side="left", padx=10, pady=4)
    # -------------------------
    # Actions
    # -------------------------
    def perform_search(self):
        query = (self.search_entry.get() or "").strip()
        if query:
            self.app_state.set(f"Searching for: {query}")
            matched_page = None
            for page_name in PAGES:
                if query.lower() in page_name.lower():
                    matched_page = page_name
                    break
            if matched_page:
                self.switch_page(matched_page)
        else:
            self.app_state.set("Status: Ready")

    def clear_search(self):
        if self.search_entry:
            self.search_entry.delete(0, "end")
        self.app_state.set("Status: Ready")

    def focus_search(self):
        if self.search_entry:
            self.search_entry.focus_set()
            self.app_state.set("Status: Focused on Search")

    def switch_page(self, page_name):
        if self.current_page == page_name:
            return
        if page_name not in PAGES:
            self.app_state.set(f"Error: Page '{page_name}' not found")
            return

        self.current_page = page_name
        self.app_state.set(f"Status: Opened '{page_name}'")

        for tab in self.notebook.tabs():
            self.notebook.forget(tab)

        inner_tabs = PAGES.get(page_name, [])
        for tab_name in inner_tabs:
            tab_frame = tb.Frame(self.notebook, padding=10)
            create_tab_content(tab_frame, page_name, tab_name, self.app_state)
            self.notebook.add(tab_frame, text=tab_name)

        if inner_tabs:
            self.notebook.select(0)

    # -------------------------
    # Menu actions
    # -------------------------
    def new_project(self):
        self.app_state.set("Status: New project created")
        MessageDialog(title="New Project", message="New project initialized").show()

    def open_project(self):
        self.app_state.set("Status: Open project dialog")
        MessageDialog(title="Open Project", message="Open dialog not implemented").show()

    def quit_app(self):
        self.destroy()

    def show_about(self):
        MessageDialog(title="About", message="Landscape GUI Template — ttkbootstrap version").show()

    def _bind_shortcuts(self):
        self.bind_all("<Control-n>", lambda e: self.new_project())
        self.bind_all("<Control-o>", lambda e: self.open_project())
        self.bind_all("<Control-f>", lambda e: self.search_entry.focus_set())
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        if self.tip or not self.text:
            return
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.attributes("-topmost", True)
        label = tk.Label(self.tip, text=self.text, bg="#FFFFE0", relief="solid", borderwidth=1, padx=6, pady=4)
        label.pack()
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip.wm_geometry(f"+{x}+{y}")

    def _hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None
    def _toast(self, message, duration_ms=1600):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        frame = tk.Frame(toast, bg="#333333")
        frame.pack(fill="both", expand=True)
        label = tk.Label(frame, text=message, bg="#333333", fg="#FFFFFF", padx=12, pady=8)
        label.pack()
        # Position near bottom-right
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() - 260
        y = self.winfo_rooty() + self.winfo_height() - 100
        toast.geometry(f"240x50+{x}+{y}")
        toast.after(duration_ms, toast.destroy)
    # -------------------------
    # Shortcuts
    # -------------------------
    def _bind_shortcuts(self):
        self.bind_all("<Control-n>", lambda e: self.new_project())
        self.bind_all("<Control-o>", lambda e: self.open_project())
        self.bind_all("<Control-f>", lambda e: self.search_entry.focus_set())

    def _bind_mouse_scroll(self):
        self.notebook.bind_all("<MouseWheel>", self._on_mouse_scroll)

# -------------------------
# Entrypoint
# -------------------------
if __name__ == "__main__":
    try:
        app = NestedTabApp(theme="darkly")
        app.mainloop()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
