"""
Serial Logger — reads sensor data from a serial port and saves it to CSV.

Data format from MCU:
  - Sensor readings wrapped in angle brackets → saved to CSV:  <1,2,3,4,5>
  - Everything else (debug prints, etc.)     → printed to console only

Usage:
  python serial_logger.py
"""

import serial
import serial.tools.list_ports
import threading
import sys
import re
import os
from datetime import datetime

# ──────────────────────────────────────────────
# Globals
# ──────────────────────────────────────────────
ser: serial.Serial | None = None
csv_file = None
running = False
read_thread: threading.Thread | None = None
buffer = ""          # accumulates partial serial data between reads
buffer_lock = threading.Lock()


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def list_ports() -> list[str]:
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]


def print_separator(char="─", width=50):
    print(char * width)


def log(msg: str):
    """Timestamped console print."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


# ──────────────────────────────────────────────
# Serial reader thread
# ──────────────────────────────────────────────
def serial_reader():
    """
    Continuously reads from the serial port.

    Lines that contain <...> patterns have the inner content written to CSV.
    Anything outside angle brackets is printed to the console.
    """
    global buffer, running

    while running:
        try:
            if ser and ser.in_waiting:
                chunk = ser.read(ser.in_waiting).decode("utf-8", errors="replace")
                with buffer_lock:
                    buffer += chunk
                    process_buffer()
        except serial.SerialException as e:
            log(f"Serial error: {e}")
            running = False
            break


def process_buffer():
    """
    Parse whatever is currently in `buffer`.
    Writes CSV data and prints console messages.
    Called inside buffer_lock.
    """
    global buffer

    # We process character by character to correctly handle interleaved text.
    result_console = []
    i = 0

    while i < len(buffer):
        if buffer[i] == "<":
            # Flush any accumulated console text first
            if result_console:
                text = "".join(result_console).strip()
                if text:
                    log(f"MCU » {text}")
                result_console = []

            # Look for the closing '>'
            end = buffer.find(">", i + 1)
            if end == -1:
                # Incomplete packet — keep the rest in the buffer for next read
                buffer = buffer[i:]
                return
            # Extract and write the CSV payload
            payload = buffer[i + 1 : end]
            write_csv(payload)
            i = end + 1

        elif buffer[i] == ">":
            # Stray '>' with no opening '<' — treat as plain text
            result_console.append(buffer[i])
            i += 1

        else:
            result_console.append(buffer[i])
            i += 1

    # Flush remaining console text
    if result_console:
        text = "".join(result_console).strip()
        if text:
            log(f"MCU » {text}")

    buffer = ""  # fully consumed


def write_csv(payload: str):
    """Write a single payload line to the CSV file (no extra newline mangling)."""
    if csv_file and not csv_file.closed:
        csv_file.write(payload + "\n")
        csv_file.flush()
        log(f"CSV ← {payload}")


# ──────────────────────────────────────────────
# Send a custom message to the MCU
# ──────────────────────────────────────────────
def send_message():
    if not ser or not ser.is_open:
        print("  ✖  No active serial connection.")
        return
    msg = input("  Enter message to send: ").strip()
    if msg:
        ser.write((msg + "\n").encode("utf-8"))
        log(f"Sent → {msg}")


# ──────────────────────────────────────────────
# Start / Stop
# ──────────────────────────────────────────────
def start_listening():
    global ser, csv_file, running, read_thread

    # ── Choose port ──────────────────────────
    ports = list_ports()
    if not ports:
        print("  ✖  No serial ports found. Check your connection.")
        return

    print("\n  Available ports:")
    for idx, p in enumerate(ports):
        print(f"    [{idx}] {p}")

    try:
        choice = int(input("  Select port number: "))
        port = ports[choice]
    except (ValueError, IndexError):
        print("  ✖  Invalid selection.")
        return

    # ── Baud rate ────────────────────────────
    baud_input = input("  Baud rate [default 9600]: ").strip()
    baud = int(baud_input) if baud_input.isdigit() else 9600

    # ── CSV file name ─────────────────────────
    default_csv = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_name = input(f"  CSV filename [default: {default_csv}]: ").strip()
    if not csv_name:
        csv_name = default_csv

    # ── Open port & file ─────────────────────
    try:
        ser = serial.Serial(port, baud, timeout=0.05)
    except serial.SerialException as e:
        print(f"  ✖  Could not open {port}: {e}")
        return

    csv_file = open(csv_name, "a", newline="")
    running = True

    read_thread = threading.Thread(target=serial_reader, daemon=True)
    read_thread.start()

    print_separator()
    log(f"Listening on {port} @ {baud} baud  →  {csv_name}")
    print_separator()


def stop_listening():
    global running, ser, csv_file

    running = False
    if read_thread:
        read_thread.join(timeout=2)
    if ser and ser.is_open:
        ser.close()
    if csv_file and not csv_file.closed:
        csv_file.close()
    log("Stopped. Serial port closed and CSV saved.")


# ──────────────────────────────────────────────
# Menu
# ──────────────────────────────────────────────
def menu():
    print_separator("═")
    print("  Serial Logger")
    print_separator("═")

    while True:
        print()
        status = "● RUNNING" if running else "○ IDLE"
        print(f"  Status: {status}")
        print("  [1] Start listening")
        print("  [2] Send message to MCU")
        print("  [3] Stop listening")
        print("  [4] Exit")
        print()

        choice = input("  > ").strip()

        if choice == "1":
            if running:
                print("  Already listening.")
            else:
                start_listening()

        elif choice == "2":
            send_message()

        elif choice == "3":
            if running:
                stop_listening()
            else:
                print("  Not currently listening.")

        elif choice == "4":
            if running:
                stop_listening()
            print("  Goodbye!")
            sys.exit(0)

        else:
            print("  Invalid option, try again.")


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n  Interrupted.")
        if running:
            stop_listening()
        sys.exit(0)
