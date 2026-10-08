# Z3DMR ADIF Logbook Maker

## 1. Welcome to the Z3DMR ADIF Logbook Maker

**Z3DMR ADIF Logbook Maker** is a small Python utility that converts ADIF log files produced by the **Z3DMR** Android application into a configurable CSV file for use as a personal amateur-radio logbook.

Z3DMR is used to record DMR activity and saves the logged contacts in ADIF format.

This application reads the Z3DMR ADIF file and creates a CSV logbook containing the fields selected in `config.yaml`.

The application is designed to keep the conversion rules configurable rather than hard-coded into the Python program.

The configuration defines:

* Station information
* Maidenhead locator
* DMR ID
* QTH and country
* Timezone handling
* Input file and format
* Output file and format
* CSV column names
* ADIF source fields
* CSV column order

### Project name

**Z3DMR ADIF Logbook Maker**
z3dmr_adif_logbook_maker.py
### Input

ADIF files exported from Z3DMR.

### Output

A configurable CSV amateur-radio logbook.

### To run the application
After making changes to the **config.yaml** file Run this command:
```bash
./z3dmr_adif_logbook_maker.py
```

---

## 2. Quick start guide

### Prerequisites

* Python 3
* A Z3DMR ADIF export file
* The project configuration file `config.yaml`

### Basic process

1. Export the ADIF log from the Z3DMR application.
2. Place the ADIF file in the location configured in `config.yaml`.
3. Check the station and conversion settings in `config.yaml`.
4. Run the Z3DMR ADIF Logbook Maker.
5. The application reads the ADIF file.
6. The application creates the configured CSV logbook.

The default configuration is designed to allow the application to run without asking for an input filename.

To change this behaviour, set:

```yaml
input:
  source:
    prompt_for_file: true
```

When `prompt_for_file` is `false`, the configured `default_file` is used.

When `prompt_for_file` is `true`, the application asks the user for the source ADIF file.

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

### Input

```yaml
input:
  format: ADIF
  default_file: z3dmr_export.adi
  source:
    prompt_for_file: false
```

`format` defines the input file format.

`default_file` specifies the default ADIF file to read.

`prompt_for_file` controls how the source file is selected:

* `false` — use `default_file`
* `true` — ask the user for the source file

### Output

```yaml
output:
  format: CSV
  default_file: hamradio_logbook.csv
```

`format` defines the output format.

`default_file` specifies the default CSV file that will be created.

### CSV columns

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

### Current CSV fields

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

Z3DMR-specific fields such as call count and total seconds are deliberately not included in the logbook CSV.

The CSV layout can be changed by editing the `columns` section of `config.yaml`; the Python application should not need to be changed simply to change the CSV column order or selected fields.


