Instant Restart Tray (Windows)  
==============================

A tiny Windows system-tray utility that can quickly restart Spotify Desktop when it freezes or needs a fast relaunch. It runs in the tray and provides a one-click “Restart now” action plus restart and launch method options.[1][2]

Not affiliated with Spotify. “Spotify” is a trademark of Spotify AB.[3]

Features  
--------

- System tray icon with a right-click menu.[2]
- Restart now (default action in the menu).[4]
- Restart options:  
  - Hard (fastest): uses Windows `taskkill` to end Spotify quickly (including child processes).[5]
  - Graceful (safer): attempts a clean terminate first (requires `psutil`).[6]
- Start methods:  
  - EXE (classic installer path)  
  - URI (`spotify:`)  

Requirements  
------------

- Windows (the script is Windows-specific).  
- Python 3.9+ recommended.  
- Python packages:  
  - pystray[7]
  - Pillow[8]
  - psutil (optional, only for “Graceful”)[9]

Installation (from source)  
--------------------------

1) Clone the repo, then from the repo root run:[10]
python -m pip install -r requirements.txt

2) Run the app:  
python app.py

Configuration  
-------------

Spotify EXE path (classic installer)  
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This project assumes the classic installer. Update the constant in `app.py` if your path differs:

SPOTIFY_EXE = r"C:\Users\anike\AppData\Roaming\Spotify\Spotify.exe"

Usage  
-----

1) Start the app (`python app.py`).  
2) A tray icon appears.  
3) Right-click the tray icon to open the menu.[2]
4) Choose:  
- Restart now to restart Spotify immediately.  
- Restart options → Hard or Graceful.[5][6]
- Start method → EXE or URI.  

Which options should I use?  
---------------------------

- Use Hard (fastest) for the snappiest restart.[5]
- Use Graceful (safer) if you want a cleaner shutdown (requires `psutil`).[6]
- Use EXE for classic installs; switch to URI if EXE launch fails.  

Packaging as an EXE (optional)  
------------------------------

1) Install PyInstaller:[11]
python -m pip install pyinstaller

2) Build a Windows executable (no console window):[11]
pyinstaller --onefile --windowed --name "InstantRestartTray" app.py

Output will be in:  
dist\InstantRestartTray.exe

Troubleshooting  
---------------

Graceful mode does nothing  
~~~~~~~~~~~~~~~~~~~~~~~~~

Install psutil:[9]
python -m pip install psutil

Restart doesn’t relaunch Spotify  
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Confirm the `SPOTIFY_EXE` path exists.  
- Switch Start method to URI (`spotify:`) from the tray menu.  

License  
-------

Add a LICENSE file (MIT is common). A license clarifies how others can use/modify/share the code.[12][13]

[1](https://realpython.com/readme-python-project/)
[2](https://pythonhosted.org/pystray/)
[3](https://developer.spotify.com/documentation/design)
[4](https://pystray.readthedocs.io/en/latest/reference.html)
[5](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/taskkill)
[6](https://psutil.readthedocs.io/en/latest/index.html?highlight=terminate)
[7](https://pypi.org/project/pystray/)
[8](https://www.geeksforgeeks.org/python/create-a-responsive-system-tray-icon-using-python-pystray/)
[9](https://pypi.org/project/psutil/)
[10](https://www.geeksforgeeks.org/python/how-to-install-python-packages-with-requirements-txt/)
[11](https://pyinstaller.org/en/stable/usage.html)
[12](https://www.welcometothejungle.com/en/articles/btc-readme-documentation-best-practices)
[13](https://docs.python-guide.org/writing/structure/)
