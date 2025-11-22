import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import sys

# --- Configuration Data ---
# Outer Tab Name maps to a list of Inner Tab Names
PAGES = {
    "Project Dashboard": ["Metrics Overview", "Resource Usage", "Activity Log"],
    "System Settings": ["User Accounts", "Security Policy", "Database Sync", "About App"],
    "Reporting Tools": ["Generate Report", "View History", "Configure Schedule"],
    "Help & Documentation": ["Quick Start Guide", "FAQ", "Contact Support"]
}

class NestedTabApp(tk.Tk):
    """
    Main application class for the landscape GUI with nested sidebar tabs.
    """
    def __init__(self):
        super().__init__()
        self.title("Landscape GUI Template - Nested Tabs")
        
        # Set landscape geometry and minimum size
        self.geometry("1000x650") 
        self.minsize(800, 550) 
        
        # Configure the main grid layout (1 row, 2 columns) to be responsive
        self.grid_rowconfigure(0, weight=1)
        # Column 0 (Sidebar) fixed width, Column 1 (Main Content) takes up all extra space
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Main Content

        # --- Apply a basic theme for better aesthetics ---
        style = ttk.Style(self)
        style.theme_use('default') # Use 'clam' for a modern look (or 'default', 'alt', 'classic')

        # Custom styling for the sidebar buttons
        style.configure('Sidebar.TButton', 
                        font=('Helvetica', 12, 'bold'),
                        padding=[10, 15, 10, 15],
                        foreground='white',
                        background='#3F51B5', # Deep Indigo for primary buttons
                        relief='flat')
        style.map('Sidebar.TButton',
                  background=[('active', '#5C6BC0')],
                  foreground=[('disabled', '#AAAAAA')])
        
        # Custom styling for the active sidebar button indicator
        style.configure('Active.Sidebar.TButton',
                        background='#FF9800', # Amber for active indicator
                        foreground='white')

        self.current_page = None
        self.sidebar_buttons = {}

        # Initialize UI components
        self.create_sidebar()
        self.create_main_content_area()
        
        # Load the initial page
        first_page_name = list(PAGES.keys())[0]
        self.switch_page(first_page_name)

    def create_sidebar(self):
        """Creates the fixed-width sidebar Frame containing the outer tab buttons."""
        sidebar = tk.Frame(self, bg='#212121', width=200, relief='raised') # Dark background
        sidebar.grid(row=0, column=0, sticky="nswe")
        sidebar.grid_propagate(False) # Prevent the frame from resizing to content

        # Title/Logo area
        title_label = tk.Label(sidebar, text="APP NAVIGATION", 
                               font=('Helvetica', 14, 'bold'), 
                               bg='#212121', fg='#FF9800', pady=20)
        title_label.pack(fill='x', padx=10)

        # Create buttons for each outer tab
        for i, page_name in enumerate(PAGES.keys()):
            btn = ttk.Button(sidebar, 
                             text=page_name, 
                             style='Sidebar.TButton', 
                             command=lambda name=page_name: self.switch_page(name))
            btn.pack(fill='x', padx=10, pady=5)
            self.sidebar_buttons[page_name] = btn

    def create_main_content_area(self):
        """Creates the main content area using a ttk.Notebook for inner tabs."""
        
        # Frame to hold the Notebook, making padding easier
        main_frame = ttk.Frame(self, padding="15 15 15 15")
        main_frame.grid(row=0, column=1, sticky="nswe")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # The main ttk.Notebook for the inner tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky="nswe")
        
    def switch_page(self, page_name):
        """
        Switches the currently visible set of inner tabs (the "page") 
        based on the clicked sidebar button.
        """
        if self.current_page == page_name:
            return

        # 1. Update Sidebar Button Styles (Visual feedback)
        for name, btn in self.sidebar_buttons.items():
            if name == page_name:
                btn.configure(style='Active.Sidebar.TButton')
            else:
                btn.configure(style='Sidebar.TButton')
        
        self.current_page = page_name
        
        # 2. Clear existing inner tabs
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)

        # 3. Build new inner tabs for the selected page
        inner_tabs = PAGES[page_name]
        
        for tab_name in inner_tabs:
            tab_frame = ttk.Frame(self.notebook, padding="20")
            
            # Add content to the inner tab frame
            header = ttk.Label(tab_frame, 
                               text=f"{page_name} > {tab_name}", 
                               font=('Helvetica', 16, 'bold'))
            header.pack(pady=(0, 15), anchor='w')
            
            content = scrolledtext.ScrolledText(tab_frame, wrap=tk.WORD, 
                                                width=80, height=25, 
                                                font=('Consolas', 10),
                                                padx=10, pady=10)
            
            # Mock content based on the tab name
            content_text = f"This is the content area for the '{tab_name}' tab.\n\n"
            content_text += "You can embed various widgets here, such as charts, tables, input forms, or complex interactive views.\n\n"
            content_text += f"This view belongs to the main category: '{page_name}'.\n\n"
            
            if 'Security Policy' in tab_name:
                content_text += "Important: Review and update your access control lists annually.\n"
                
            elif 'Report' in tab_name:
                content_text += "Placeholder for report generation controls and output.\n"
                
            elif 'Activity Log' in tab_name:
                content_text += "2023-11-23 10:00: User 'admin' logged in.\n"
                content_text += "2023-11-23 10:15: Report 'Q4-2023' generated by 'manager'.\n"
                content_text += "2023-11-23 10:30: Resource limit exceeded warning received.\n"

            content.insert(tk.END, content_text)
            content.configure(state='disabled') # Make it read-only
            
            content.pack(fill='both', expand=True)

            # Add the frame to the notebook
            self.notebook.add(tab_frame, text=tab_name)
            
        # Select the first inner tab
        if inner_tabs:
            self.notebook.select(0)

if __name__ == "__main__":
    app = NestedTabApp()
    
    # Run the main event loop
    try:
        app.mainloop()
    except tk.TclError as e:
        # Handle common Tkinter errors gracefully if running in certain environments
        if "can't invoke " in str(e) and 'after#0' in str(e):
            print("Tkinter mainloop exited due to environment issue. Re-run or ignore if successful.")
            sys.exit(0)
        else:
            raise
