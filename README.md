# 🛠 Tool Launcher

A clean, click-to-run GUI for all your Python scripts.

## Requirements

- Python 3.10+
- `Pillow` *(optional — only needed to display custom images on cards)*

Install Pillow:
```
pip install Pillow
```

## Running

```
python launcher.py
```

## Adding a tool

1. Click **＋ Add Tool** in the top-right corner.
2. Fill in:
   | Field | Required | Notes |
   |---|---|---|
   | **Title** | ✅ | Shown on the card |
   | **Description** | — | Short summary under the title |
   | **Script Path** | ✅ | Relative to `launcher.py`. Use *Browse* to pick the file. |
   | **Image Path** | — | PNG/JPG thumbnail for the card. Use *Browse* to pick the file. |
3. Click **Save ✓**.

## File structure

All paths in `tools.json` are **relative to** the folder where `launcher.py` lives.
Keep your scripts in the same folder or any sub-folder:

```
launcher.py          ← run this
tools.json           ← auto-created, stores all tool info
my_scripts/
  script_1/
    script.py
    README.md
    img.jpg
  script_2/
    other.py
    README.md
    img.png

```

## Editing / removing a tool

- Click **✎** on a card to edit its details.
- Click **✕** on a card to remove it from the launcher (the script itself is **not** deleted).

## tools.json format

```json
[
  {
    "id": "auto-generated-uuid",
    "title": "Rename Files",
    "description": "Bulk rename files in a folder using a pattern.",
    "script_path": "my_scripts/rename_files.py",
    "image_path":  "my_scripts/images/rename.png"
  }
]
```
