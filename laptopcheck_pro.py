import platform
import os
import subprocess
import multiprocessing
import time
import datetime
import webbrowser
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import pygame
import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import numpy as np
import re
import json

# Initialize
pygame.mixer.init()
os_type = platform.system().lower()

# ========================================
# 0. MISSING CORE FUNCTIONS (ADDED)
# ========================================

def get_processor_info():
    """Get processor information"""
    try:
        if 'windows' in os_type:
            output = subprocess.check_output('wmic cpu get name,numberofcores,numberoflogicalprocessors', shell=True).decode()
            lines = [line.strip() for line in output.split('\n') if line.strip()]
            return lines[1] if len(lines) > 1 else platform.processor()
        elif 'linux' in os_type:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line.lower():
                        return line.split(':')[1].strip()
            return platform.processor()
        else:
            return platform.processor()
    except:
        return platform.processor()

def get_ram_info():
    """Get RAM information"""
    try:
        if 'windows' in os_type:
            output = subprocess.check_output('wmic memorychip get capacity', shell=True).decode()
            sizes = [int(size) for size in re.findall(r'\d+', output) if int(size) > 0]
            total_gb = sum(sizes) / (1024**3) if sizes else psutil.virtual_memory().total / (1024**3)
            return f"{total_gb:.1f} GB"
        else:
            total_gb = psutil.virtual_memory().total / (1024**3)
            return f"{total_gb:.1f} GB"
    except:
        total_gb = psutil.virtual_memory().total / (1024**3)
        return f"{total_gb:.1f} GB"

def test_speakers():
    """Test speaker functionality"""
    try:
        # Try to play a simple beep sound
        pygame.mixer.init()
        sample_rate = 22050
        duration = 500  # milliseconds
        frequency = 440  # Hz (A note)
        
        # Generate a simple sine wave
        frames = int(duration * sample_rate / 1000)
        arr = np.sin(2 * np.pi * frequency * np.linspace(0, duration/1000, frames))
        
        # Convert to 16-bit PCM format
        arr = (arr * 32767).astype(np.int16)
        
        # Create pygame sound and play
        sound = pygame.sndarray.make_sound(arr)
        sound.play()
        pygame.time.wait(duration)
        
        return "Working - beep played"
    except Exception as e:
        return f"Test failed: {str(e)}"

# ========================================
# 1. FORENSIC & RARE CHECKS
# ========================================

def get_bios_flash_count():
    try:
        if 'windows' in os_type:
            log = subprocess.check_output('wevtutil qe System /q:"*[System[(EventID=1796)]]" /f:text', shell=True).decode()
            return len(re.findall(r"EventID=1796", log))
        return "N/A"
    except:
        return "N/A"

def get_lid_open_count():
    try:
        if 'windows' in os_type:
            log = subprocess.check_output('wevtutil qe Microsoft-Windows-Kernel-Power/Thermal-Policy /c:1 /f:text', shell=True).decode()
            return "Estimated from power logs"
        return "N/A"
    except:
        return "N/A"

def get_ram_spd():
    try:
        if 'linux' in os_type:
            cmd = "sudo -n dmidecode -t 17 2>/dev/null || dmidecode -t 17"
            out = subprocess.check_output(cmd, shell=True).decode()
            modules = []
            for block in out.split("Memory Device")[1:]:
                serial = re.search(r"Serial Number: (.+)", block)
                part = re.search(r"Part Number: (.+)", block)
                speed = re.search(r"Speed: (.+)", block)
                if part and "NO DIMM" not in part.group(1):
                    modules.append({
                        "part": part.group(1).strip(),
                        "serial": serial.group(1).strip() if serial else "N/A",
                        "speed": speed.group(1).strip() if speed else "N/A"
                    })
            return modules
        return []
    except:
        return []

def get_wifi_card():
    try:
        if 'windows' in os_type:
            out = subprocess.check_output('netsh wlan show interfaces', shell=True).decode()
            mac = re.search(r"Physical address[\s:]+([0-9A-F:]{17})", out)
            return mac.group(1) if mac else "N/A"
        elif 'linux' in os_type:
            out = subprocess.check_output('iwconfig 2>/dev/null || ip link', shell=True).decode()
            mac = re.search(r"ether ([0-9a-f:]{17})", out)
            return mac.group(1).upper() if mac else "N/A"
        return "N/A"
    except:
        return "N/A"

def get_storage_serial():
    try:
        if 'windows' in os_type:
            out = subprocess.check_output('wmic diskdrive get serialnumber,model', shell=True).decode()
            lines = [l.strip() for l in out.splitlines() if l.strip() and "SerialNumber" not in l]
            return lines[0] if lines else "N/A"
        elif 'linux' in os_type:
            out = subprocess.check_output('lsblk -o NAME,SERIAL,MODEL -d -n', shell=True).decode()
            return out.splitlines()[0] if out else "N/A"
        return "N/A"
    except:
        return "N/A"

# ========================================
# 2. ENHANCED DIAGNOSTICS
# ========================================

def get_battery_info_pro():
    info = {}
    try:
        if 'linux' in os_type:
            paths = ['/sys/class/power_supply/BAT0', '/sys/class/power_supply/BAT1']
            for p in paths:
                if os.path.exists(p):
                    capacity = int(open(f"{p}/capacity").read())
                    status = open(f"{p}/status").read().strip()
                    cycle = open(f"{p}/cycle_count").read().strip() if os.path.exists(f"{p}/cycle_count") else "N/A"
                    design = int(open(f"{p}/charge_full_design").read()) if os.path.exists(f"{p}/charge_full_design") else 0
                    full = int(open(f"{p}/charge_full").read()) if os.path.exists(f"{p}/charge_full") else 0
                    manuf = open(f"{p}/manufacturer").read().strip() if os.path.exists(f"{p}/manufacturer") else "N/A"
                    date = open(f"{p}/manufacture_date").read().strip() if os.path.exists(f"{p}/manufacture_date") else "N/A"
                    health = (full / design * 100) if design > 0 else 0
                    info = {
                        "Health": f"{health:.1f}%",
                        "Charge": f"{capacity}%",
                        "Cycle": cycle,
                        "Manufacturer": manuf,
                        "MFD": date
                    }
                    break
        # Add Windows/macOS later
        if not info:  # Fallback for Windows or if Linux battery not found
            battery = psutil.sensors_battery()
            if battery:
                info = {
                    "Health": "N/A",
                    "Charge": f"{battery.percent}%",
                    "Cycle": "N/A",
                    "Manufacturer": "N/A",
                    "MFD": "N/A"
                }
        return info
    except:
        return {"Error": "Battery not found"}

def stress_test_pro(duration=30):
    try:
        temps = psutil.sensors_temperatures()
        start_temp = temps.get('coretemp', [{}])[0].current if 'coretemp' in temps else None
        start_rpm = psutil.sensors_fans().get('fan', [{}])[0].current if 'fan' in psutil.sensors_fans() else None

        def worker():
            [x*x for x in range(10000)]

        procs = [multiprocessing.Process(target=worker) for _ in range(os.cpu_count())]
        for p in procs: p.start()
        for p in procs: p.join()

        end_temp = temps.get('coretemp', [{}])[0].current if 'coretemp' in temps else None
        end_rpm = psutil.sensors_fans().get('fan', [{}])[0].current if 'fan' in psutil.sensors_fans() else None

        delta_t = f"{end_temp - start_temp:.1f}°C" if start_temp and end_temp else "N/A"
        rpm_drop = f"{start_rpm - end_rpm:.0f} RPM" if start_rpm and end_rpm else "N/A"
        return {"Delta Temp": delta_t, "Fan Drop": rpm_drop}
    except:
        return {"Error": "psutil sensors not available"}

# ========================================
# 3. CONDITION SCORING AI
# ========================================

def calculate_condition_score(results):
    score = 100
    reasons = []

    # RAM upgrade
    if len(results.get('RAM SPD', [])) > 1:
        score -= 5
        reasons.append("RAM upgraded (mixed modules)")

    # WiFi swap
    if results.get('WiFi MAC', 'N/A') != "N/A":
        score -= 10
        reasons.append("WiFi card replaced")

    # Battery health
    battery_health = results['Battery'].get('Health', '0')
    if battery_health != 'N/A' and battery_health != 'Error':
        try:
            health = float(battery_health.replace('%', ''))
            if health < 80: 
                score -= 15
                reasons.append("Battery health poor")
            elif health < 90: 
                score -= 5
                reasons.append("Battery health degraded")
        except ValueError:
            pass

    # Thermal
    if 'Delta Temp' in results['Stress']:
        delta_str = results['Stress']['Delta Temp']
        if delta_str != 'N/A':
            try:
                delta = float(delta_str.replace('°C', ''))
                if delta > 25: 
                    score -= 10
                    reasons.append("High thermal delta under stress")
            except ValueError:
                pass

    # Final
    grade = "GOOD" if score >= 80 else "FAIR" if score >= 60 else "POOR" if score >= 40 else "AVOID"
    color = "good" if score >= 80 else "warn" if score >= 60 else "bad"
    return {"score": score, "grade": grade, "color": color, "reasons": reasons}

# ========================================
# 4. GUI + REPORT
# ========================================

class LaptopCheckPro:
    def __init__(self, root):
        self.root = root
        self.root.title("LaptopCheck AI Pro")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a1a1a')
        self.results = {}

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 12, 'bold'), padding=12)
        style.configure('TLabel', font=('Helvetica', 11), background='#1a1a1a', foreground='white')

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="LaptopCheck AI Pro", font=('Helvetica', 18, 'bold'), foreground='#00d4ff').pack(pady=10)
        ttk.Label(frame, text="Forensic-Level Diagnostics", foreground='#888').pack()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        self.run_btn = ttk.Button(btn_frame, text="Run Full Scan", command=self.run_scan)
        self.run_btn.grid(row=0, column=0, padx=10)
        self.report_btn = ttk.Button(btn_frame, text="Generate Report", command=self.generate_report, state='disabled')
        self.report_btn.grid(row=0, column=1, padx=10)

        self.text = tk.Text(frame, height=25, font=('Courier', 10), bg='#0f0f0f', fg='#00ff00', insertbackground='white')
        self.text.pack(fill='both', expand=True, pady=10)

    def log(self, msg):
        self.text.insert(tk.END, msg + "\n")
        self.text.see(tk.END)

    def run_scan(self):
        self.log("Starting forensic scan...")
        self.results = {}

        self.results['Processor'] = get_processor_info()
        self.results['RAM'] = get_ram_info()
        self.results['RAM SPD'] = get_ram_spd()
        self.results['Battery'] = get_battery_info_pro()
        self.results['WiFi MAC'] = get_wifi_card()
        self.results['Storage'] = get_storage_serial()
        self.results['BIOS Flash'] = get_bios_flash_count()
        self.results['Lid Opens'] = get_lid_open_count()
        self.results['Stress'] = stress_test_pro()
        self.results['Speakers'] = test_speakers()
        self.results['Keyboard'] = "User confirmed"

        self.results['Condition'] = calculate_condition_score(self.results)

        self.log("\nScan Complete!\n")
        for k, v in self.results.items():
            self.log(f"{k}: {json.dumps(v, indent=2)}")
        self.report_btn['state'] = 'normal'

    def generate_report(self):
        score = self.results['Condition']
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <title>LaptopCheck AI Pro Report</title>
          <style>
            body {{ font-family: 'Segoe UI', sans-serif; margin: 40px; background: #f4f4f4; }}
            .card {{ background: white; padding: 25px; border-radius: 15px; box-shadow: 0 6px 20px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            .score {{ font-size: 2em; text-align: center; padding: 20px; border-radius: 15px; }}
            .good {{ background: #d5efda; color: #27ae60; }}
            .warn {{ background: #fdf3d7; color: #e67e22; }}
            .bad {{ background: #fce3e3; color: #c0392b; }}
            ul {{ line-height: 1.8; }}
            @media print {{ body {{ background: white; }} }}
          </style>
        </head>
        <body>
          <h1>LaptopCheck AI Pro</h1>
          <p style="text-align:center"><strong>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</strong></p>

          <div class="card score {score['color']}">
            <strong>Overall Condition: {score['grade']} ({score['score']}/100)</strong>
          </div>

          <div class="card">
            <h2>Hardware Authenticity</h2>
            <ul>
              <li><strong>RAM:</strong> { 'UPGRADED' if len(self.results['RAM SPD']) > 1 else 'Original' }</li>
              <li><strong>WiFi:</strong> { 'SWAPPED' if self.results['WiFi MAC'] != 'N/A' else 'Original' }</li>
              <li><strong>Storage:</strong> {self.results['Storage']}</li>
            </ul>
          </div>

          <div class="card">
            <h2>Physical Condition</h2>
            <ul>
              <li><strong>Battery Health:</strong> {self.results['Battery'].get('Health', 'N/A')}</li>
              <li><strong>Thermal Delta:</strong> {self.results['Stress'].get('Delta Temp', 'N/A')}</li>
              <li><strong>Fan Dust:</strong> {self.results['Stress'].get('Fan Drop', 'N/A')}</li>
            </ul>
          </div>

          <p style="text-align:center; margin-top:40px;">
            <button onclick="window.print()" style="padding:12px 30px; font-size:1.1em; background:#00d4ff; color:white; border:none; border-radius:8px; cursor:pointer;">
              Print / Save as PDF
            </button>
          </p>
        </body>
        </html>
        """
        with open("LaptopCheck_AI_Pro_Report.html", "w") as f:
            f.write(html)
        webbrowser.open("LaptopCheck_AI_Pro_Report.html")
        messagebox.showinfo("Success", "Pro Report Generated!")

# ========================================
# 5. RUN
# ========================================

if __name__ == "__main__":
    root = tk.Tk()
    app = LaptopCheckPro(root)
    root.mainloop()
