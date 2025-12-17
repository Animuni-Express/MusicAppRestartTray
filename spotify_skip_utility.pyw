import os
import sys
import time
import threading
import subprocess

import pystray
from pystray import MenuItem as Item, Menu as Menu
from PIL import Image, ImageDraw

try:
    import psutil
    PSUTIL_AVAILABLE = True
except Exception:
    PSUTIL_AVAILABLE = False


class SpotifyInstantRestartTray:
    SPOTIFY_EXE = r"C:\Users\anike\AppData\Roaming\Spotify\Spotify.exe"

    def __init__(self):
        if sys.platform != "win32":
            raise RuntimeError("Windows only.")

        self.restart_mode = "hard"     # hard | graceful
        self.start_method = "exe"      # exe | uri

        self._hard_kill_sleep_s = 0.03
        self._graceful_timeout_s = 0.75

        self._lock = threading.Lock()
        self._cooldown_s = 0.20
        self._last_restart_ts = 0.0

        # Avoid console flashes for subprocess calls where possible. [web:217]
        self._creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    # ---------- icon ----------
    def create_icon(self):
        sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        images = {}
        for w, h in sizes:
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)

            pad = max(1, w // 16)
            d.ellipse([pad, pad, w - pad - 1, h - pad - 1], fill=(25, 180, 85, 255))

            arc_pad = max(2, w // 7)
            box = [arc_pad, arc_pad, w - arc_pad - 1, h - arc_pad - 1]
            thickness = max(2, w // 12)
            d.arc(box, start=50, end=325, fill=(255, 255, 255, 235), width=thickness)

            ax = int(w * 0.73)
            ay = int(h * 0.30)
            s = max(3, w // 8)
            d.polygon([(ax, ay), (ax + s, ay + s // 2), (ax + s // 3, ay + s)],
                      fill=(255, 255, 255, 235))

            images[(w, h)] = img

        images[(64, 64)].info["sizes"] = images
        return images[(64, 64)]

    # ---------- helpers ----------
    def _popen_quiet(self, args):
        subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=self._creationflags
        )

    def _is_spotify_running(self) -> bool:
        if PSUTIL_AVAILABLE:
            try:
                for p in psutil.process_iter(["name"]):
                    name = (p.info.get("name") or "").lower()
                    if name == "spotify.exe" or name.startswith("spotify"):
                        return True
            except Exception:
                pass

        r = subprocess.run(
            'tasklist /fi "imagename eq spotify.exe"',
            shell=True, capture_output=True, text=True,
            creationflags=self._creationflags
        )
        return "spotify.exe" in (r.stdout or "").lower()

    def _wait_not_running_fast(self, timeout_s=0.5):
        # Short bounded wait to reduce relaunch races without feeling slow. [web:177]
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            if not self._is_spotify_running():
                return True
            time.sleep(0.03)
        return False

    # ---------- kill ----------
    def _kill_hard(self):
        # /t kills child processes too. [web:177]
        subprocess.run("taskkill /f /t /im spotify.exe >nul 2>&1", shell=True,
                       creationflags=self._creationflags)
        subprocess.run("taskkill /f /t /im spotifywebhelper.exe >nul 2>&1", shell=True,
                       creationflags=self._creationflags)
        subprocess.run("taskkill /f /t /im spotify* >nul 2>&1", shell=True,
                       creationflags=self._creationflags)
        time.sleep(self._hard_kill_sleep_s)
        self._wait_not_running_fast(timeout_s=0.5)

    def _kill_graceful(self):
        if not PSUTIL_AVAILABLE:
            self._kill_hard()
            return

        procs = []
        for p in psutil.process_iter(["name"]):
            name = (p.info.get("name") or "").lower()
            if name == "spotify.exe" or name.startswith("spotify"):
                procs.append(p)

        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass

        # terminate -> wait_procs -> kill survivors. [web:13]
        try:
            _, alive = psutil.wait_procs(procs, timeout=self._graceful_timeout_s)
        except Exception:
            alive = procs

        for p in alive:
            try:
                p.kill()
            except Exception:
                pass

        self._wait_not_running_fast(timeout_s=0.5)

    # ---------- start ----------
    def _start_exe(self):
        if os.path.isfile(self.SPOTIFY_EXE):
            self._popen_quiet([self.SPOTIFY_EXE])
        else:
            self._start_uri()

    def _start_uri(self):
        self._popen_quiet(["cmd", "/c", "start", "", "spotify:"])

    def _start_spotify(self):
        if self.start_method == "exe":
            self._start_exe()
        else:
            self._start_uri()

    # ---------- main action ----------
    def restart_now(self):
        now = time.time()
        if now - self._last_restart_ts < self._cooldown_s:
            return
        self._last_restart_ts = now

        if not self._lock.acquire(blocking=False):
            return
        try:
            if self.restart_mode == "graceful":
                self._kill_graceful()
            else:
                self._kill_hard()

            self._start_spotify()
        finally:
            self._lock.release()

    # ---------- tray callbacks ----------
    def cb_restart(self, icon, item=None):
        threading.Thread(target=self.restart_now, daemon=True).start()

    def cb_set_restart_mode(self, mode):
        def _inner(icon, item=None):
            self.restart_mode = mode
            icon.update_menu()
        return _inner

    def cb_set_start_method(self, method):
        def _inner(icon, item=None):
            self.start_method = method
            icon.update_menu()
        return _inner

    def cb_quit(self, icon, item=None):
        icon.stop()
        os._exit(0)

    # ---------- run ----------
    def run(self):
        restart_options = Menu(
            Item("Hard (fastest)", self.cb_set_restart_mode("hard"),
                 radio=True, checked=lambda item: self.restart_mode == "hard"),
            Item("Graceful (safer)", self.cb_set_restart_mode("graceful"),
                 radio=True, checked=lambda item: self.restart_mode == "graceful"),
        )

        start_methods = Menu(
            Item("EXE (classic)", self.cb_set_start_method("exe"),
                 radio=True, checked=lambda item: self.start_method == "exe"),
            Item("URI (spotify:)", self.cb_set_start_method("uri"),
                 radio=True, checked=lambda item: self.start_method == "uri"),
        )

        menu = Menu(
            Item("Restart now", self.cb_restart, default=True),
            Item("Restart options", restart_options),

            Menu.SEPARATOR,  # supported separator [web:11][web:61]

            Item("Start method", start_methods),

            Menu.SEPARATOR,

            Item("Quit", self.cb_quit),
        )

        icon = pystray.Icon(
            "spotify_instant_restart",
            self.create_icon(),
            "Spotify Instant Restart",
            menu=menu,
        )
        icon.run()


if __name__ == "__main__":
    SpotifyInstantRestartTray().run()



