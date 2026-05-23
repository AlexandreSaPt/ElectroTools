# CSV Visualizer

A small interactive Python tool for exploring serial logger CSV files.

## What it does

The script asks you to pick a CSV file, loads the file, reads the header row, and shows the detected columns.
You then choose which columns to display and group them into one or more subplots.
Each confirmed group becomes a separate subplot, and the resulting chart is shown with synchronized zoom/pan and a shared vertical crosshair.

## Features

- File picker dialog for selecting a CSV file
- Reads CSV headers and shows available variables
- Build ordered plot groups from selected columns
- One subplot per confirmed group
- Shared X axis across subplots for synchronized zooming/panning
- Hover support with a vertical crosshair and per-plot annotations

## Dependencies

- Python 3.8+ (or a compatible Python 3 version)
- pandas
- matplotlib

Install dependencies with:

```bash
pip install pandas matplotlib
```

## How to run

From the script folder:

```bash
python csv_visualizer.py
```

Then select a CSV file in the file dialog, choose columns, confirm groups, and press `PLOT`.

## Notes

- The script expects a CSV file with a header row.
- It inserts an internal `__index__` column for the X axis if no timestamp column is provided.
- If a CSV already contains a column named `__index__`, that may conflict with the internal index column.

## Known issues

- The vertical crosshair can be extremely slow on large datasets.
- Very large CSV files may also produce sluggish interaction due to the current drawing and event handling.

## Suggested additions

- A note on the expected CSV format
- Example usage with sample CSV headers
- License information if you want to share the project publicly
