import urequests, machine, time
from manager import wifi_manager

SERVER_BASE = "https://github.com/TelegraphCommunicationSystem/Telegraph/archive/refs/tags/0.0.1.zip"  # URL deines Servers
VERSION_URL = "https://raw.githubusercontent.com/TelegraphCommunicationSystem/Telegraph/refs/heads/main/config/version.txt"
LOCAL_VERSION_FILE = "config/version.txt"

def connect_wifi():
    wlan = wifi_manager.get_connection()
    if wlan is None:
        print("Could not initialize the network connection.")
        return False
    print(wlan)
    if wlan.isconnected():
        print("Network already connected.")
        return True

def get_local_version():
    try:
        with open(LOCAL_VERSION_FILE, "r") as f:
            return f.read().strip()
    except:
        return "0.0"

def get_remote_version():
    try:
        r = urequests.get(VERSION_URL)
        if r.status_code == 200:
            version = r.text.strip()
            r.close()
            print(f"Serverversion: {version}")
            return version
    except Exception as e:
        print("Fehler beim Abrufen der Serverversion:", e)
    return None

def download_file(filename):
    try:
        url = SERVER_BASE + "/" + filename
        r = urequests.get(url)
        if r.status_code == 200:
            with open(filename, "w") as f:
                f.write(r.text)
            print(f"{filename} aktualisiert.")
        r.close()
    except Exception as e:
        print("Fehler beim Download:", e)

def check_for_update():
    local_v = get_local_version()
    remote_v = get_remote_version()
    if not remote_v:
        print("Keine Verbindung oder Version nicht gefunden.")
        return
    if remote_v != local_v:
        print(f"Neue Version gefunden: {remote_v}")
        for file in ["main.py", "utils.py"]:  # Dateien, die aktualisiert werden sollen
            download_file(file)
        with open(LOCAL_VERSION_FILE, "w") as f:
            f.write(remote_v)
        print("Update abgeschlossen. Neustart...")
        time.sleep(2)
        machine.reset()
    else:
        print("Software ist aktuell.")

if connect_wifi():
    check_for_update()

# Wenn kein Update, dann normales Starten
#import main
