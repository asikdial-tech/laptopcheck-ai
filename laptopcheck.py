import platform
import os
import sys
import subprocess
import multiprocessing
import time
import tkinter as tk
from tkinter import ttk, messagebox
import pygame
import datetime
import webbrowser
import base64
from io import BytesIO
import matplotlib.pyplot as plt  # For simple plots in report

# Initialize pygame for sound
pygame.mixer.init()

def get_os_type():
    return platform.system().lower()

def get_processor_info():
    info = {
        'Model': platform.processor(),
        'Architecture': platform.machine(),
        'Cores': os.cpu_count(),
        'Variant': platform.release()  # Approximate
    }
    # No direct "usage hours" for processor, approximate with system uptime
    try:
        if 'windows' in get_os_type():
            uptime = subprocess.check_output('net stats workstation').decode()
            uptime = uptime.split('\n')[2].split()[-1]
        elif 'linux' in get_os_type():
            with open('/proc/uptime', 'r') as f:
                uptime = float(f.read().split()[0]) / 3600  # hours
                uptime = f"{uptime:.2f} hours"
        elif 'darwin' in get_os_type():
            uptime = subprocess.check_output(['sysctl', '-n', 'kern.boottime']).decode().strip()
            # Simplified, actual calculation needed
            uptime = "Uptime info (Mac)"
        else:
            uptime = "Unknown"
        info['Approximate Usage (Uptime)'] = uptime
    except Exception:
        info['Approximate Usage (Uptime)'] = "Unable to retrieve"
    return info

def get_ram_info():
    os_type = get_os_type()
    info = {}
    try:
        if 'linux' in os_type:
            total = int(subprocess.check_output("cat /proc/meminfo | grep MemTotal | awk '{print $2}'", shell=True)) / 1024 / 1024
            info['Total RAM (GB)'] = f"{total:.2f}"

            # Auto sudo for dmidecode
            cmd = "sudo -n dmidecode -t 17 2>/dev/null || dmidecode -t 17"
            output = subprocess.check_output(cmd, shell=True).decode()
            speeds = [line for line in output.splitlines() if "Speed:" in line and "MHz" in line]
            if speeds:
                speed = speeds[0].split(':')[1].strip().split()[0]
                info['Speed'] = f"{speed} MHz"
            else:
                info['Speed'] = "Unknown"
        # ... keep others
    except:
        info['Speed'] = "Error (run with sudo)"
    return info

def get_battery_info():
    os_type = get_os_type()
    info = {}
    try:
        if 'linux' in os_type:
            capacity_path = '/sys/class/power_supply/BAT0/capacity'
            status_path = '/sys/class/power_supply/BAT0/status'
            cycle_path = '/sys/class/power_supply/BAT0/cycle_count'
            design_path = '/sys/class/power_supply/BAT0/charge_full_design'
            full_path = '/sys/class/power_supply/BAT0/charge_full'

            if os.path.exists(capacity_path):
                capacity = int(open(capacity_path).read().strip())
                status = open(status_path).read().strip()
                cycle = open(cycle_path).read().strip() if os.path.exists(cycle_path) else "N/A"
                design = int(open(design_path).read().strip()) if os.path.exists(design_path) else 0
                full = int(open(full_path).read().strip()) if os.path.exists(full_path) else 0

                health = (full / design * 100) if design > 0 else 0

                info['Current Charge'] = f"{capacity}%"
                info['Status'] = status
                info['Cycle Count'] = cycle
                info['Health'] = f"{health:.1f}%"
                if design and full:
                    info['Capacity'] = f"{design//1000} mWh → {full//1000} mWh"
            else:
                info['Battery'] = "No battery detected"
        # ... keep Windows/macOS parts
    except Exception as e:
        info['Error'] = str(e)
    return info


def test_speakers():
    try:
        pygame.mixer.quit()
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        # Generate 440 Hz tone (A4)
        import numpy as np
        sample_rate = 44100
        duration = 1.5
        freq = 440
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = np.sin(freq * t * 2 * np.pi)
        sound = np.int16(tone * 32767)
        sound_array = pygame.sndarray.make_sound(sound)
        sound_array.play()
        while pygame.mixer.get_busy():
            time.sleep(0.1)
        return "Played 440 Hz tone"
    except Exception as e:
        return f"Speaker test failed: {e}"

def test_keyboard(root):
    def on_key(event):
        messagebox.showinfo("Keyboard Test", f"Key '{event.keysym}' pressed successfully!")
        root.unbind('<Key>')
    
    messagebox.showinfo("Keyboard Test", "Press any key to test.")
    root.bind('<Key>', on_key)
    return "User interaction"

def stress_test(duration=30):
    try:
        import psutil
        start_temp = psutil.sensors_temperatures().get('coretemp', [{}])[0].current if 'coretemp' in psutil.sensors_temperatures() else None

        def worker():
            start = time.time()
            while time.time() - start < duration:
                _ = [x*x for x in range(1000)]
        
        processes = [multiprocessing.Process(target=worker) for _ in range(os.cpu_count())]
        for p in processes: p.start()
        for p in processes: p.join()

        end_temp = psutil.sensors_temperatures().get('coretemp', [{}])[0].current if 'coretemp' in psutil.sensors_temperatures() else None
        temp_str = f"{start_temp}°C → {end_temp}°C" if start_temp and end_temp else "N/A"
        return f"Completed. Temp: {temp_str}"
    except:
        return "Stress test failed (install psutil)"
    
class LaptopCheckApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LaptopCheck AI")
        self.root.geometry("600x400")
        self.root.configure(bg='#f0f0f0')
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 12), padding=10)
        style.configure('TLabel', font=('Helvetica', 10), background='#f0f0f0')
        
        self.frame = ttk.Frame(root, padding=20)
        self.frame.pack(fill='both', expand=True)
        
        ttk.Label(self.frame, text="Laptop Diagnostics Tool").grid(row=0, column=0, columnspan=2, pady=10)
        
        self.run_button = ttk.Button(self.frame, text="Run Diagnostics", command=self.run_diagnostics)
        self.run_button.grid(row=1, column=0, pady=10)
        
        self.report_button = ttk.Button(self.frame, text="Generate Report", command=self.generate_report, state='disabled')
        self.report_button.grid(row=1, column=1, pady=10)
        
        self.results_text = tk.Text(self.frame, height=15, width=70, font=('Courier', 10))
        self.results_text.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.results = {}

    def run_diagnostics(self):
        self.results = {}
        self.results['Processor'] = get_processor_info()
        self.results['RAM'] = get_ram_info()
        self.results['Battery'] = get_battery_info()
        self.results['Speakers'] = test_speakers()
        self.results['Keyboard'] = test_keyboard(self.root)
        stress_result = stress_test(10)  # Short test
        self.results['Stress Test'] = stress_result
        
        self.results_text.delete(1.0, tk.END)
        for section, data in self.results.items():
            self.results_text.insert(tk.END, f"{section}:\n")
            if isinstance(data, dict):
                for k, v in data.items():
                    self.results_text.insert(tk.END, f"  {k}: {v}\n")
            else:
                self.results_text.insert(tk.END, f"  {data}\n")
            self.results_text.insert(tk.END, "\n")
        
        self.report_button['state'] = 'normal'

    def generate_report(self):
        html = "<html><body><h1>LaptopCheck AI Report</h1>"
        html += f"<p>Date: {datetime.datetime.now()}</p>"
        for section, data in self.results.items():
            html += f"<h2>{section}</h2><ul>"
            if isinstance(data, dict):
                for k, v in data.items():
                    html += f"<li><b>{k}:</b> {v}</li>"
            else:
                html += f"<li>{data}</li>"
            html += "</ul>"
        
        # Add a simple plot for visualization
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])  # Dummy plot, replace with real data like CPU load
        ax.set_title("Sample Diagnostic Plot")
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        graphic = base64.b64encode(image_png).decode('utf-8')
        html += f'<img src="data:image/png;base64,{graphic}"/>'
        
        html += "</body></html>"
        
        with open('laptop_report.html', 'w') as f:
            f.write(html)
        
        webbrowser.open('laptop_report.html')
        messagebox.showinfo("Report", "Report generated and opened. Print from browser.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LaptopCheckApp(root)
    root.mainloop()
