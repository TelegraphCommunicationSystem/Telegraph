import urequests, machine, time, os
from manager import wifi_manager

#Auslagern in Config
SERVER_BASE = "https://github.com/TelegraphCommunicationSystem/Telegraph"  # URL deines Servers
VERSION_URL = "https://raw.githubusercontent.com/TelegraphCommunicationSystem/Telegraph/refs/heads/main/config/version.txt"
LOCAL_VERSION_FILE = "../config/version.txt"

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
            global REMOTE_VERSION
            REMOTE_VERSION = version
            return version
    except Exception as e:
        print("Fehler beim Abrufen der Serverversion:", e)
    return None

def get_updated_files(remote_version: str):
    """
    Lädt die Dateiliste aus der Release-URL (update.txt) und gibt sie als Liste zurück.
    Format in update.txt: z.B. 'main.py, receiver.py' oder zeilenweise.
    Nicht case-sensitiv: wir normalisieren auf lower-case.
    """
    url = f"https://github.com/TelegraphCommunicationSystem/Telegraph/releases/download/{remote_version}/update.txt"
    try:
        r = urequests.get(url)
        if r.status_code != 200:
            try:
                r.close()
            except:
                pass
            print("Fehler beim Laden der update.txt, Status:", r.status_code)
            return []

        text = r.text or ""
        r.close()

        # akzeptiert: Komma-getrennt und/oder Zeilenumbrüche
        raw_items = []
        for line in text.replace("\r", "\n").split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            raw_items.extend([p.strip() for p in line.split(",")])

        files = []
        seen = set()
        for name in raw_items:
            name = (name or "").strip()
            if not name:
                continue
            name_norm = name.lower()
            if name_norm not in seen:
                seen.add(name_norm)
                files.append(name_norm)

        return files
    except Exception as e:
        print("Fehler beim Abrufen der Updated-Files-Liste:", e)
        return []

def download_file(filename, remote_version):
    raw_url = f"https://github.com/TelegraphCommunicationSystem/Telegraph/blob/{remote_version}"
    try:
        url = raw_url + "/" + filename
        r = urequests.get(url)
        if r.status_code == 200:
            # Extract directory path from filename
            dir_path = "/".join(filename.split("/")[:-1])

            # Check if directory exists, create if it doesn't
            if dir_path and dir_path != "":
                try:
                    os.stat(dir_path)
                except OSError:
                    # Directory doesn't exist, create it (including parent directories)
                    parts = dir_path.split("/")
                    current_path = ""
                    for part in parts:
                        current_path += part
                        try:
                            os.mkdir(current_path)
                        except OSError:
                            pass  # Directory already exists
                        current_path += "/"

            with open(filename, "w") as f:
                f.write(r.text)
            print(f"{filename} aktualisiert.")
        r.close()
    except Exception as e:
        r.close()
        print("Fehler beim Download:", e)

def check_for_update():
    local_v = get_local_version()
    remote_v = get_remote_version()
    if not remote_v:
        print("Keine Verbindung oder Version nicht gefunden.")
        return
    if remote_v != local_v:
        print(f"Neue Version gefunden: {remote_v}")

        files_to_update = get_updated_files(remote_v)
        if not files_to_update:
            print("Keine Dateien in update.txt gefunden – Update wird abgebrochen.")
            return

        for file in files_to_update:
            download_file(file, remote_v)

        with open(LOCAL_VERSION_FILE, "w") as f:
            f.write(remote_v)
        print("Update abgeschlossen. Neustart...")
        time.sleep(2)
        machine.reset()
    else:
        print("Software ist aktuell.")

def update_firmware():
    if connect_wifi():
        check_for_update()