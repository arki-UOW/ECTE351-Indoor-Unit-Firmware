"""Minimal boot-time setup for the ECTE351 indoor unit."""

import gc
import time


gc.collect()

# Development escape window.
# The application starts automatically via main.py, but mpremote occasionally
# struggles to interrupt immediately once Wi-Fi/MQTT activity begins. This
# short delay provides a predictable Ctrl+C window after reset so files can be
# updated without repeatedly power-cycling the ESP32-S3.
print("[BOOT] Starting application in 3 seconds - Ctrl+C for REPL")
time.sleep(3)
