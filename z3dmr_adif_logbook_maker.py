#!/usr/bin/env python3
"""Z3DMR ADIF Logbook Maker.

Reads an ADIF file exported by Z3DMR and creates a configurable CSV
logbook using settings from config.yaml.
"""

from __future__ import annotations

import csv
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install it with: pip install pyyaml")
    sys.exit(1)


CONFIG_FILE = Path("config.yaml")


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if not isinstance(config, dict):
        raise ValueError("Configuration file must contain a YAML mapping.")

    return config


def find_adif_files(directory: Path) -> list[Path]:
    """Return all ADIF files in the configured directory."""

    if not directory.exists():
        raise FileNotFoundError(
            f"Input directory not found: {directory}"
        )

    if not directory.is_dir():
        raise ValueError(
            f"Input path is not a directory: {directory}"
        )

    files = [
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.suffix.lower() in (".adi", ".adif")
    ]

    return sorted(
        files,
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def choose_input_file(config: dict[str, Any]) -> Path:
    """Display available ADIF files and let the user select one."""

    input_config = config.get("input", {})
    source_config = input_config.get("source", {})

    directory_name = source_config.get(
        "directory",
        ".",
    )

    directory = Path(directory_name)

    files = find_adif_files(directory)

    if not files:
        raise FileNotFoundError(
            f"No ADIF files were found in: {directory}"
        )

    print()
    print("Z3DMR ADIF Logbook Maker")
    print()
    print("Available ADIF files:")
    print()

    for index, path in enumerate(files, start=1):
        print(f"{index}. {path.name}")

    print()

    if len(files) == 1:
        selected_file = files[0]
        print("Only one ADIF file is available.")
    else:
        while True:
            entered = input(
                f"Select an input file [1-{len(files)}]: "
            ).strip()

            try:
                selection = int(entered)
            except ValueError:
                print("Please enter a number.")
                continue

            if 1 <= selection <= len(files):
                selected_file = files[selection - 1]
                break

            print(
                f"Please enter a number between 1 and {len(files)}."
            )

    print()
    print(f"Input file selected: {selected_file.name}")
    print()

    return selected_file


def parse_adif_records(text: str) -> list[dict[str, str]]:
    """Parse ADIF records after the EOH marker."""

    eoh = re.search(
        r"<EOH\s*/?>",
        text,
        re.IGNORECASE,
    )

    if eoh:
        text = text[eoh.end():]

    records: list[dict[str, str]] = []

    chunks = re.split(
        r"<EOR\s*/?>",
        text,
        flags=re.IGNORECASE,
    )

    field_pattern = re.compile(
        r"<([^:>\s]+):(\d+)(?::([^>\s]+))?>",
        re.IGNORECASE,
    )

    for chunk in chunks:
        if not chunk.strip():
            continue

        matches = list(
            field_pattern.finditer(chunk)
        )

        record: dict[str, str] = {}

        for index, match in enumerate(matches):
            field_name = match.group(1).upper()
            length = int(match.group(2))

            value_start = match.end()

            if index + 1 < len(matches):
                value_end = matches[index + 1].start()
            else:
                value_end = len(chunk)

            record[field_name] = (
                chunk[value_start:value_end][:length]
            )

        if record:
            records.append(record)

    return records


def make_datetime(
    record: dict[str, str],
    fields: list[str],
    date_format: str,
) -> str:
    """Create the output DateTime from QSO_DATE and TIME_ON."""

    if len(fields) != 2:
        raise ValueError(
            "DateTime requires QSO_DATE and TIME_ON as source_fields."
        )

    date_value = record.get(
        fields[0].upper(),
        "",
    ).strip()

    time_value = record.get(
        fields[1].upper(),
        "",
    ).strip()

    if not date_value or not time_value:
        return ""

    try:
        parsed = datetime.strptime(
            f"{date_value} {time_value}",
            "%Y%m%d %H%M%S",
        )
    except ValueError as exc:
        raise ValueError(
            f"Invalid ADIF date/time: {date_value} {time_value}"
        ) from exc

    return parsed.strftime(date_format)


def get_columns(
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Validate and return CSV columns in position order."""

    columns = config.get("columns", [])

    if not isinstance(columns, list) or not columns:
        raise ValueError(
            "The configuration must contain a non-empty columns list."
        )

    positions: list[int] = []

    for column in columns:
        if not isinstance(column, dict):
            raise ValueError(
                "Each column definition must be a YAML mapping."
            )

        for required in (
            "name",
            "source_fields",
            "position",
        ):
            if required not in column:
                raise ValueError(
                    f"Column definition is missing '{required}'."
                )

        if (
            not isinstance(column["source_fields"], list)
            or not column["source_fields"]
        ):
            raise ValueError(
                f"Column '{column['name']}' must have source_fields."
            )

        positions.append(int(column["position"]))

    if len(positions) != len(set(positions)):
        raise ValueError(
            "CSV column positions must be unique."
        )

    if sorted(positions) != list(range(len(positions))):
        raise ValueError(
            "CSV column positions must start at 0 and be consecutive."
        )

    return sorted(
        columns,
        key=lambda column: int(column["position"]),
    )


def column_value(
    column: dict[str, Any],
    record: dict[str, str],
    date_format: str,
) -> str:
    """Return the CSV value for one configured column."""

    name = str(column["name"])

    fields = [
        str(field).upper()
        for field in column["source_fields"]
    ]

    if name.lower() == "datetime":
        return make_datetime(
            record,
            fields,
            date_format,
        )

    values = [
        record.get(field, "").strip()
        for field in fields
    ]

    return " ".join(
        value
        for value in values
        if value
    )


def write_csv(
    output_file: Path,
    records: list[dict[str, str]],
    columns: list[dict[str, Any]],
    date_format: str,
) -> None:
    """Create the CSV if it does not exist, otherwise append records."""

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_exists = output_file.exists()

    mode = "a" if file_exists else "w"

    with output_file.open(
        mode,
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(
                [
                    str(column["name"])
                    for column in columns
                ]
            )

        for record in records:
            writer.writerow(
                [
                    column_value(
                        column,
                        record,
                        date_format,
                    )
                    for column in columns
                ]
            )


def main() -> int:
    try:
        config = load_config(CONFIG_FILE)

        input_config = config.get("input", {})
        output_config = config.get("output", {})

        input_format = str(
            input_config.get("format", "ADIF")
        ).upper()

        output_format = str(
            output_config.get("format", "CSV")
        ).upper()

        if input_format != "ADIF":
            raise ValueError(
                f"Unsupported input format: {input_format}"
            )

        if output_format != "CSV":
            raise ValueError(
                f"Unsupported output format: {output_format}"
            )

        input_file = choose_input_file(config)

        output_name = output_config.get("default_file")

        if not output_name:
            raise ValueError(
                "output.default_file must be specified in config.yaml."
            )

        output_file = Path(output_name)

        columns = get_columns(config)

        date_format = str(
            config.get(
                "date_format",
                "%Y-%m-%d %H:%M:%S",
            )
        )

        text = input_file.read_text(
            encoding="utf-8-sig"
        )

        records = parse_adif_records(text)

        if not records:
            raise ValueError(
                f"No ADIF records were found in {input_file}."
            )

        file_exists = output_file.exists()

        write_csv(
            output_file,
            records,
            columns,
            date_format,
        )

        if file_exists:
            action = "appended to"
        else:
            action = "created"

        print(
            f"Input file : {input_file.name}"
        )
        print(
            f"Records    : {len(records)}"
        )
        print(
            f"Output file: {output_file}"
        )
        print(
            f"Records successfully {action} the CSV."
        )
        print(
            "Conversion completed successfully."
        )

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 1

    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


