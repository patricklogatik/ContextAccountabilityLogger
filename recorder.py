import os
import sys
import time
from datetime import datetime, timedelta
from pynput import keyboard, mouse
from PIL import ImageGrab
import threading
import json
from collections import defaultdict
import pyperclip
import psutil
import tkinter as tk

WINDOW_TRACKING_AVAILABLE = False

if sys.platform.startswith("win"):
    try:
        import win32gui  # type: ignore
        import win32process  # type: ignore

        WINDOW_TRACKING_AVAILABLE = True
    except ImportError:
        win32gui = None  # type: ignore
        win32process = None  # type: ignore
        WINDOW_TRACKING_AVAILABLE = False
else:
    win32gui = None  # type: ignore
    win32process = None  # type: ignore

class AppleOverlay:
    def __init__(self, on_goal_change_callback):
        self.on_goal_change = on_goal_change_callback
        self.goal = ""
        self.timer_end = None
        self.window = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        
    def create_window(self):
        self.window = tk.Tk()
        self.window.title("Focus")
    
        screen_width = self.window.winfo_screenwidth()
        bar_width = 480
        bar_height = 42
        
        self.window.geometry(f"{bar_width}x{bar_height}+{(screen_width - bar_width) // 2}+10")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.95)
        
        # Light frame
        main_frame = tk.Frame(self.window, bg='#E5E5E5', bd=0)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # White content
        content = tk.Frame(main_frame, bg='#FFFFFF', bd=0)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Drag handle
        drag_handle = tk.Label(
            content,
            text="⋮⋮",
            font=('Segoe UI', 10),
            bg='#FFFFFF',
            fg='#C7C7CC',
            cursor='fleur',
            padx=8
        )
        drag_handle.pack(side=tk.LEFT)
        drag_handle.bind('<Button-1>', self.start_drag)
        drag_handle.bind('<B1-Motion>', self.do_drag)
        
        # Goal label
        self.goal_label = tk.Label(
            content,
            text="No goal",
            font=('Segoe UI', 10),
            bg='#FFFFFF',
            fg='#8E8E93',
            anchor='w',
            padx=8
        )
        self.goal_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Timer
        self.timer_label = tk.Label(
            content,
            text="",
            font=('Segoe UI', 13, 'bold'),
            bg='#FFFFFF',
            fg='#34C759',
            padx=12
        )
        self.timer_label.pack(side=tk.LEFT)
        
        # Settings button
        settings_btn = tk.Button(
            content,
            text="⚙",
            font=('Segoe UI', 12),
            bg='#FFFFFF',
            fg='#007AFF',
            activebackground='#F2F2F7',
            activeforeground='#007AFF',
            relief=tk.FLAT,
            bd=0,
            width=2,
            cursor='hand2',
            command=self.show_dialog
        )
        settings_btn.pack(side=tk.RIGHT, padx=6, pady=6)
        
        # Draggable
        for widget in [content, main_frame, self.goal_label, self.timer_label]:
            widget.bind('<Button-1>', self.start_drag)
            widget.bind('<B1-Motion>', self.do_drag)
        
        self.update_display()
        self.keep_on_top()
    
    def keep_on_top(self):
        """Re-assert topmost every 2 seconds"""
        if self.window:
            try:
                self.window.attributes('-topmost', True)
                self.window.lift()
                self.window.after(2000, self.keep_on_top)
            except:
                pass

    def start_drag(self, event):
        self.drag_start_x = event.x_root - self.window.winfo_x()
        self.drag_start_y = event.y_root - self.window.winfo_y()
    
    def do_drag(self, event):
        x = event.x_root - self.drag_start_x
        y = event.y_root - self.drag_start_y
        self.window.geometry(f"+{x}+{y}")
        
    def set_goal(self, goal, minutes):
        self.goal = goal
        if minutes > 0:
            self.timer_end = datetime.now() + timedelta(minutes=minutes)
        else:
            self.timer_end = None
        
        if self.on_goal_change:
            self.on_goal_change(goal, minutes)
        
        self.update_display()
    
    def update_display(self):
        if not self.window:
            return
        
        if self.goal:
            self.goal_label.config(text=f"🎯 {self.goal}", fg='#000000')
        else:
            self.goal_label.config(text="No goal - Press ⚙", fg='#8E8E93')
        
        if self.timer_end:
            remaining = (self.timer_end - datetime.now()).total_seconds()
            if remaining > 0:
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                
                if mins >= 10:
                    color = '#34C759'
                elif mins >= 5:
                    color = '#FF9500'
                else:
                    color = '#FF3B30'
                
                self.timer_label.config(text=f"{mins:02d}:{secs:02d}", fg=color)
            else:
                self.timer_label.config(text="Done!", fg='#FF3B30')
        else:
            self.timer_label.config(text="")
        
        self.window.after(1000, self.update_display)
    
    def show_dialog(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Set Focus")
        dialog.geometry("360x240")
        dialog.configure(bg='#FFFFFF')
        dialog.attributes('-topmost', True)
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 180
        y = (dialog.winfo_screenheight() // 2) - 120
        dialog.geometry(f"+{x}+{y}")
        
        # Title
        tk.Label(
            dialog,
            text="What's your focus?",
            font=('Segoe UI', 15),
            bg='#FFFFFF',
            fg='#000000'
        ).pack(pady=(25, 10))
        
        # Goal input
        goal_frame = tk.Frame(dialog, bg='#FFFFFF')
        goal_frame.pack(padx=30, pady=8, fill=tk.X)
        
        goal_entry = tk.Entry(
            goal_frame,
            font=('Segoe UI', 12),
            bg='#F2F2F7',
            fg='#000000',
            insertbackground='#007AFF',
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightcolor='#007AFF',
            highlightbackground='#D1D1D6'
        )
        goal_entry.pack(fill=tk.X, ipady=6, ipadx=8)
        goal_entry.focus()
        
        # Timer label
        tk.Label(
            dialog,
            text="Duration (minutes)",
            font=('Segoe UI', 10),
            bg='#FFFFFF',
            fg='#8E8E93'
        ).pack(pady=(12, 5))
        
        # Timer controls
        timer_frame = tk.Frame(dialog, bg='#FFFFFF')
        timer_frame.pack(pady=5)
        
        timer_entry = tk.Entry(
            timer_frame,
            font=('Segoe UI', 12),
            bg='#F2F2F7',
            fg='#000000',
            insertbackground='#007AFF',
            relief=tk.FLAT,
            width=6,
            bd=0,
            justify='center',
            highlightthickness=1,
            highlightcolor='#007AFF',
            highlightbackground='#D1D1D6'
        )
        timer_entry.insert(0, "25")
        timer_entry.pack(side=tk.LEFT, padx=5, ipady=4)
        
        # Quick buttons
        for mins in [25, 45, 60]:
            btn = tk.Button(
                timer_frame,
                text=str(mins),
                font=('Segoe UI', 10),
                bg='#F2F2F7',
                fg='#007AFF',
                activebackground='#E5E5EA',
                relief=tk.FLAT,
                bd=0,
                padx=10,
                pady=3,
                cursor='hand2',
                command=lambda m=mins: (timer_entry.delete(0, tk.END), timer_entry.insert(0, str(m)))
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        def on_submit():
            goal = goal_entry.get().strip()
            try:
                minutes = int(timer_entry.get())
            except:
                minutes = 25
            
            if goal:
                self.set_goal(goal, minutes)
            dialog.destroy()
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg='#FFFFFF')
        btn_frame.pack(pady=20)
        
        # Start button
        start_btn = tk.Button(
            btn_frame,
            text="Start Focus",
            font=('Segoe UI', 12),
            bg='#007AFF',
            fg='#FFFFFF',
            activebackground='#0051D5',
            activeforeground='#FFFFFF',
            relief=tk.FLAT,
            bd=0,
            padx=25,
            pady=8,
            cursor='hand2',
            command=on_submit
        )
        start_btn.pack(side=tk.LEFT, padx=4)
        
        # Cancel button
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=('Segoe UI', 12),
            bg='#F2F2F7',
            fg='#000000',
            activebackground='#E5E5EA',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=dialog.destroy
        )
        cancel_btn.pack(side=tk.LEFT, padx=4)
        
        goal_entry.bind('<Return>', lambda e: on_submit())
        timer_entry.bind('<Return>', lambda e: on_submit())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    def run(self):
        self.create_window()
        self.window.mainloop()

class ActivityTracker:
    def __init__(self, log_folder, keystroke_interval=15):
        self.log_folder = log_folder
        self.today_folder = os.path.join(log_folder, datetime.now().strftime('%Y-%m-%d'))
        self.screenshot_folder = os.path.join(self.today_folder, "screenshots")
        
        self.activity_log_file = os.path.join(self.today_folder, "activity_log.json")
        self.keylog_file = os.path.join(self.today_folder, "keystrokes.txt")
        self.clipboard_file = os.path.join(self.today_folder, "clipboard.txt")
        self.window_log_file = os.path.join(self.today_folder, "windows.txt")
        self.events_file = os.path.join(self.today_folder, "events.txt")
        self.app_usage_file = os.path.join(self.today_folder, "app_usage_summary.json")
        self.session_summary_file = os.path.join(self.today_folder, "session_summary.json")
        
        os.makedirs(self.screenshot_folder, exist_ok=True)
        
        if not os.path.exists(self.activity_log_file):
            with open(self.activity_log_file, 'w') as f:
                json.dump([], f)
        
        self.log_lock = threading.Lock()
        self.keystroke_buffer = []
        self.keystroke_interval = keystroke_interval
        self.last_clipboard = ""
        self.current_window = ""
        self.current_app = ""
        self.app_usage_time = defaultdict(float)
        self.last_window_check = datetime.now()
        self.session_start = datetime.now()
        self.keystroke_count = 0
        self.screenshot_count = 0
        self.last_activity = datetime.now()
        
        self.goal_overlay = AppleOverlay(self.log_goal_change)
        self.ctrl_pressed = False
        self.window_tracking_enabled = WINDOW_TRACKING_AVAILABLE
        self.multi_monitor_capture = True

        self.log_event("system", "session_started", {})

        if not self.window_tracking_enabled:
            print("Window tracking disabled: win32 APIs not available on this platform.")
            self.log_event("system", "window_tracking_unavailable", {"platform": sys.platform})

        with open(self.keylog_file, 'a', encoding='utf-8') as f:
            f.write(f"\n=== Session started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        with open(self.events_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{self.session_start.strftime('%Y-%m-%d %H:%M:%S')}] Session started\n")
        
        self.running = True
    
    def log_goal_change(self, goal, minutes):
        self.log_event("goal", "goal_set", {
            "goal": goal,
            "timer_minutes": minutes,
            "timer_end": (datetime.now() + timedelta(minutes=minutes)).isoformat() if minutes > 0 else None
        })
        print(f"Goal set: {goal} ({minutes} minutes)")
    
    def log_event(self, event_type, event_name, data):
        try:
            with self.log_lock:
                with open(self.activity_log_file, 'r') as f:
                    log = json.load(f)
                
                event = {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": event_type,
                    "event_name": event_name,
                    "data": data
                }
                log.append(event)
                
                with open(self.activity_log_file, 'w') as f:
                    json.dump(log, f, indent=2)
        except Exception as e:
            print(f"Log event error: {e}")
    
    def take_screenshot(self):
        while self.running:
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                try:
                    if self.multi_monitor_capture:
                        screenshot = ImageGrab.grab(all_screens=True)
                    else:
                        screenshot = ImageGrab.grab()
                except TypeError:
                    screenshot = ImageGrab.grab()
                    self.multi_monitor_capture = False

                filename = os.path.join(self.screenshot_folder, f"screenshot_{timestamp}.png")
                screenshot.save(filename)
                self.screenshot_count += 1
                
                self.log_event("screenshot", "captured", {
                    "filename": f"screenshot_{timestamp}.png",
                    "path": filename
                })
                
                print(f"Screenshot saved: {filename}")
            except Exception as e:
                print(f"Screenshot error: {e}")
            
            time.sleep(120)
    
    def save_keystroke_buffer(self):
        while self.running:
            time.sleep(self.keystroke_interval)
            
            if self.keystroke_buffer:
                try:
                    keystroke_text = ''.join(self.keystroke_buffer)
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    self.log_event("input", "keystrokes", {
                        "text": keystroke_text,
                        "length": len(self.keystroke_buffer)
                    })
                    
                    with open(self.keylog_file, 'a', encoding='utf-8') as f:
                        f.write(f"[{timestamp}] {keystroke_text}\n")
                    
                    print(f"Logged {len(self.keystroke_buffer)} keystrokes")
                    self.keystroke_buffer.clear()
                except Exception as e:
                    print(f"Keylog error: {e}")
    
    def on_press(self, key):
        try:
            self.keystroke_count += 1
            self.last_activity = datetime.now()
            
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            elif self.ctrl_pressed:
                if hasattr(key, 'char') and key.char and key.char.lower() == 'q':
                    print("Ctrl+Q detected!")
                    if self.goal_overlay and self.goal_overlay.window:
                        self.goal_overlay.window.after(0, self.goal_overlay.show_dialog)
                    self.ctrl_pressed = False
                    return
            
            if key != keyboard.Key.ctrl_l and key != keyboard.Key.ctrl_r:
                if not (hasattr(key, 'char') and key.char and key.char.lower() == 'q'):
                    self.ctrl_pressed = False
            
            try:
                self.keystroke_buffer.append(key.char)
            except AttributeError:
                if key == keyboard.Key.backspace:
                    if self.keystroke_buffer:
                        self.keystroke_buffer.pop()
                elif key == keyboard.Key.enter:
                    self.keystroke_buffer.append('\n')
                elif key == keyboard.Key.tab:
                    self.keystroke_buffer.append('\t')
                elif key == keyboard.Key.space:
                    self.keystroke_buffer.append(' ')
                elif key in [keyboard.Key.delete, keyboard.Key.esc]:
                    self.keystroke_buffer.append(f"[{key.name}]")
        except Exception as e:
            print(f"Key capture error: {e}")
    
    def on_release(self, key):
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False
    
    def get_active_window_info(self):
        if not self.window_tracking_enabled or not WINDOW_TRACKING_AVAILABLE or win32gui is None:
            return "Unavailable", "Unavailable"

        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            app_name = process.name()
            return app_name, window_title
        except Exception:
            return "Unknown", "Unknown"

    def track_window_activity(self):
        if not self.window_tracking_enabled:
            return

        while self.running:
            try:
                app_name, window_title = self.get_active_window_info()
                current_time = datetime.now()
                
                window_info = f"{app_name} - {window_title}"
                if window_info != self.current_window and window_title not in {"Unknown", "Unavailable"}:
                    time_spent = 0
                    if self.current_window:
                        time_spent = (current_time - self.last_window_check).total_seconds()
                        self.app_usage_time[self.current_app] += time_spent
                    
                    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    self.log_event("window", "changed", {
                        "app": app_name,
                        "window_title": window_title,
                        "previous_app": self.current_app if self.current_app else None,
                        "time_on_previous": round(time_spent, 2)
                    })
                    
                    with open(self.window_log_file, 'a', encoding='utf-8') as f:
                        f.write(f"[{timestamp}] {app_name} → {window_title}\n")
                    
                    print(f"Window: {app_name} - {window_title[:50]}")
                    
                    self.current_window = window_info
                    self.current_app = app_name
                    self.last_window_check = current_time
                
            except Exception as e:
                print(f"Window tracking error: {e}")
            
            time.sleep(2)
    
    def on_mouse_event(self, x, y):
        self.last_activity = datetime.now()
    
    def on_mouse_click(self, x, y, button, pressed):
        if pressed:
            self.last_activity = datetime.now()
    
    def start_mouse_listener(self):
        with mouse.Listener(on_move=self.on_mouse_event, on_click=self.on_mouse_click) as listener:
            listener.join()
    
    def monitor_clipboard(self):
        while self.running:
            try:
                current_clipboard = pyperclip.paste()
                
                if current_clipboard != self.last_clipboard and current_clipboard.strip():
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    self.log_event("clipboard", "changed", {
                        "content": current_clipboard,
                        "length": len(current_clipboard)
                    })
                    
                    with open(self.clipboard_file, 'a', encoding='utf-8') as f:
                        f.write(f"\n[{timestamp}] CLIPBOARD:\n{current_clipboard}\n")
                        f.write("-" * 50 + "\n")
                    
                    print(f"Clipboard logged ({len(current_clipboard)} chars)")
                    self.last_clipboard = current_clipboard
                    
            except Exception as e:
                print(f"Clipboard error: {e}")
            
            time.sleep(1)
    
    def start_keylogger(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()
    
    def save_session_stats(self):
        while self.running:
            time.sleep(300)
            
            try:
                session_duration = (datetime.now() - self.session_start).total_seconds()
                idle_time = (datetime.now() - self.last_activity).total_seconds()
                is_idle = idle_time > 60
                
                self.log_event("status", "activity_check", {
                    "session_duration_minutes": round(session_duration / 60, 2),
                    "idle_seconds": round(idle_time, 2),
                    "is_idle": is_idle,
                    "keystrokes_total": self.keystroke_count,
                    "screenshots_total": self.screenshot_count,
                    "current_app": self.current_app,
                    "current_window": self.current_window[:100] if self.current_window else ""
                })
                
                idle_status = "IDLE" if is_idle else "ACTIVE"
                print(f"Status: {round(session_duration / 60, 2)}min, {idle_status}, App: {self.current_app}")
            except Exception as e:
                print(f"Stats error: {e}")
    
    def save_session_summary(self):
        try:
            if self.current_app:
                time_spent = (datetime.now() - self.last_window_check).total_seconds()
                self.app_usage_time[self.current_app] += time_spent
            
            session_duration = (datetime.now() - self.session_start).total_seconds()
            
            app_usage_minutes = {app: round(seconds / 60, 2) 
                                for app, seconds in self.app_usage_time.items()}
            
            summary = {
                "session_start": self.session_start.isoformat(),
                "session_end": datetime.now().isoformat(),
                "total_duration_minutes": round(session_duration / 60, 2),
                "total_keystrokes": self.keystroke_count,
                "total_screenshots": self.screenshot_count,
                "app_usage_minutes": app_usage_minutes,
                "top_apps": sorted(app_usage_minutes.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
            with open(self.app_usage_file, 'w') as f:
                json.dump(app_usage_minutes, f, indent=2)
            
            with open(self.session_summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"\nSession Summary:")
            print(f"  Duration: {summary['total_duration_minutes']} minutes")
            print(f"  Keystrokes: {summary['total_keystrokes']}")
            print(f"  Screenshots: {summary['total_screenshots']}")
            print(f"  Top Apps: {summary['top_apps']}")
            
        except Exception as e:
            print(f"Summary save error: {e}")
    
    def run(self):
        # Start all tracking threads in background
        threads = [
            threading.Thread(target=self.take_screenshot, daemon=True),
            threading.Thread(target=self.start_keylogger, daemon=True),
            threading.Thread(target=self.save_keystroke_buffer, daemon=True),
            threading.Thread(target=self.save_session_stats, daemon=True),
            threading.Thread(target=self.monitor_clipboard, daemon=True),
            threading.Thread(target=self.start_mouse_listener, daemon=True)
        ]

        if self.window_tracking_enabled:
            threads.append(threading.Thread(target=self.track_window_activity, daemon=True))
        else:
            print("Active window tracking is disabled for this platform.")

        for thread in threads:
            thread.start()
        
        print(f"Activity tracker started. Logging to: {self.today_folder}")
        print(f"Keystrokes saved every {self.keystroke_interval} seconds")
        if self.window_tracking_enabled:
            print("All tracking active (clipboard, window, mouse)")
        else:
            print("Tracking active (clipboard, mouse) – window tracking disabled on this platform")
        print("Unified activity log: activity_log.json")
        print("")
        print("APPLE-STYLE OVERLAY")
        print("  • Light bar at top-center")
        print("  • Click gear or press Ctrl+Q to set goal")
        print("")
        print("Starting overlay (Ctrl+C to stop)...")
        print("=" * 60)
        
        # Run overlay in MAIN thread (stable)
        try:
            self.goal_overlay.run()
        except KeyboardInterrupt:
            pass
        finally:
            print("\nStopping activity tracker...")
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            duration = round((datetime.now() - self.session_start).total_seconds() / 60, 2)
            
            self.log_event("system", "session_ended", {"duration_minutes": duration})
            
            with open(self.events_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] Session ended (Duration: {duration} min)\n")
            
            self.running = False
            time.sleep(1)
            self.save_session_summary()

if __name__ == "__main__":
    CONFIG_FILE = "tracker_config.json"
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            log_folder = config.get('log_folder')
            keystroke_interval = config.get('keystroke_interval', 15)
    else:
        print("First time setup - Please specify the log folder:")
        log_folder = input("Enter full path for logs (e.g., C:\\ActivityLogs): ").strip()
        log_folder = log_folder.strip('"').strip("'")
        
        interval_choice = input("Save keystrokes every: (1) 15 seconds [default], (2) 30 seconds, (3) 60 seconds: ").strip()
        keystroke_interval = {'1': 15, '2': 30, '3': 60}.get(interval_choice, 15)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'log_folder': log_folder, 'keystroke_interval': keystroke_interval}, f)
        
        print(f"Configuration saved. Keystrokes will be saved every {keystroke_interval} seconds")
    
    tracker = ActivityTracker(log_folder, keystroke_interval)

    tracker.run()
