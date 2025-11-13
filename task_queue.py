import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import queue
import threading
import time
import concurrent.futures
from datetime import datetime
import os
import csv
import tkinter.font as tkFont

# Custom Priority Queue with Path Mapping
# Structure: (priority_value, task_id, file_path)
class PriorityQueue:
    def __init__(self):
        self._queue = queue.PriorityQueue()
        self._items = {} # Maps file_path to (priority, task_id) for existence checks

    def put(self, file_path, priority, task_id):
        if file_path not in self._items:
            # Lower number = Higher priority (standard for PriorityQueue)
            priority_value = self._get_priority_value(priority)
            self._queue.put((priority_value, task_id, file_path))
            self._items[file_path] = (priority_value, task_id)

    def get(self, timeout=None):
        priority_value, task_id, file_path = self._queue.get(timeout=timeout)
        if file_path in self._items:
            del self._items[file_path]
        return file_path

    def task_done(self):
        self._queue.task_done()
        
    def empty(self):
        return self._queue.empty()
        
    def contains(self, file_path):
        return file_path in self._items

    def _get_priority_value(self, priority_label):
        # High=1, Medium=2, Low=3
        return {"High": 1, "Medium": 2, "Low": 3}.get(priority_label, 2)
        
    def get_priority_label(self, priority_value):
        # 1=High, 2=Medium, 3=Low
        return {1: "High", 2: "Medium", 3: "Low"}.get(priority_value, "Medium")
        
    def get_all_paths(self):
        return list(item[2] for item in self._queue.queue)

class TaskManagerApp:
    def __init__(self, root, num_workers=4):
        self.root = root
        self.root.title("File Queue Task Manager (Advanced)")

        self.file_queue = PriorityQueue() # Use custom PriorityQueue
        self.running = False
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=num_workers)
        self.task_rows = {}          # file_path -> row_id
        self.task_metadata = {}      # file_path -> {"id", "start", "priority", "size", "modified"}
        self.task_counter = 0
        self.worker_threads = []
        self.num_workers = num_workers
        self.stop_event = threading.Event()
        
        # New Control Dictionaries
        self.paused_tasks = {}       # file_path -> True if paused
        self.canceled_tasks = {}     # file_path -> True if canceled

        self.setup_ui()
        self.configure_styles()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

    # --- UI & Style Configuration ---
    
    def configure_styles(self):
        self.style = ttk.Style()
        
        # Color coding for statuses
        self.task_table.tag_configure('queued', foreground='gray', font='Arial 8')
        self.task_table.tag_configure('processing', foreground='blue', font='Arial 8 bold')
        self.task_table.tag_configure('paused', foreground='#ff8c00', font='Arial 8') # Orange for Paused
        self.task_table.tag_configure('completed', foreground='green', font='Arial 8 bold') # Green for Completed
        self.task_table.tag_configure('failed', foreground='red', font='Arial 8 bold') # Red for Failed

        # Custom progress bar aesthetic (same as before)
        self.progress_styles = {}
        for i in range(101):
            tag_name = f"progress_{i}"
            progress_width = int(i / 100.0 * 1000)

            progress_color = '#a6e3a6'
            background_color = '#e5e5e5'

            if i == 100:
                self.style.configure(tag_name, 
                                     fieldbackground=[("selected", "SystemHighlight"), ("!selected", "green")], 
                                     foreground=[("selected", "white"), ("!selected", "black")])
            else:
                self.style.configure(tag_name, 
                                     fieldbackground=[
                                         ("selected", "SystemHighlight"), 
                                         ("!selected", 
                                          [('progress_bg.Tredge', 0, progress_width, progress_color), 
                                           ('progress_bg.Tredge', progress_width, 1000, background_color)]
                                         )
                                     ], 
                                     foreground=[("selected", "white"), ("!selected", "black")])
            
            self.task_table.tag_configure(tag_name, background="", font='Arial 8 bold')
            self.progress_styles[i] = tag_name

    def setup_ui(self):
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        frame = ttk.Frame(self.root, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(2, weight=1) # Notebook is at row 2
        frame.columnconfigure(0, weight=1)

        # --- Settings Frame (Row 0) ---
        settings_frame = ttk.LabelFrame(frame, text="⚙️ Task Settings", padding=5)
        settings_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10), columnspan=2)
        
        # Priority Selector
        ttk.Label(settings_frame, text="Default Priority:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.default_priority = tk.StringVar(value="Medium")
        self.priority_combo = ttk.Combobox(settings_frame, textvariable=self.default_priority, 
                                           values=["High", "Medium", "Low"], state="readonly", width=10)
        self.priority_combo.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        # File Filter Entry
        ttk.Label(settings_frame, text="File Filter (e.g., txt,csv):").grid(row=0, column=2, padx=(20,5), pady=2, sticky="w")
        self.file_filter = tk.StringVar(value="")
        ttk.Entry(settings_frame, textvariable=self.file_filter, width=15).grid(row=0, column=3, padx=5, pady=2, sticky="w")
        
        # Recursive Checkbox
        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Recursive Search", variable=self.recursive_var).grid(row=0, column=4, padx=(20, 5), pady=2, sticky="w")

        # --- Controls Frame (Row 1) ---
        controls = ttk.Frame(frame)
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 10), columnspan=2)
        
        # File/Folder Buttons
        ttk.Button(controls, text="➕ Add File", command=self.add_file).grid(row=0, column=0, padx=5)
        ttk.Button(controls, text="📁 Add Folder", command=self.add_folder).grid(row=0, column=1, padx=5)
        
        # Action Buttons (Start/Stop, Clear)
        self.start_stop_button = ttk.Button(controls, text="▶️ Start Queue", command=self.toggle_workers, style='TButton', width=15)
        self.start_stop_button.grid(row=0, column=2, padx=(20, 5))
        
        ttk.Button(controls, text="⏸️ Pause Selected", command=lambda: self.control_task("Pause")).grid(row=0, column=3, padx=5)
        ttk.Button(controls, text="▶️ Resume Selected", command=lambda: self.control_task("Resume")).grid(row=0, column=4, padx=5)
        ttk.Button(controls, text="🛑 Cancel Selected", command=lambda: self.control_task("Cancel")).grid(row=0, column=5, padx=5)

        ttk.Button(controls, text="🗑️ Clear Queue", command=self.clear_queue).grid(row=0, column=6, padx=(20, 5))
        ttk.Button(controls, text="❌ Exit Safely", command=self.on_exit).grid(row=0, column=7, padx=5)
        
        # --- Notebook (Tabs) (Row 2) ---
        self.notebook = ttk.Notebook(frame)
        self.notebook.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=5)
        
        # --- Task Tab ---
        task_tab = ttk.Frame(self.notebook)
        task_tab.grid_rowconfigure(0, weight=1)
        task_tab.grid_columnconfigure(0, weight=1)
        self.notebook.add(task_tab, text="🏃 Active Tasks")
        
        # ADDED PRIORITY, SIZE, MODIFIED DATE COLUMNS
        self.task_table = ttk.Treeview(task_tab, columns=("id", "file", "priority", "size", "modified", "status", "progress", "started"), show="headings", height=15)
        
        cols = {"id": 60, "file": 350, "priority": 80, "size": 100, "modified": 140, "status": 100, "progress": 120, "started": 130}
        for col, width in cols.items():
            heading_text = col.title().replace('Id', 'ID')
            self.task_table.heading(col, text=heading_text, command=lambda _col=col: self.treeview_sort_column(self.task_table, _col, False))
            self.task_table.column(col, width=width, anchor="w")
        
        self.task_table.column("id", anchor="center")
        self.task_table.column("priority", anchor="center")
        self.task_table.column("status", anchor="center")
        self.task_table.column("progress", anchor="center")
        
        self.task_table.grid(row=0, column=0, sticky="nsew")
        self.task_table.bind("<Double-1>", lambda e: self.on_header_double_click(e, self.task_table))
        
        task_scroll = ttk.Scrollbar(task_tab, orient="vertical", command=self.task_table.yview)
        task_scroll.grid(row=0, column=1, sticky="ns")
        self.task_table.configure(yscrollcommand=task_scroll.set)

        # --- History Tab ---
        history_tab = ttk.Frame(self.notebook)
        history_tab.grid_rowconfigure(0, weight=1)
        history_tab.grid_columnconfigure(0, weight=1)
        self.notebook.add(history_tab, text="✅ History")
        
        # ADDED DURATION AND PRIORITY TO HISTORY
        self.history_table = ttk.Treeview(history_tab, columns=("id", "file", "priority", "completed", "duration", "status"), show="headings", height=15)
        
        history_cols = {"id": 60, "file": 350, "priority": 80, "completed": 150, "duration": 100, "status": 100}
        for col, width in history_cols.items():
            heading_text = col.title().replace('Id', 'ID')
            self.history_table.heading(col, text=heading_text, command=lambda _col=col: self.treeview_sort_column(self.history_table, _col, False))
            self.history_table.column(col, width=width, anchor="w")
            
        self.history_table.column("id", anchor="center")
        self.history_table.column("priority", anchor="center")
        self.history_table.column("duration", anchor="center")
        self.history_table.column("status", anchor="center")
        
        self.history_table.grid(row=0, column=0, sticky="nsew")
        self.history_table.bind("<Double-1>", lambda e: self.on_header_double_click(e, self.history_table))
        
        history_scroll = ttk.Scrollbar(history_tab, orient="vertical", command=self.history_table.yview)
        history_scroll.grid(row=0, column=1, sticky="ns")
        self.history_table.configure(yscrollcommand=history_scroll.set)

        export_button = ttk.Button(history_tab, text="💾 Export History to CSV", command=self.export_history)
        export_button.grid(row=1, column=0, columnspan=2, pady=5, sticky="e")
        
        self.autofit_columns(self.history_table)

    # --- Worker Management ---
    
    # ... (start_workers, stop_workers, toggle_workers, update_queued_to_paused, clear_queue remain the same) ...

    def start_workers(self):
        if not self.running:
            self.running = True
            self.stop_event.clear()
            if self.executor._shutdown:
                self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) 
                
            self.worker_threads.clear()
            
            for _ in range(self.num_workers):
                t = threading.Thread(target=self.worker_loop, daemon=True)
                t.start()
                self.worker_threads.append(t)
            
            # Resume any paused tasks
            for file_path in list(self.paused_tasks.keys()):
                self.root.after(0, lambda fp=file_path: self.control_task_internal(fp, "Resume"))
                
            self.start_stop_button.config(text="⏸️ Stop Queue")

    def stop_workers(self):
        if self.running:
            self.running = False
            self.stop_event.set()
            
            self.root.after(0, self.update_queued_to_paused)
            
            self.start_stop_button.config(text="▶️ Start Queue")
    
    def toggle_workers(self):
        if self.running:
            self.stop_workers()
        else:
            self.start_workers()

    def update_queued_to_paused(self):
        for file_path in list(self.task_rows.keys()):
            row_id = self.task_rows.get(file_path)
            if row_id:
                status = self.task_table.item(row_id, "values")[5] # Status is at index 5
                if status == "Queued":
                    self.update_status(file_path, "Paused")
                    self.paused_tasks[file_path] = True # Treat remaining queued as paused

    def clear_queue(self):
        if self.running:
            messagebox.showerror("Error", "Stop the queue before clearing it.")
            return

        if not self.file_queue.empty() or self.task_rows:
            if not messagebox.askyesno("Clear Queue", "Are you sure you want to clear all pending tasks?"):
                return
        
        # Clear all control dictionaries
        self.paused_tasks.clear()
        self.canceled_tasks.clear()

        # Clear the internal queue
        for path in self.file_queue.get_all_paths():
            try:
                self.file_queue.get(timeout=0)
                self.file_queue.task_done()
            except queue.Empty:
                pass

        for row_id in self.task_table.get_children():
            self.task_table.delete(row_id)
        self.task_rows.clear()
        self.task_metadata.clear()
        
        messagebox.showinfo("Queue Cleared", "All pending tasks have been removed.")

    # --- Task Control (Pause/Resume/Cancel) ---

    def control_task(self, action):
        selected_items = self.task_table.selection()
        if not selected_items:
            messagebox.showinfo("Selection Error", "Please select one or more tasks.")
            return

        for item_id in selected_items:
            # Get the full file path from the metadata based on row_id
            vals = self.task_table.item(item_id, "values")
            file_name = vals[1] 
            
            # Find the file_path from task_rows
            file_path = next((k for k, v in self.task_rows.items() if v == item_id and os.path.basename(k) == file_name), None)
            
            if file_path:
                self.control_task_internal(file_path, action)

    def control_task_internal(self, file_path, action):
        row_id = self.task_rows.get(file_path)
        if not row_id: return

        if action == "Pause":
            if file_path not in self.canceled_tasks:
                self.paused_tasks[file_path] = True
                self.update_status(file_path, "Paused")
        
        elif action == "Resume":
            if file_path in self.paused_tasks and file_path not in self.canceled_tasks:
                del self.paused_tasks[file_path]
                self.update_status(file_path, "Queued")
                
                # Re-add to the priority queue
                priority = self.task_metadata[file_path]["priority"]
                task_id = self.task_metadata[file_path]["id"]
                self.file_queue.put(file_path, priority, task_id)
        
        elif action == "Cancel":
            # If still in queue, remove it instantly
            if self.file_queue.contains(file_path):
                # We can't easily remove from PriorityQueue, so we just mark it as canceled
                pass
            
            self.canceled_tasks[file_path] = True
            self.update_status(file_path, "Cancelling...")
            
            # Immediately finalize and remove from UI
            self.root.after(500, lambda: self.finish_task(file_path, "Canceled"))


    # --- File & Folder Handling ---
    
    def add_file(self):
        priority = self.default_priority.get()
        file_path = filedialog.askopenfilename()
        if file_path:
            self.add_task_to_queue(file_path, priority)

    def add_folder(self):
        priority = self.default_priority.get()
        folder_path = filedialog.askdirectory()
        if folder_path:
            is_recursive = self.recursive_var.get()
            extensions = [ext.strip().lower() for ext in self.file_filter.get().split(',') if ext.strip()]
            
            if is_recursive:
                for root, _, files in os.walk(folder_path):
                    for entry in files:
                        file_path = os.path.join(root, entry)
                        self.check_and_add_file(file_path, priority, extensions)
            else:
                for entry in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, entry)
                    if os.path.isfile(file_path):
                        self.check_and_add_file(file_path, priority, extensions)
                        
    def check_and_add_file(self, file_path, priority, extensions):
        if file_path in self.task_rows: return
        
        if extensions:
            ext = os.path.splitext(file_path)[1].lstrip('.').lower()
            if ext not in extensions:
                return # Skip file if extension filter is active
                
        self.add_task_to_queue(file_path, priority)

    def add_task_to_queue(self, file_path, priority):
        if file_path in self.task_rows:
            messagebox.showinfo("Duplicate", f"File already in queue: {os.path.basename(file_path)}")
            return
            
        self.task_counter += 1
        task_id = self.task_counter
        started = datetime.now()

        # Gather metadata
        try:
            file_size = os.path.getsize(file_path)
            modified_ts = os.path.getmtime(file_path)
            modified_date = datetime.fromtimestamp(modified_ts).strftime("%Y-%m-%d")
        except:
            file_size = 0
            modified_date = "N/A"
            
        file_size_str = self.format_file_size(file_size)

        # Insert into UI
        row_id = self.task_table.insert("", tk.END, 
                                        values=(task_id, os.path.basename(file_path), priority, file_size_str, modified_date, "Queued", "0%", started.strftime("%Y-%m-%d %H:%M:%S")),
                                        tags=('queued', 'progress_0'))
        
        # Store metadata
        self.task_rows[file_path] = row_id
        self.task_metadata[file_path] = {
            "id": task_id, 
            "start": started, 
            "priority": priority, 
            "size": file_size_str, 
            "modified": modified_date
        }
        
        # Put into Priority Queue
        self.file_queue.put(file_path, priority, task_id)
        
    def format_file_size(self, size_bytes):
        if size_bytes == 0: return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while size_bytes >= 1024 and i < len(size_name) - 1:
            size_bytes /= 1024
            i += 1
        return f"{size_bytes:,.1f} {size_name[i]}"


    # --- Task Execution Logic ---

    def worker_loop(self):
        while self.running:
            try:
                # Use PriorityQueue get
                file_path = self.file_queue.get(timeout=0.1)
                
                if not self.running:
                    self.file_queue.put(file_path, "Medium", 0) # Put back
                    break
                
                # Check for cancellation or pause flag *after* retrieving from queue
                if file_path in self.canceled_tasks:
                    self.file_queue.task_done()
                    continue
                
                if file_path in self.paused_tasks:
                    # Put the item back into the queue for next worker/resume, and mark task done for queue count
                    priority = self.task_metadata[file_path]["priority"]
                    task_id = self.task_metadata[file_path]["id"]
                    self.file_queue.put(file_path, priority, task_id)
                    self.file_queue.task_done()
                    continue
                    
                self.executor.submit(self.process_file, file_path)
                self.file_queue.task_done()
                
            except queue.Empty:
                if self.stop_event.is_set():
                    break
                continue
                
    def process_file(self, file_path):
        if not self.running or file_path in self.canceled_tasks or file_path in self.paused_tasks:
            self.root.after(0, lambda: self.update_status(file_path, "Paused" if file_path in self.paused_tasks else "Queued"))
            return

        try:
            self.root.after(0, lambda: self.update_status(file_path, "Processing"))
            
            # Simulated work
            for i in range(1, 101):
                if not self.running or file_path in self.canceled_tasks or file_path in self.paused_tasks:
                    self.root.after(0, lambda: self.update_status(file_path, "Paused" if file_path in self.paused_tasks else "Cancelling..."))
                    return
                    
                time.sleep(0.02)
                self.root.after(0, lambda val=i: self.update_progress(file_path, val))
            
            self.root.after(0, lambda: self.finish_task(file_path, "Completed"))
            
        except Exception:
            self.root.after(0, lambda: self.finish_task(file_path, "Failed"))

    def update_status(self, file_path, status):
        row_id = self.task_rows.get(file_path)
        if row_id:
            vals = list(self.task_table.item(row_id, "values"))
            vals[5] = status # Status is at index 5
            
            current_tags = list(self.task_table.item(row_id, "tags"))
            # Remove old status tags
            new_tags = [t for t in current_tags if not t in ('queued', 'processing', 'paused', 'completed', 'failed')]
            
            # Add new status tag
            if status == "Queued":
                new_tags.append('queued')
            elif status == "Processing":
                new_tags.append('processing')
            elif status == "Paused":
                new_tags.append('paused')
            
            self.task_table.item(row_id, values=vals, tags=tuple(new_tags))

    def update_progress(self, file_path, value):
        row_id = self.task_rows.get(file_path)
        if row_id:
            vals = list(self.task_table.item(row_id, "values"))
            vals[6] = f"{value}%" # Progress is at index 6
            
            current_tags = list(self.task_table.item(row_id, "tags"))
            new_tags = [t for t in current_tags if not t.startswith('progress_')]
            new_tags.append(self.progress_styles.get(value, 'progress_0'))
            
            self.task_table.item(row_id, values=vals, tags=tuple(new_tags))

    def finish_task(self, file_path, status):
        # Clean up control flags
        self.paused_tasks.pop(file_path, None)
        self.canceled_tasks.pop(file_path, None)
        
        if file_path in self.task_rows:
            row_id = self.task_rows.pop(file_path)
            current_vals = self.task_table.item(row_id, "values") 
            
            if file_path in self.task_metadata:
                metadata = self.task_metadata.pop(file_path)
                task_id = metadata["id"]
                start_time = metadata["start"]
                priority = metadata["priority"]
                
                end_time = datetime.now()
                duration = round((end_time - start_time).total_seconds(), 2)
            else:
                task_id = 0
                priority = "N/A"
                end_time = datetime.now()
                duration = 0
                
            # Add to history table
            tag = 'completed' if status == "Completed" else 'failed'
            self.history_table.insert("", tk.END, values=(task_id, os.path.basename(file_path), priority, end_time.strftime("%Y-%m-%d %H:%M:%S"), duration, status), tags=(tag))
            self.autofit_columns(self.history_table)
            
            # Update the 'Active Task' row before deleting
            progress_tag = 'progress_100' if status == "Completed" else 'progress_0'
            
            # Use current_vals[0] (ID), current_vals[1] (File), current_vals[2] (Priority), current_vals[7] (Started At)
            self.task_table.item(row_id, values=(current_vals[0], current_vals[1], current_vals[2], current_vals[3], current_vals[4], status, "100%", current_vals[7]), tags=(tag, progress_tag))
            
            self.root.after(500, lambda: self.task_table.delete(row_id))

    # --- Utility Functions (autofit, sort, export, exit remain largely the same) ---

    def export_history(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Save History as CSV")
        if save_path:
            try:
                with open(save_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Task ID", "File Name", "Priority", "Completed At", "Duration (s)", "Finish Status"])
                    for row_id in self.history_table.get_children():
                        values = self.history_table.item(row_id, "values")
                        writer.writerow(values)
                messagebox.showinfo("Export Successful", f"History exported to {save_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Error exporting history: {e}")

    def on_exit(self):
        if not self.file_queue.empty() or self.running:
            if not messagebox.askyesno("Exit", "Queue still has pending tasks or workers are running. Exit anyway?"):
                return
        
        self.stop_workers()
        self.executor.shutdown(wait=False)

        for t in self.worker_threads:
            if t.is_alive():
                 t.join(timeout=0.1)

        self.root.destroy()

    def autofit_columns(self, treeview):
        font = tkFont.Font(font=('TkDefaultFont', 9))
        for col in treeview["columns"]:
            max_width = font.measure(treeview.heading(col, "text")) + 10
            
            for row_id in treeview.get_children():
                val = treeview.set(row_id, col)
                if val:
                    width = font.measure(str(val))
                    if width > max_width:
                        max_width = width
            treeview.column(col, width=max_width + 10 if max_width < 50 else max_width + 10)

    def autofit_column(self, treeview, col_id):
        font = tkFont.Font(font=('TkDefaultFont', 9))
        col_index = int(col_id.replace("#", "")) - 1
        col_name = treeview["columns"][col_index]
        
        max_width = font.measure(treeview.heading(col_name, "text")) + 10
        
        for row_id in treeview.get_children():
            val = treeview.set(row_id, col_name)
            if val:
                width = font.measure(str(val))
                if width > max_width:
                    max_width = width
        treeview.column(col_name, width=max_width + 10 if max_width < 50 else max_width + 10)

    def on_header_double_click(self, event, treeview):
        region = treeview.identify_region(event.x, event.y)
        if region == "heading":
            col_id = treeview.identify_column(event.x)
            self.autofit_column(treeview, col_id)

    def treeview_sort_column(self, tv, col, reverse):
        items = [(tv.set(k, col), k) for k in tv.get_children('')]
        
        # Custom logic for priority sorting
        if col == "priority":
            # Map High=1, Medium=2, Low=3 for sorting
            priority_map = {"High": 1, "Medium": 2, "Low": 3, "N/A": 4}
            items.sort(key=lambda t: priority_map.get(t[0], 4), reverse=reverse)
        else:
            try:
                # Try to sort numerically (for ID, Progress, Duration)
                items.sort(key=lambda t: float(t[0].strip('%') if isinstance(t[0], str) and t[0].endswith('%') else t[0]), reverse=reverse)
            except ValueError:
                # Fallback to string sort
                items.sort(key=lambda t: t[0], reverse=reverse)
            
        for index, (_, k) in enumerate(items):
            tv.move(k, '', index)
        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManagerApp(root, num_workers=4)
    root.mainloop()
