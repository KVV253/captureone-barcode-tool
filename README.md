````markdown
# Capture One Barcode Tool

A small utility that augments **Capture One Enterprise** by inserting a barcode image into the next photo captured during a tethered session.

## Components
- **Python barcode daemon** (`main.py`) — listens on a UNIX socket and produces a JPEG barcode overlay in the  Capture folder.
- **AppleScript event handler** (`Capture One Scripts/Background Scripts/on_barcode_capture_event.scpt`) — invoked by Capture One when a barcode is scanned.
- **Service scripts** (`Capture One Scripts/service/*.scpt`) — start/stop the daemon and open logs from the macOS 
  Scripts menu.

## Features
- Generates **Code-128** barcodes using `python-barcode`.
- Saves barcode images (default canvas ~**370×260 px** JPEG) with consistent names in the Capture folder.
- Communicates via a **UNIX domain socket** for minimal latency.
- AppleScript helpers to **start/stop** the daemon and **tail** its log.

## Requirements
- macOS with **Capture One Enterprise**.
- **Python 3.8+** (tested with 3.12).
- Packages listed in `requirements.txt` (`python-barcode`, `Pillow`, `piexif`, etc.).
- Optional: **PyInstaller** to produce a standalone `BarcodeDaemon` binary.

## Installation

### 1) Install Python dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
````

### 2) Build the daemon (optional but recommended)

To integrate with the AppleScripts, build a single-file binary:

```bash
pip install pyinstaller
pyinstaller \
  --name BarcodeDaemon \
  --onefile \
  --console \
  --add-data "DejaVuSans-Bold.ttf:." \
  --hidden-import=pkg_resources.py2_warn \
  --hidden-import=jaraco.text \
  main.py
```

Copy the generated binary to:

```
~/Library/Scripts/Capture One Scripts/Background Scripts/BarcodeDaemon
```

> You may run `python main.py` directly, but the AppleScripts expect the binary path above.

### 3) Install AppleScripts

Copy the **Capture One Scripts** folder from this repository to:

```
~/Library/Scripts/Capture One Scripts/
    ├── Background Scripts/
    │   └── BarcodeDaemon
    │   └── on_barcode_capture_event.scpt
    └── service/
        ├── start_daemon.scpt
        ├── stop_daemon.scpt
        └── open_log.scpt
```

## Capture One setup

1. **Configure the barcode scanner**
   [https://support.captureone.com/hc/en-us/articles/360002675898-Configuring-the-Barcode-scanner-Studio-for-Enterprise](https://support.captureone.com/hc/en-us/articles/360002675898-Configuring-the-Barcode-scanner-Studio-for-Enterprise)

2. **Add the Barcode tool**
   [https://support.captureone.com/hc/en-us/articles/360002663277-Barcode-Scanner-Tool-Studio-for-Enterprise?isTrial=false\&language=ru\&remainingTrial=0\&rk=\&tool=barcode\&variant=7\&version=16.6.3](https://support.captureone.com/hc/en-us/articles/360002663277-Barcode-Scanner-Tool-Studio-for-Enterprise?isTrial=false&language=ru&remainingTrial=0&rk=&tool=barcode&variant=7&version=16.6.3)

3. **Next Capture Naming**
   Use a pattern like `name_0001` (img_sequential сounter), so the generated barcode image matches the upcoming shot name.

## Usage

### Start the daemon

From the macOS menu bar **Script** icon choose:
**Capture One Scripts → service → start\_daemon**.
The script launches `BarcodeDaemon` and waits for the socket **/tmp/barcode\_daemon\_socket** to appear.

### Scan a barcode in Capture One

* `on_barcode_capture_event.scpt` fires and ensures the daemon is running.
* It sends a line to the socket:

  ```
  <folder_path>,<barcode_value>,<next_capture_name>
  ```
* The Python daemon generates a JPEG barcode in the Capture folder and the next capture proceeds with the expected name/counter.

### Stop the daemon

**Capture One Scripts → service → stop\_daemon** sends the `kill process` command and waits for shutdown.

### Watch logs (optional)

**Capture One Scripts → service → open\_log** tails `/tmp/barcode_daemon.log` in Terminal.

## Test without a physical scanner

If you don’t have a scanner, simulate “F12 → CODE → F12” as keyboard input focused in Capture One (the Barcode tool input must be active).

> macOS will prompt for **Accessibility** permission for Python.

```python
# mini_script_scan.py
# Simulate: F12 0123456789 F12
# pip install pyautogui
import time
import pyautogui

time.sleep(2)  # switch focus to Capture One
pyautogui.press('f12')
pyautogui.write('0123456789')
pyautogui.press('f12')
```

Run:

```bash
pip install pyautogui
python mini_script_scan.py
```

## Direct socket test (optional)

Send a message directly to the daemon (replace paths/text accordingly):

```bash
printf "%s" "/Users/you/Capture/Capture,0123456789,job_0001" | nc -U /tmp/barcode_daemon_socket -w 2
```

A file `job_0001.jpg` should appear in the Capture folder.

## Directory structure

```
captureone-barcode-tool/
├── main.py                     # Python daemon
├── requirements.txt            # Python dependencies
├── DejaVuSans-Bold.ttf         # Font used by barcode writer
├── Capture One Scripts/        # AppleScript helpers
│   ├── Background Scripts/
│   │   └── BarcodeDaemon
│   │   └── on_barcode_capture_event.scpt
│   └── service/
│       ├── start_daemon.scpt
│       ├── stop_daemon.scpt
│       └── open_log.scpt
└── LICENSE                     # MIT License
```

## Logging & Troubleshooting

* Daemon log: **/tmp/barcode\_daemon.log**
* Socket file: **/tmp/barcode\_daemon\_socket** (remove stale socket if the daemon crashes).
* Ensure the `BarcodeDaemon` binary is executable:

  ```bash
  chmod +x ~/Library/Scripts/Capture\ One\ Scripts/Background\ Scripts/BarcodeDaemon
  ```

## License

This project is released under the **MIT License**. Feel free to use, modify, and distribute.

## Acknowledgments

* **python-barcode** for barcode generation.
* **Pillow** for image processing.
* **Capture One Enterprise** for AppleScript event hooks.

*Happy shooting!*
