# Z3DMR ADIF Logbook Maker

## 1. Welcome to the Z3DMR ADIF Logbook Maker

**Z3DMR ADIF Logbook Maker** is a small Python utility that converts ADIF log files produced by the **Z3DMR** Android application into a configurable CSV file for use as a personal amateur-radio logbook.

Z3DMR is used to record DMR activity and saves logged contacts in ADIF format.

This application reads a Z3DMR ADIF file and creates or updates a CSV logbook containing the fields selected in `config.yaml`.

The application is designed to keep the conversion rules configurable rather than hard-coded into the Python program.

The configuration defines:

* Station information
* Maidenhead locator
* DMR ID
* QTH and country
* Timezone handling
* Input directory and format
* Output file and format
* CSV column names
* ADIF source fields
* CSV column order

### Project name

**Z3DMR ADIF Logbook Maker**

Python application:

```text
z3dmr_adif_logbook_maker.py
```

### Input

ADIF files exported from Z3DMR.

The application supports:

* `.adi`
* `.adif`

### Output

A configurable CSV amateur-radio logbook.

### To run the application

After making changes to the **config.yaml** file, run:

```bash
# Make Python script executable
chmod 775 z3dmr_adif_logbook_maker.py

./z3dmr_adif_logbook_maker.py
```

---

## 2. Quick start guide

### Prerequisites

* Python 3
* PyYAML
* A Z3DMR ADIF export file
* The project configuration file `config.yaml`

### Basic process

1. Export the ADIF log from the Z3DMR application.
2. Place the ADIF file in the directory configured in `config.yaml`.
3. Check the station and conversion settings in `config.yaml`.
4. Run the Z3DMR ADIF Logbook Maker.
5. The application lists all available `.adi` and `.adif` files.
6. Select the ADIF file to process.
7. The application converts the selected records to CSV.
8. If the CSV does not exist, it is created with a header.
9. If the CSV already exists, the new records are appended to the existing CSV.

### Installing PyYAML

If PyYAML is not already installed:

```bash
pip install pyyaml
```

### Selecting an ADIF file
At this point, copy the log files from your Android Downloads folder to a USB 3 Thumb drive, and then to this folder

The application does **not** require a specific ADIF filename to be configured.

**Assume we have these files in this directory:**

```text
z3dmr-stations-20261006-1947.adi
z3dmr-stations-20261007-1815.adi
z3dmr-stations-20261008-0910.adif
```
When we run the application:
```bash
./z3dmr_adif_logbook_maker.py
```

The application displays:

```text
Available ADIF files:

1. z3dmr-stations-20261008-0910.adif
2. z3dmr-stations-20261007-1815.adi
3. z3dmr-stations-20261006-1947.adi

Select an input file [1-3]:
```

The user selects the file by entering its number.

If only one ADIF file is available, it is selected automatically.

The application does not maintain a processed-file list. An ADIF file can therefore be selected again on a later run.

---

## 3. Configuration guide

The application is controlled by `config.yaml`.

### Station information

```yaml
callsign: ZS6BVR
maidenhead_locator: KG44dd58
dmr_id: 6550430
qth: Pretoria
country: South Africa
```

These values identify the station using the logbook maker.

### Timezone

```yaml
timezone:
  local: Africa/Johannesburg
  logbook: UTC
```

`local` identifies the station's local timezone.

`logbook` defines the timezone used for timestamps written to the CSV logbook.

The Z3DMR ADIF timestamps are treated as UTC and the resulting logbook timestamps are written using the configured `date_format`.

### Date format

```yaml
date_format: "%Y-%m-%d %H:%M:%S"
```

This produces timestamps such as:

```text
2026-10-06 17:21:36
```

---

## 4. Input configuration

The input configuration defines the format and directory containing the Z3DMR ADIF files.

Example:

```yaml
input:
  format: ADIF
  source:
    directory: .
    prompt_for_file: true
```

### Input format

```yaml
format: ADIF
```

Defines the input file format.

The current application supports ADIF input.

### Input directory

```yaml
source:
  directory: .
```

Defines the directory in which the application searches for ADIF files.

The value:

```text
.
```

means the current project directory.

The application searches this directory for files ending in:

```text
.adi
.adif
```

### File selection

```yaml
prompt_for_file: true
```

This setting indicates that the application should allow the user to select an ADIF file from the available files.

The application currently lists all available ADIF files and allows the user to select one by number.

The application does not use a configured `default_file` for the ADIF input.

---

## 5. Output configuration

The output configuration defines the CSV format and output filename.

Example:

```yaml
output:
  format: CSV
  default_file: hamradio_logbook.csv
```

### Output format

```yaml
format: CSV
```

Defines the output format.

The current application supports CSV output.

### Output file

```yaml
default_file: hamradio_logbook.csv
```

Defines the CSV logbook file.

### Creating and updating the CSV

If the output CSV does not exist, the application:

1. Creates the CSV file.
2. Writes the configured column headers.
3. Writes the converted ADIF records.

If the output CSV already exists, the application:

1. Opens the existing CSV.
2. Does not write another header.
3. Appends the converted records.

For example:

```text
ADIF file
    |
    v
Select ADIF file
    |
    v
Read ADIF records
    |
    v
Convert records
    |
    v
CSV exists?
   / \
 No   Yes
 |     |
Create Append
 |     |
 +--+--+
    |
    v
CSV logbook
```

The application does not maintain a separate processed-file database or state file.

---

## 6. CSV columns

The CSV columns are configurable.

Each column specifies:

* `name` — name written to the CSV header
* `source_fields` — ADIF field or fields used to create the value
* `position` — position of the column in the CSV file

Example:

```yaml
columns:
  - name: DateTime
    source_fields:
      - QSO_DATE
      - TIME_ON
    position: 0

  - name: Callsign
    source_fields:
      - CALL
    position: 1

  - name: Name
    source_fields:
      - NAME
    position: 2

  - name: QTH
    source_fields:
      - QTH
    position: 3
```

The `position` value starts at `0`.

Therefore:

```text
position: 0
```

is the first CSV column.

```text
position: 1
```

is the second CSV column.

The `DateTime` example uses two ADIF fields:

```text
QSO_DATE
TIME_ON
```

These fields are combined to create the single CSV value.

---

## 7. Current CSV fields

The initial logbook configuration contains:

| Position | CSV column  | ADIF source            |
| -------: | ----------- | ---------------------- |
|        0 | DateTime    | `QSO_DATE` + `TIME_ON` |
|        1 | Callsign    | `CALL`                 |
|        2 | Name        | `NAME`                 |
|        3 | QTH         | `QTH`                  |
|        4 | State       | `STATE`                |
|        5 | Country     | `COUNTRY`              |
|        6 | Mode        | `SUBMODE`              |
|        7 | Propagation | `PROP_MODE`            |
|        8 | Network     | `APP_Z3DMR_NETWORK`    |
|        9 | Talkgroup   | `APP_Z3DMR_TALKGROUP`  |
|       10 | DMR_ID      | `APP_Z3DMR_DMR_ID`     |
|       11 | Comment     | `COMMENT`              |

Z3DMR-specific activity fields such as call count and total seconds are deliberately not included in the logbook CSV.

The CSV layout can be changed by editing the `columns` section of `config.yaml`.

The Python application should not need to be changed simply to:

* Add a CSV field
* Remove a CSV field
* Change the ADIF source field
* Change the CSV column order

---

## 8. ADIF processing

The application reads ADIF records separated by the ADIF `<EOR>` marker.

Each ADIF record produces one CSV row.

The `DateTime` field is created from:

```text
QSO_DATE
TIME_ON
```

For example:

```text
QSO_DATE = 20261006
TIME_ON  = 172136
```

produces:

```text
2026-10-06 17:21:36
```

using the configured date format.

---

## 9. Important behaviour

The application is intentionally simple and file based.

### Every run

Each time the application is started:

1. The configuration is loaded.
2. Available ADIF files are discovered.
3. The user selects an ADIF file.
4. The selected ADIF file is converted.
5. The output CSV is created or updated.

### Reprocessing an ADIF file

The application does **not** record which ADIF files have previously been processed.

This means an ADIF file can be selected again.

If the output CSV already exists, selecting the same ADIF file again will append its records again.

If the output CSV has been deleted, the next run will create a new CSV from the selected ADIF file.

This behaviour keeps the application stateless and allows the user to control the contents of the output logbook.

---

## 10. Project files

The main project files are:

```text
z3dmr-adif-logbook-maker/
├── config.yaml
├── README.md
├── z3dmr_adif_logbook_maker.py
└── <Z3DMR ADIF files>
```

### `config.yaml`

Contains the configurable application settings.

### `z3dmr_adif_logbook_maker.py`

Contains the Python application that:

* Finds ADIF files
* Allows the user to select an ADIF file
* Parses ADIF records
* Converts ADIF fields to configured CSV fields
* Creates the CSV when required
* Appends records to an existing CSV

### `README.md`

Contains the project documentation and configuration guide.

### ADIF files

These are the files exported from Z3DMR and used as input to the conversion process.

---

## 11. Design principles

The project follows a few simple principles:

### Configuration over hard-coding

Conversion rules should be defined in `config.yaml` wherever practical.

### Simple file-based processing

The application does not require a database or external service.

### User-controlled input

The user selects which ADIF export should be processed.

### Reusable output

The CSV logbook can be updated by processing additional ADIF exports.

### No unnecessary processing state

The application does not maintain a separate processed-file registry.

### Keep the Python application generic

Changes to the CSV structure should normally be made through `config.yaml` rather than by modifying the Python code.
