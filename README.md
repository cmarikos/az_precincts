# AZ Precinct Code Normalizer (`pctnum`)

This project standardizes Arizona voting precinct identifiers into a **uniform 6‑character `pctnum`** code:

```
<COUNTY_PREFIX><ZERO-PADDED 4-DIGIT PRECINCT NUMBER>
e.g., PM0025  (PIMA county, precinct 25)
```

It helps with mapping and joining disparate program datasets where precinct fields differ (numeric vs. text, decimals in CSV exports, embedded numbers in names, etc.).

---

## What the script does

1. **Loads a CSV** of precinct‑level records (typically exported from BigQuery).
2. **Maps county names → two‑letter prefixes** (see table below).
3. **Extracts the numeric precinct code**, handling common formats:
   - Plain integers (`25`)
   - Decimals from CSV exports (`25.0`)
   - Text names with trailing digits (e.g., `"Precinct 87"` → `0087`) — optional regex mode
4. **Builds `pctnum`** as `<prefix><number padded to 4 digits>`, e.g., `MO0102`.
5. **Flags unparseable rows** as `ERROR`.
6. **Writes a new CSV** with the `pctnum` column added.

---

## County prefix dictionary

```python
county_codes = {
    'YUMA': 'YU', 'MARICOPA': 'MC', 'SANTA CRUZ': 'SC', 'GILA': 'GI',
    'PIMA': 'PM', 'PINAL': 'PN', 'APACHE': 'AP', 'GRAHAM': 'GM',
    'LA PAZ': 'LP', 'MOHAVE': 'MO', 'NAVAJO': 'NA', 'COCHISE': 'CH',
    'YAVAPAI': 'YA', 'COCONINO': 'CN', 'GREENLEE': 'GN'
}
```
You could also use FIPS county prefixes in this dictionary, but I prefer alphabetical because it lets me easily see at a glance which county any precinct is in.

> **Assumption:** County names in your CSV match these keys (uppercased, spacing as shown). If not, normalize first (e.g., `df['countyname'] = df['countyname'].str.upper().str.strip()`). 

---

## Inputs & Outputs

- **Input CSV:** Exported dataset with at least:
  - A county column (e.g., `countyname` or `county_name`)
  - A precinct column:
    - **Numeric mode:** `precinctcode` like `25`, `25.0`
    - **Regex mode (embedded digits):** a string field like `svi_registration_national_precinct_code` or `precinct_name` that ends with digits

- **Output CSV:** Same rows plus a new `pctnum` column. Rows that cannot be parsed get `pctnum = 'ERROR'`.

---

## Quickstart

### A) Numeric precinct codes (simplest)

Use this when the precinct column is numeric (or numeric‐formatted strings like `25.0`).

```python
import pandas as pd

precincts = pd.read_csv('/path/to/RAZA_c4_2024_Door_Attempts.csv')

county_codes = {
    'YUMA':'YU','MARICOPA':'MC','SANTA CRUZ':'SC','GILA':'GI','PIMA':'PM','PINAL':'PN',
    'APACHE':'AP','GRAHAM':'GM','LA PAZ':'LP','MOHAVE':'MO','NAVAJO':'NA','COCHISE':'CH',
    'YAVAPAI':'YA','COCONINO':'CN','GREENLEE':'GN'
}

def extract_pctnum(countyname, precinctcode, county_codes):
    try:
        precinct_int = int(float(precinctcode))  # handles '25' and '25.0'
    except (ValueError, TypeError):
        return 'ERROR'

    num_part = str(precinct_int).zfill(4)
    county_prefix = county_codes.get(str(countyname).upper().strip())
    return county_prefix + num_part if county_prefix else 'ERROR'

precincts['pctnum'] = precincts.apply(
    lambda row: extract_pctnum(row['countyname'], row['precinctcode'], county_codes),
    axis=1
)

precincts.to_csv('/content/modified_precincts.csv', index=False)
```

**Examples**
- `countyname='PIMA'`, `precinctcode='25.0'` → `PM0025`  
- `countyname='MOHAVE'`, `precinctcode='102'` → `MO0102`

---

### B) Text precinct names with trailing digits (regex mode)

Use this if the precinct identifier is embedded in a string (e.g., `"PRECINCT 87"`), or for fields like `svi_registration_national_precinct_code`.  
Also skips **UNCODED** rows (returns `ERROR`).

```python
import re
import pandas as pd

precincts = pd.read_csv('/path/to/2024_Door_Attempts.csv')

county_codes = { ... }  # same dict as above

def extract_pctnum(county_name, precinctcode, county_codes):
    s = str(precinctcode).upper()
    if 'UNCODED' in s:
        return 'ERROR'

    # capture 1–3 trailing digits, then zero-pad to 4
    match = re.search(r'(\d{1,3})$', s)
    if not match:
        return 'ERROR'

    num_part = match.group(1).zfill(4)
    county_prefix = county_codes.get(str(county_name).upper().strip())
    return county_prefix + num_part if county_prefix else 'ERROR'

precincts['pctnum'] = precincts.apply(
    lambda row: extract_pctnum(row['county_name'], row['svi_registration_national_precinct_code'], county_codes),
    axis=1
)

precincts.to_csv('/content/modified_c4precincts.csv', index=False)
print(precincts[['county_name','svi_registration_national_precinct_code','pctnum']].head())
```

**Examples**
- `county_name='PIMA'`, `svi_registration_national_precinct_code='PRECINCT 7'` → `PM0007`
- `county_name='MARICOPA'`, `...='PC 123'` → `MC0123`
- `...='UNCODED'` → `ERROR`

---

## Data quality checks (recommended)

After writing your output CSV:

1. **Length check**  
   `precincts['pctnum'].str.len().value_counts()` should show `6` for valid rows (2 letters + 4 digits).

2. **Error flag audit**  
   `precincts[precincts['pctnum'] == 'ERROR']`  
   - Missing or mismatched county names?
   - Non‐numeric or missing precinct digits?
   - “UNCODED” values?

3. **Uniqueness (within county)**  
   `precincts.groupby(['countyname','pctnum']).size().loc[lambda s: s>1]` — duplicates should be investigated.

4. **Crosswalk spot‑check**  
   If you maintain a master `pctnum` crosswalk, inner join and review any non‑matches.

---

## Common pitfalls & fixes

- **County string mismatches**  
  Normalize: `df['countyname'] = df['countyname'].str.upper().str.strip()`.  
  Ensure names match keys exactly (e.g., `"SANTA CRUZ"` not `"SantaCruz"`).

- **CSV decimals**  
  BigQuery CSV exports often render integers like `25` as `25.0`. The numeric mode handles this via `int(float(...))`.

- **Leading zeros lost**  
  Never store the numeric precinct as an integer alone; always recompute `zfill(4)` when generating `pctnum`.

- **“UNCODED” rows**  
  Regex mode explicitly returns `ERROR` for these—decide whether to drop or repair upstream.

---

## Why this exists

Different sources encode precincts inconsistently (numbers, decimals, text labels, or missing). A single normalized `pctnum` key:
- Simplifies joins across voter file outputs, canvassing exports, and survey data.
- Prevents silent mismatches in mapping and aggregation.
- Keeps downstream models and reports stable.

---

## Adapting to your file

- **Column names**  
  Update the `.apply(...)` call to use your column headers (e.g., `county_name` vs. `countyname`).

- **County map changes**  
  If a county label differs, either normalize input or add a new mapping key.

- **Alternate parsing rules**  
  If your precinct codes don’t end with digits, adjust the regex accordingly (e.g., capture the first run of digits).

---

## Example validation snippet

```python
# Basic validation after build
ok = precincts.query("pctnum != 'ERROR' and pctnum.str.len() == 6", engine="python")
err = precincts[~precincts.index.isin(ok.index)]

print(f"Valid rows: {len(ok):,}  |  Errors: {len(err):,}")
if not err.empty:
    display(err.head(20))
```

---

**Maintainer:** Christina Marikos christina@ruralazaction.org 
**Scope:** Arizona precinct normalization for mapping/joining  
**Output key:** `pctnum` (2‑letter county prefix + 4‑digit precinct number)
