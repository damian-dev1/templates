import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox
import sys
import datetime
COLORS = {
    "bg_dark": "#2b2b2b",       # Main background
    "bg_lighter": "#3a3a3a",    # Sidebar/Secondary background
    "fg_light": "#ffffff",      # Main text
    "fg_dim": "#aaaaaa",        # Secondary text
    "accent": "#375a7f",        # Primary button color (Blueish)
    "accent_hover": "#2b4662",  # Darker blue for hover
    "highlight": "#f39c12",     # Search highlight (Orange/Yellow)
    "success": "#00bc8c",       # Success Green
    "entry_bg": "#444444",
    "select_bg": "#375a7f"
}
PAGES = {
    "Overview": ["Welcome", "Release Notes", "Shortcuts"],
    "Data": ["Import", "Explore", "Export"],
    "Settings": ["Appearance", "Preferences", "About"],
}
class ToolTip:
    """Custom ToolTip implementation using standard tkinter."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True) # Remove window decorations
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#ffffe0", foreground="#000000",
                         relief="solid", borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)
    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
class ToastNotification:
    """Custom Toast Notification using standard tkinter Toplevel."""
    def __init__(self, master, title, message, duration=3000, color=COLORS["accent"]):
        self.master = master
        self.window = tk.Toplevel(master)
        self.window.wm_overrideredirect(True)
        frame = tk.Frame(self.window, bg=color, bd=2, relief="raised")
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text=title, font=("Helvetica", 10, "bold"), 
                 bg=color, fg="white", anchor="w").pack(fill="x", padx=10, pady=(5,0))
        tk.Label(frame, text=message, font=("Helvetica", 9), 
                 bg=color, fg="white", anchor="w").pack(fill="x", padx=10, pady=5)
        self.window.update_idletasks()
        width = 250
        height = 60
        x = master.winfo_rootx() + master.winfo_width() - width - 20
        y = master.winfo_rooty() + master.winfo_height() - height - 40
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.after(duration, self.window.destroy)
class NestedTabApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Landscape GUI Template - Standard Lib Only")
        self._center_window(1000, 600)
        self.minsize(800, 500)
        self.style = ttk.Style()
        self._configure_styles()
        self.app_state = tk.StringVar(value="Status: Ready")
        self.clock_var = tk.StringVar()
        self.current_page = None
        self.sidebar_buttons = {}
        self.text_widgets = []
        self.search_entry = None
        self.configure(bg=COLORS["bg_dark"])
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._create_menu()
        self._create_header()
        self._create_main_layout()
        self._create_statusbar()
        self._bind_shortcuts()
        self._start_clock()
        first_page = next(iter(PAGES)) if PAGES else None
        if first_page:
            self.switch_page(first_page)
    def _center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
    def _configure_styles(self):
        """Manually define a Dark Theme using the 'clam' engine."""
        self.style.theme_use('clam')
        self.style.configure(".", 
                             background=COLORS["bg_dark"], 
                             foreground=COLORS["fg_light"], 
                             font=("Segoe UI", 10))
        self.style.configure("TButton", 
                             background=COLORS["accent"], 
                             foreground=COLORS["fg_light"], 
                             borderwidth=0, 
                             focuscolor=COLORS["select_bg"])
        self.style.map("TButton", 
                       background=[('active', COLORS["accent_hover"]), ('pressed', COLORS["success"])])
        self.style.configure("Sidebar.TButton", 
                             background=COLORS["bg_lighter"], 
                             anchor="w", 
                             borderwidth=0)
        self.style.map("Sidebar.TButton", 
                       background=[('active', COLORS["accent"]), ('selected', COLORS["accent"])])
        self.style.configure("Header.TFrame", background=COLORS["accent"])
        self.style.configure("Sidebar.TFrame", background=COLORS["bg_lighter"])
        self.style.configure("Status.TFrame", background=COLORS["bg_lighter"])
        self.style.configure("TNotebook", background=COLORS["bg_dark"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=COLORS["bg_lighter"], foreground=COLORS["fg_light"], padding=[10, 2])
        self.style.map("TNotebook.Tab", background=[("selected", COLORS["accent"])])
        self.style.configure("Header.TLabel", background=COLORS["accent"], foreground=COLORS["fg_light"], font=("Helvetica", 14, "bold"))
        self.style.configure("SidebarHeader.TLabel", background=COLORS["bg_lighter"], foreground=COLORS["fg_dim"], font=("Helvetica", 9, "bold"))
        self.style.configure("Status.TLabel", background=COLORS["bg_lighter"], foreground=COLORS["fg_dim"], font=("Consolas", 9))
    def _create_menu(self):
        menubar = tk.Menu(self, bg=COLORS["bg_lighter"], fg=COLORS["fg_light"], tearoff=0)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["bg_lighter"], fg=COLORS["fg_light"])
        file_menu.add_command(label="New Project", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_project, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["bg_lighter"], fg=COLORS["fg_light"])
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
    def _create_header(self):
        header = ttk.Frame(self, style="Header.TFrame", padding=10)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="GUI TEMPLATE (STD LIB)", style="Header.TLabel").pack(side="left")
        search_frame = ttk.Frame(header, style="Header.TFrame")
        search_frame.pack(side="right")
        self.search_entry = ttk.Entry(search_frame, width=25)
        self.search_entry.pack(side="left", padx=5)
        ToolTip(self.search_entry, "Search content (Ctrl+F)")
        ttk.Button(search_frame, text="🔍", width=3, command=self.perform_search).pack(side="left")
        ttk.Button(search_frame, text="✕", width=3, command=self.clear_search).pack(side="left")
    def _create_main_layout(self):
        container = ttk.Frame(self)
        container.grid(row=1, column=0, sticky="nswe")
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)
        sidebar = ttk.Frame(container, style="Sidebar.TFrame", width=180, padding=(5,10))
        sidebar.grid(row=0, column=0, sticky="nswe")
        sidebar.grid_propagate(False)
        ttk.Label(sidebar, text=" MODULES", style="SidebarHeader.TLabel").pack(anchor="w", pady=5)
        for page in PAGES:
            btn = ttk.Button(sidebar, text=f"  {page}", style='Sidebar.TButton',
                             command=lambda p=page: self.switch_page(p))
            btn.pack(fill="x", pady=2, padx=5)
            self.sidebar_buttons[page] = btn
        content_frame = ttk.Frame(container, padding=10)
        content_frame.grid(row=0, column=1, sticky="nswe")
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill="both", expand=True)
    def _create_statusbar(self):
        bar = ttk.Frame(self, style="Status.TFrame")
        bar.grid(row=2, column=0, sticky="ew")
        ttk.Label(bar, textvariable=self.app_state, style="Status.TLabel").pack(side="left", padx=10, pady=2)
        ttk.Label(bar, textvariable=self.clock_var, style="Status.TLabel").pack(side="right", padx=10, pady=2)
    def create_tab_content(self, page_name, tab_name):
        frame = ttk.Frame(self.notebook, padding=15)
        header_lbl = ttk.Label(frame, text=f"{page_name} / {tab_name}", font=("Helvetica", 16, "bold"))
        header_lbl.pack(anchor="w", pady=(0, 10))
        st = scrolledtext.ScrolledText(frame, height=12, wrap="word", font=("Segoe UI", 10), bd=0, 
                                       bg=COLORS["bg_dark"], fg=COLORS["fg_light"], 
                                       insertbackground=COLORS["fg_light"])
        st.pack(fill="both", expand=True)
        self.text_widgets.append(st) 
        text_content = f"""
        Welcome to the {tab_name} tab.
        Feature Set:
        1. Std Lib Only: No 'pip install' needed.
        2. Dark Mode: Manually configured styles.
        3. Custom Toasts: Native Python implementation.
        The quick brown fox jumps over the lazy dog.
        """
        st.insert("1.0", text_content.strip())
        st.config(state="disabled")
        footer = ttk.Frame(frame)
        footer.pack(fill="x", pady=(10, 0))
        ttk.Button(footer, text="Run Action", 
                  command=lambda: self.show_toast("Action", f"Ran action on {tab_name}")).pack(side="left")
        return frame
    def switch_page(self, page_name):
        if self.current_page == page_name: return
        if self.current_page:
            pass
        self.current_page = page_name
        self.app_state.set(f"Status: Opened {page_name}")
        self.text_widgets.clear()
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        for tab_name in PAGES[page_name]:
            tab = self.create_tab_content(page_name, tab_name)
            self.notebook.add(tab, text=tab_name)
    def perform_search(self):
        query = self.search_entry.get().strip()
        if not query: return
        found = False
        for page, tabs in PAGES.items():
            if query.lower() in page.lower():
                self.switch_page(page)
                found = True
                break
            for tab in tabs:
                if query.lower() in tab.lower():
                    self.switch_page(page)
                    self.notebook.select(tabs.index(tab)) 
                    found = True
                    break
            if found: break
        if found:
            self.highlight_text(query)
            self.app_state.set(f"Found: '{query}'")
        else:
            self.show_toast("Search", f"No results for '{query}'", color="#e74c3c")
    def highlight_text(self, query):
        try:
            current_idx = self.notebook.index("current")
            if current_idx < len(self.text_widgets):
                widget = self.text_widgets[current_idx]
                widget.config(state="normal")
                widget.tag_remove("search", "1.0", "end")
                start = "1.0"
                while True:
                    start = widget.search(query, start, stopindex="end", nocase=True)
                    if not start: break
                    end = f"{start}+{len(query)}c"
                    widget.tag_add("search", start, end)
                    start = end
                widget.tag_config("search", background=COLORS["highlight"], foreground="black")
                widget.config(state="disabled")
        except: pass
    def clear_search(self):
        self.search_entry.delete(0, "end")
        for w in self.text_widgets:
            w.config(state="normal")
            w.tag_remove("search", "1.0", "end")
            w.config(state="disabled")
        self.app_state.set("Status: Ready")
    def show_toast(self, title, message, color=COLORS["accent"]):
        ToastNotification(self, title, message, color=color)
    def new_project(self):
        self.show_toast("New Project", "Project initialized", color=COLORS["success"])
    def open_project(self):
        messagebox.showinfo("Open Project", "File dialog placeholder")
    def show_about(self):
        messagebox.showinfo("About", "Standard Library Template v1.0")
    def quit_app(self):
        self.destroy()
    def _start_clock(self):
        self.clock_var.set(datetime.datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._start_clock)
    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self.new_project())
        self.bind("<Control-o>", lambda e: self.open_project())
        self.bind("<Control-f>", lambda e: self.search_entry.focus_set())
        self.notebook.bind("<Button-4>", lambda e: self._scroll_tabs(-1))
        self.notebook.bind("<Button-5>", lambda e: self._scroll_tabs(1))
        self.notebook.bind("<MouseWheel>", lambda e: self._scroll_tabs(-1 if e.delta > 0 else 1))
    def _scroll_tabs(self, direction):
        try:
            curr = self.notebook.index(self.notebook.select())
            nxt = curr + direction
            if 0 <= nxt < self.notebook.index("end"):
                self.notebook.select(nxt)
        except: pass
if __name__ == "__main__":
    try:
        app = NestedTabApp()
        app.mainloop()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
