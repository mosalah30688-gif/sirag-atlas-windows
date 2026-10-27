import json
import os
import shutil
import subprocess
import sys
import threading
import datetime
from pathlib import Path


def resource_path(rel_path: str) -> str:
    """Resolve bundled asset path in both source mode and PyInstaller AppImage binary."""
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    return os.path.join(base, rel_path)


def open_external_url(url: str) -> bool:
    """
    Reliably open an external URL in the user's default system browser on Windows 10/11
    (via native Win32 ShellExecute / os.startfile) or Linux.
    """
    if not url:
        return False

    if sys.platform == "win32":
        try:
            os.startfile(url)
            return True
        except Exception:
            import webbrowser
            return webbrowser.open(url)

    clean_env = os.environ.copy()

    # Restore original host LD_LIBRARY_PATH (saved by AppRun before mounting bundled libs)
    orig_ld = clean_env.pop("SIRAG_HOST_LD_LIBRARY_PATH", None)
    if orig_ld:
        clean_env["LD_LIBRARY_PATH"] = orig_ld
    else:
        clean_env.pop("LD_LIBRARY_PATH", None)

    for var in (
        "LD_PRELOAD",
        "QT_PLUGIN_PATH",
        "QT_QPA_PLATFORM_PLUGIN_PATH",
        "QML2_IMPORT_PATH",
        "PYTHONPATH",
        "PYTHONHOME",
        "GIO_MODULE_DIR",
        "GSETTINGS_SCHEMA_DIR",
        "GTK_PATH",
        "GTK_EXE_PREFIX",
        "GTK_DATA_PREFIX",
        "GDK_PIXBUF_MODULE_FILE",
        "GDK_PIXBUF_MODULEDIR",
        "PERLLIB",
    ):
        clean_env.pop(var, None)

    # Ensure XDG_DATA_DIRS doesn't point exclusively inside temporary /tmp/.mount_* AppImage dir
    xdg_dirs = clean_env.get("XDG_DATA_DIRS", "")
    if ".mount_" in xdg_dirs:
        kept = [p for p in xdg_dirs.split(":") if p and ".mount_" not in p]
        clean_env["XDG_DATA_DIRS"] = ":".join(kept) if kept else "/usr/local/share:/usr/share"

    def _launch_runner():
        candidates = []
        if shutil.which("xdg-open"):
            candidates.append(["xdg-open", url])
        if shutil.which("gio"):
            candidates.append(["gio", "open", url])
        for br in (
            "x-www-browser",
            "sensible-browser",
            "google-chrome",
            "google-chrome-stable",
            "brave-browser",
            "chromium",
            "chromium-browser",
            "firefox",
            "microsoft-edge",
            "vivaldi",
            "falkon",
            "konqueror",
            "epiphany",
        ):
            exe = shutil.which(br)
            if exe:
                candidates.append([exe, url])

        for cmd in candidates:
            try:
                proc = subprocess.Popen(
                    cmd,
                    env=clean_env,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                # For short-lived openers (xdg-open / gio), verify they didn't immediately exit with error
                if os.path.basename(cmd[0]) in ("xdg-open", "gio"):
                    try:
                        rc = proc.wait(timeout=2.5)
                        if rc == 0:
                            return
                        continue
                    except subprocess.TimeoutExpired:
                        return
                return
            except Exception:
                continue

    threading.Thread(target=_launch_runner, daemon=True).start()
    return True


HIJRI_MONTHS_AR = [
    "محرّم", "صفر", "ربيع الأول", "ربيع الآخر",
    "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان",
    "رمضان", "شوّال", "ذو القعدة", "ذو الحجة"
]


def gregorian_to_hijri(dt: datetime.date = None):
    """Accurate tabular/astronomical Hijri conversion returning (day, month_num, year, formatted_ar)."""
    if dt is None:
        dt = datetime.date.today()
    jd = dt.toordinal() + 1721425
    l = jd - 1948440 + 10632
    n = (l - 1) // 10631
    l = l - 10631 * n + 354
    j = ((10985 - l) // 5316) * ((50 * l) // 17719) + (l // 5670) * ((43 * l) // 15238)
    l = l - ((30 - j) // 15) * ((17719 * j) // 50) - (j // 16) * ((15238 * j) // 43) + 29
    month = (24 * l) // 709
    day = l - (709 * month) // 24
    year = 30 * n + j - 30
    month = max(1, min(12, month))
    month_name = HIJRI_MONTHS_AR[month - 1]
    return day, month, year, f"{day} {month_name} {year} هـ"


class DataRepository:
    """Loads all 11 authenticated Prophetic Seerah datasets offline from bundled JSON."""

    def __init__(self):
        self.events = self._load_json("events.json")
        self.hijrah_data = self._load_json("hijrah_data.json")
        self.battles = self._load_json("battles.json")
        self.sanctuaries = self._load_json("sanctuaries.json")
        self.scenarios = self._load_json("scenarios.json")
        self.companions = self._load_json("companions.json")
        self.lineage = self._load_json("lineage.json")
        self.diwan_lexicon = self._load_json("diwan_lexicon.json")
        self.guidance = self._load_json("guidance.json")
        self.relics = self._load_json("relics.json")
        self.khatmah_days = self._load_json("khatmah_days.json")

    def _load_json(self, filename: str):
        p = resource_path(os.path.join("assets", "data", filename))
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)


class UserState:
    """Persists explorer mastery, bookmarks, Khatmah councils, quiz medals & preferences."""

    def __init__(self, repo: DataRepository):
        self.repo = repo
        if sys.platform == "win32":
            appdata = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
            self.config_dir = Path(appdata) / "SiragAtlasSeerah"
        else:
            self.config_dir = Path.home() / ".config" / "sirag-atlas"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.config_dir / "user_state.json"
        self.data = self._load()
        self._listeners = []

    def _default_state(self):
        return {
            "theme": "night",
            "font_scale": "normal",
            "ambiance_type": "desert",
            "auto_update_notify": True,
            "reader_name": "",
            "stations": [],
            "battles": [],
            "scenarios": [],
            "companions": [],
            "relics": [],
            "bookmarks": [],
            "sunnah_done": [],
            "khatmah_done": [],
            "quiz_solved": []
        }

    def _load(self):
        base = self._default_state()
        if self.state_file.exists():
            try:
                loaded = json.loads(self.state_file.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    base.update(loaded)
            except Exception:
                pass
        return base

    def save(self):
        try:
            self.state_file.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass
        for cb in self._listeners:
            try:
                cb()
            except Exception:
                pass

    def on_change(self, callback):
        self._listeners.append(callback)

    def add_unique(self, key: str, item_id):
        lst = self.data.setdefault(key, [])
        if item_id not in lst:
            lst.append(item_id)
            self.save()

    def toggle_in_list(self, key: str, item_id) -> bool:
        lst = self.data.setdefault(key, [])
        if item_id in lst:
            lst.remove(item_id)
            present = False
        else:
            lst.append(item_id)
            present = True
        self.save()
        return present

    def mastery_stats(self):
        total = (
            len(self.repo.events)
            + len(self.repo.battles)
            + len(self.repo.scenarios)
            + len(self.repo.companions)
            + len(self.repo.relics)
        )
        done = (
            len(self.data.get("stations", []))
            + len(self.data.get("battles", []))
            + len(self.data.get("scenarios", []))
            + len(self.data.get("companions", []))
            + len(self.data.get("relics", []))
        )
        pct = min(100, round((done / max(1, total)) * 100))
        return pct, done, total
