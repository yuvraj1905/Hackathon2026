# Calibration Data

Place GeekyAnts estimation Excel exports here for automatic calibration.

## Supported Formats

- `.xlsx` (Excel 2007+)
- `.xls` (Excel 97-2003)

## Multi-Sheet Support

The loader automatically processes **ALL sheets** in each workbook.

### Sheet Processing Rules

A sheet is processed if it contains:

**Feature Column** (any of):
- Name
- Module Name
- Feature
- Module

**AND**

**Hours Data** (priority order):

1. **Total Hours** column (preferred)
2. **Component columns** (summed if Total missing):
   - Web Mobile
   - Backend
   - Wireframe
   - Visual Design

## Row Filtering

Rows are **skipped** if:
- Feature name is empty
- Hours ≤ 0
- Name contains: total, subtotal, summary, grand total

## Example Sheet Structure

```
| Name                    | Category | Total Hours | Web Mobile | Backend |
|-------------------------|----------|-------------|------------|---------|
| User Authentication     | Security | 65          | 20         | 45      |
| Product Catalog         | Core     | 120         | 50         | 70      |
| Payment Integration     | Payment  | 85          | 25         | 60      |
```

## Aggregation

Features with the same normalized name are aggregated using **weighted average**:

- Normalization: lowercase, remove special chars, collapse whitespace
- Sample size threshold: ≥ 2 samples required for calibration override

## Loading

Calibration data is loaded **once at FastAPI startup**.

To reload:
1. Add/update Excel files in this folder
2. Restart the backend server

## Logs

Check logs for:
- Files processed
- Sheets scanned
- Records extracted
- Skipped sheets/errors
