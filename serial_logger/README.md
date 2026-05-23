# Serial Logger
##Description
This tools allows you to read from the serial port and save it to a csv file, while still allowing to read some other messages.
The way this works it that you wrap the text you want to send to the file inside "<" and ">".

```
<abcdefej> -> abcdefej
```

Anything that is outside "<" ">" will still be printed to the console to help with debugging.

## Dependencies
- Python 3.8 or newer
- pyserial

Install dependencies:

```bash
pip install pyserial
```

## Run

From the script directory, execute:

```bash
python serial_logger.py
```
From here, a startup menu will appear, which will gide you into using it.

If the script accepts serial port and baud rate arguments, use:

```bash
python serial_logger.py COM3 9600
```
