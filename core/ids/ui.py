import tkinter as tk
from tkinter import ttk
from .service import IDSService
import time
import threading

class IDSUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hornet IDS Monitor")
        self.root.configure(bg="black")
        self.root.geometry("1100x600")

        # Main frame
        self.main_frame = tk.Frame(root, bg="black")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="black",
                        foreground="white",
                        fieldbackground="black",
                        rowheight=25,
                        font=("Consolas", 10))
        style.map('Treeview', background=[('selected', '#4444aa')], foreground=[('selected', 'white')])

        # Columns
        self.tree = ttk.Treeview(self.main_frame,
                                 columns=("PID", "Process", "Start Time", "End Time", "Status", "Camera", "Mic", "Port"),
                                 show='headings')
        for col in ("PID", "Process", "Start Time", "End Time", "Status", "Camera", "Mic", "Port"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Back button
        self.back_button = tk.Button(root, text="Back to Main List", command=self.show_main_list,
                                     bg="#111111", fg="white", font=("Consolas", 10), relief=tk.FLAT)
        self.back_button.pack_forget()

        # Service
        self.service = IDSService()
        self.service.start()

        # Data caches
        self.rows = {}  # pid -> Treeview item
        self.process_times = {}  # pid -> {"start": ts, "end": ts, "running": bool, "data": flow_dict}
        self.cached_flows = []  # background thread writes here
        self.flows_lock = threading.Lock()

        # Bind double click
        self.tree.bind("<Double-1>", self.show_details)

        # Start background thread for flow collection
        threading.Thread(target=self.collect_flows, daemon=True).start()

        # Start UI update loop
        self.update_ui()

    def collect_flows(self):
        """Background thread to fetch new process flows every second"""
        while True:
            flows = self.service.features.sample_flows()
            ts_now = time.time()
            cleaned_flows = []
            for f in flows:
                pid = f["pid"]
                proc = f["proc"]

                # Skip PowerShell called by feature extractor
                if proc.lower() == "powershell.exe" and f.get("source") == "psutil":
                    continue

                f["ts_now"] = ts_now
                cleaned_flows.append(f)

            with self.flows_lock:
                self.cached_flows = cleaned_flows
            time.sleep(1)  # collect every second

    def update_ui(self):
        """Update UI every 0.1 second without lag"""
        with self.flows_lock:
            flows = list(self.cached_flows)
        ts_now = time.time()

        current_pids = set()
        for f in flows:
            pid = f["pid"]
            proc = f["proc"]
            cam = "Yes" if f.get("cam_active", False) else "No"
            mic = "Yes" if f.get("mic_active", False) else "No"
            port = f.get("l_port", "")

            current_pids.add(pid)

            if pid not in self.rows:
                start_ts = ts_now
                end_ts = ts_now
                item = self.tree.insert("", tk.END,
                                        values=(pid, proc,
                                                time.strftime("%H:%M:%S", time.localtime(start_ts)),
                                                time.strftime("%H:%M:%S", time.localtime(end_ts)),
                                                "Running", cam, mic, port))
                self.rows[pid] = item
                self.process_times[pid] = {"start": start_ts, "end": end_ts, "running": True, "data": f}
            else:
                # Update live end time
                self.process_times[pid]["end"] = ts_now
                self.process_times[pid]["running"] = True
                self.process_times[pid]["data"] = f
                item = self.rows[pid]
                self.tree.set(item, "End Time", time.strftime("%H:%M:%S", time.localtime(ts_now)))
                self.tree.set(item, "Status", "Running")
                self.tree.set(item, "Camera", cam)
                self.tree.set(item, "Mic", mic)
                self.tree.set(item, "Port", port)
                self.tree.item(item, tags=("running",))

        # Detect ended processes
        ended_pids = [pid for pid in self.process_times if pid not in current_pids and self.process_times[pid]["running"]]
        for pid in ended_pids:
            self.process_times[pid]["running"] = False
            item = self.rows[pid]
            end_ts = self.process_times[pid]["end"]
            self.tree.set(item, "End Time", time.strftime("%H:%M:%S", time.localtime(end_ts)))
            self.tree.set(item, "Status", "Ended")
            self.tree.item(item, tags=("ended",))

        # Tag colors
        self.tree.tag_configure("running", foreground="lime")
        self.tree.tag_configure("ended", foreground="red")

        # Repeat every 0.1 second for smooth live timer
        self.root.after(100, self.update_ui)

    def show_details(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = selected[0]
        pid = int(self.tree.item(item, "values")[0])
        flow = self.process_times[pid]["data"]

        self.main_frame.pack_forget()
        self.back_button.pack(pady=5)

        detail_win = tk.Frame(self.root, bg="black")
        detail_win.pack(fill=tk.BOTH, expand=True)
        self.detail_win = detail_win

        tk.Label(detail_win, text=f"Details for PID {pid} ({flow['proc']})",
                 bg="black", fg="white", font=("Consolas", 14)).pack(pady=5)

        keys_to_show = ["l_ip", "l_port", "r_ip", "r_port", "r_host", "service", "status", "direction",
                        "is_private_dst", "cam_active", "mic_active", "source"]
        for k in keys_to_show:
            val = flow.get(k, "")
            tk.Label(detail_win, text=f"{k}: {val}", bg="black", fg="white",
                     font=("Consolas", 12), anchor="w").pack(fill=tk.X, padx=10, pady=2)

    def show_main_list(self):
        if hasattr(self, "detail_win"):
            self.detail_win.destroy()
        self.back_button.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = IDSUI(root)
    root.mainloop()
