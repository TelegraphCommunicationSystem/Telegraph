import urequests, machine, time, os
from manager import wifi_manager

# Auslagern in Config
REPO_OWNER = "TelegraphCommunicationSystem"
REPO_NAME = "Telegraph"

# Version wird aus main/config/version.txt gelesen (Branch "main")
VERSION_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/refs/heads/main/config/version.txt"

# Lokaler Pfad im Projekt (nicht "../config/...")
LOCAL_VERSION_FILE = "config/version.txt"


def connect_wifi():
    wlan = wifi_manager.get_connection()
    if wlan is None:
        print("Could not initialize the network connection.")
        return False
    if wlan.isconnected():
        print("Network already connected.")
        return True
    return False


def get_local_version():
    try:
        with open(LOCAL_VERSION_FILE, "r") as f:
            return f.read().strip()
    except Exception:
        return "0.0"


def get_remote_version():
    r = None
    try:
        r = urequests.get(VERSION_URL)
        if r.status_code == 200:
            version = (r.text or "").strip()
            print(f"Serverversion: {version}")
            return version
        print("Fehler beim Abrufen der Serverversion, Status:", r.status_code)
        return None
    except Exception as e:
        print("Fehler beim Abrufen der Serverversion:", e)
        return None
    finally:
        try:
            if r is not None:
                r.close()
        except Exception:
            pass


def _ensure_parent_dirs(path: str):
    if "/" not in path:
        return
    parts = path.split("/")[:-1]
    cur = ""
    for p in parts:
        cur = f"{cur}/{p}" if cur else p
        try:
            os.stat(cur)
        except OSError:
            try:
                os.mkdir(cur)
            except OSError:
                pass


def _remove_file_if_exists(path: str) -> bool:
    try:
        os.remove(path)
        print(f"{path} gelöscht.")
        return True
    except OSError:
        # nicht vorhanden oder nicht löschbar -> für "d" behandeln wir "nicht vorhanden" als ok
        print(f"{path} nicht vorhanden (ok).")
        return True
    except Exception as e:
        print(f"Fehler beim Löschen von {path}:", e)
        return False


def get_update_plan(remote_version: str):
    """
    Lädt update.txt aus dem Release und parst Zeilen im Format:
      <path>,<action>
    action in {c,u,d}
    """
    url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/{remote_version}/update.txt"
    r = None
    try:
        r = urequests.get(url)
        if r.status_code != 200:
            print("Fehler beim Laden der update.txt, Status:", r.status_code)
            return []

        text = r.text or ""
        plan = []
        for raw_line in text.replace("\r", "\n").split("\n"):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            # akzeptiere sowohl "a,b" als auch "a b"
            if "," in line:
                left, right = line.split(",", 1)
            else:
                parts = line.split()
                left = parts[0]
                right = parts[1] if len(parts) > 1 else "u"

            path = (left or "").strip()
            action = (right or "").strip().lower()

            if not path:
                continue
            if action not in ("c", "u", "d"):
                print(f"Ungültige Aktion in update.txt: {line} (erlaubt: c,u,d)")
                return []

            plan.append((path, action))

        return plan
    except Exception as e:
        print("Fehler beim Abrufen/Parsen der update.txt:", e)
        return []
    finally:
        try:
            if r is not None:
                r.close()
        except Exception:
            pass


def download_file(path: str, remote_version: str) -> bool:
    """
    Lädt die Datei als Release-Asset:
      https://github.com/<owner>/<repo>/releases/download/<version>/<path>
    und schreibt sie lokal (überschreibt/legt an).
    """
    url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/{remote_version}/{path}"
    r = None
    try:
        r = urequests.get(url)
        if r.status_code != 200:
            print(f"Fehler beim Download {path}, Status:", r.status_code)
            return False

        _ensure_parent_dirs(path)
        with open(path, "w") as f:
            f.write(r.text or "")
        print(f"{path} aktualisiert.")
        return True
    except Exception as e:
        print("Fehler beim Download:", e)
        return False
    finally:
        try:
            if r is not None:
                r.close()
        except Exception:
            pass


def apply_update_plan(plan, remote_version: str) -> bool:
    for path, action in plan:
        if action == "d":
            if not _remove_file_if_exists(path):
                return False
            continue

        # c und u: beide überschreiben / erzeugen
        if not download_file(path, remote_version):
            return False

    return True


def check_for_update():
    local_v = get_local_version()
    remote_v = get_remote_version()
    if not remote_v:
        print("Keine Verbindung oder Version nicht gefunden.")
        return

    if remote_v == local_v:
        print("Software ist aktuell.")
        return

    print(f"Neue Version gefunden: {remote_v}")

    plan = get_update_plan(remote_v)
    if not plan:
        print("Kein gültiger Update-Plan in update.txt gefunden – Update wird abgebrochen.")
        return

    if not apply_update_plan(plan, remote_v):
        print("Update abgebrochen (mindestens eine Aktion fehlgeschlagen).")
        return

    _ensure_parent_dirs(LOCAL_VERSION_FILE)
    with open(LOCAL_VERSION_FILE, "w") as f:
        f.write(remote_v)

    print("Update abgeschlossen. Neustart...")
    time.sleep(2)
    machine.reset()


def update_firmware():
    if connect_wifi():
        check_for_update()