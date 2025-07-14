import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
import os
import json
import time
from datetime import timedelta

class DoItApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Do it!")
        self.root.geometry("520x700")
        self.root.resizable(False, False)
        self.style = tb.Style("darkly")
        self.task_file = "tasks.json"
        self.tasks = []  # (frame, text, start_time, label)

        self.root.configure(bg="#0D0D0D")

        self.load_data()

        # Title
        self.title_label = tk.Label(self.root, text="💡 Do it!", font=("Segoe UI", 26, "bold"),
                                    fg="#00FFFF", bg="#0D0D0D")
        self.title_label.pack(pady=(20, 5))

        # Counters
        self.counter_label = ttk.Label(self.root, text="", font=("Segoe UI", 10),
                                       foreground="#00FFAA", background="#0D0D0D")
        self.counter_label.pack()

        self.done_label = ttk.Label(self.root, text="", font=("Segoe UI", 10),
                                    foreground="#00FFAA", background="#0D0D0D")
        self.done_label.pack()

        self.rejected_label = ttk.Label(self.root, text="", font=("Segoe UI", 10),
                                        foreground="#00FFAA", background="#0D0D0D")
        self.rejected_label.pack()

        clear_btn = ttk.Button(self.root, text="🧹 Clear Done/Rejected", style="Neon.TButton", command=self.clear_counters)
        clear_btn.pack(pady=(5, 10))

        # Entry
        self.entry_frame = tk.Frame(self.root, bg="#0D0D0D")
        self.entry_frame.pack(pady=10, padx=20, fill="x")

        self.entry = ttk.Entry(self.entry_frame, font=("Segoe UI", 12), style="Neon.TEntry")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.add_task)

        add_btn = ttk.Button(self.entry_frame, text="➕", style="Neon.TButton", width=3, command=self.add_task)
        add_btn.pack(side="right")

        # Scrollable area
        container = tk.Frame(self.root, bg="#0D0D0D")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        self.canvas = tk.Canvas(container, bg="#0D0D0D", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.task_frame = tk.Frame(self.canvas, bg="#0D0D0D")

        self.task_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.task_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mousewheel support
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        self.configure_styles()
        self.load_tasks()
        self.update_timers()
        self.update_counters()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def configure_styles(self):
        self.style.configure("Neon.TEntry",
                             fieldbackground="#1A1A1A",
                             foreground="#00FFFF",
                             padding=10,
                             bordercolor="#00FFFF",
                             lightcolor="#00FFFF",
                             borderwidth=2)

        self.style.configure("Neon.TButton",
                             background="#1A1A1A",
                             foreground="#00FFAA",
                             font=("Segoe UI", 10, "bold"),
                             borderwidth=1)

        self.style.map("Neon.TButton",
                       background=[("active", "#00FFAA")],
                       foreground=[("active", "#0D0D0D")])

    def add_task(self, event=None):
        task_text = self.entry.get().strip()
        if task_text == "":
            return
        start_time = int(time.time())
        self.create_task(task_text, start_time)
        self.data["tasks"].append({"text": task_text, "start": start_time})
        self.save_data()
        self.entry.delete(0, tk.END)
        self.update_counters()

    def create_task(self, task_text, start_time):
        task_container = tk.Frame(self.task_frame, bg="#1A1A1A", pady=5, padx=10)
        task_container.pack(fill="x", pady=8, padx=5)

        label = ttk.Label(task_container, text=task_text, font=("Segoe UI", 11),
                          background="#1A1A1A", foreground="#00FFFF", wraplength=280)
        label.pack(side="top", anchor="w", pady=(0, 3))

        timer_label = ttk.Label(task_container, text="Timer: 00:00:00", font=("Segoe UI", 9),
                                background="#1A1A1A", foreground="#CCCCCC")
        timer_label.pack(side="top", anchor="w")

        button_frame = tk.Frame(task_container, bg="#1A1A1A")
        button_frame.pack(side="top", anchor="e", pady=3)

        tick_btn = ttk.Button(button_frame, text="✅", style="Neon.TButton",
                              command=lambda: self.remove_task(task_container, task_text, "green", "done"))
        tick_btn.pack(side="right", padx=5)

        cross_btn = ttk.Button(button_frame, text="❌", style="Neon.TButton",
                               command=lambda: self.remove_task(task_container, task_text, "red", "rejected"))
        cross_btn.pack(side="right", padx=5)

        self.tasks.append((task_container, task_text, start_time, timer_label))

    def update_timers(self):
        now = int(time.time())
        for _, _, start, label in self.tasks:
            elapsed = now - start
            label.config(text="Timer: " + str(timedelta(seconds=elapsed)))
        self.root.after(1000, self.update_timers)

    def remove_task(self, task_widget, task_text, color, status):
        self.data["tasks"] = [t for t in self.data["tasks"] if t["text"] != task_text]
        if status == "done":
            self.data["completed"] += 1
        elif status == "rejected":
            self.data["rejected"] += 1
        self.save_data()

        def slide_out(height=30):
            if height <= 0:
                task_widget.destroy()
                self.tasks = [t for t in self.tasks if t[0] != task_widget]
                self.update_counters()
                return
            task_widget.configure(height=height)
            task_widget.pack_configure(ipady=height // 5)
            task_widget.after(15, lambda: slide_out(height - 2))

        task_widget.configure(bg=color)
        slide_out()

    def clear_counters(self):
        self.data["completed"] = 0
        self.data["rejected"] = 0
        self.save_data()
        self.update_counters()

    def update_counters(self):
        self.counter_label.config(text=f"📝 Tasks Pending: {len(self.tasks)}")
        self.done_label.config(text=f"✅ Completed: {self.data['completed']}")
        self.rejected_label.config(text=f"❌ Rejected: {self.data['rejected']}")

    def load_tasks(self):
        for t in self.data["tasks"]:
            self.create_task(t["text"], t["start"])

    def load_data(self):
        if os.path.exists(self.task_file):
            with open(self.task_file, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {"tasks": [], "completed": 0, "rejected": 0}
            self.save_data()

    def save_data(self):
        with open(self.task_file, "w") as f:
            json.dump(self.data, f, indent=2)

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = DoItApp(root)
    root.mainloop()
