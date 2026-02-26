# Calibration System

## Overview

The calibration system loads historical estimation data from GeekyAnts Excel exports to improve estimation accuracy.

## Architecture

```
Excel Files (multi-sheet)
    ↓
CSVCalibrationLoader (scan all sheets)
    ↓
Aggregated Data (weighted averages)
    ↓
CalibrationEngine (in-memory lookup)
    ↓
EstimationAgent (applies calibration)
```

## Loading Process

**When:** Once at FastAPI startup (lifespan event)

**Where:** `app/data/calibration/` folder

**What:** All `.xlsx` and `.xls` files

**How:**
1. Scan folder for Excel files
2. For each file, iterate ALL sheets
3. Filter sheets with feature + hours columns
4. Extract feature-hour pairs
5. Aggregate using weighted average
6. Load into CalibrationEngine

## Sheet Processing Rules

**Processed if sheet contains:**
- Feature column: "Name", "Module Name", "Feature", "Module"
- Hours data: "Total Hours" OR component columns (Web Mobile, Backend, etc.)

**Skipped if:**
- Sheet is empty
- No feature or hours columns found
- Row name contains: total, subtotal, summary

## Calibration Application

**Rule:** Only override base estimate when `sample_size >= 2`

**Example:**
```python
# Base estimate: 72 hours
# Calibration data: 65 hours (n=3)
# Final: 65 hours (calibrated)

# Base estimate: 72 hours  
# Calibration data: 80 hours (n=1)
# Final: 72 hours (not enough samples)
```

## Performance

- **Load time:** ~2 seconds for 7 files (even with corrupted files)
- **Lookup time:** O(1) - in-memory dict
- **Request impact:** Zero (loaded once at startup)

## Current Status

✓ Loaded 60 unique features from calibration data
✓ Gracefully handles corrupted Excel files (7 failed, system continues)
✓ Fast in-memory lookups
✓ Integrated into estimation pipeline

## Maintenance

To update calibration data:
1. Add/update Excel files in `app/data/calibration/`
2. Restart backend server
3. Check logs for loading confirmation
