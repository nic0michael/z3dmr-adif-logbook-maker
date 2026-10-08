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


def find_input_file(config: dict[str, Any]) -> Path:
    input_config = config.get("input", {})
    source_config = input_config.get("source", {})
    default_file = input_config.get("default_file")
    prompt = bool(source_config.get("prompt_for_file", False))

    if prompt:
        prompt_text = "Enter ADIF source file"
        if default_file:
            prompt_text += f" [{default_file}]"
        entered = input(prompt_text + ": ").strip()
        filename = entered or default_file
        if not filename:
            raise ValueError("No input file was specified.")
        return Path(filename)

    if not default_file:
        raise ValueError(
            "input.default_file must be specified when "
            "input.source.prompt_for_file is false."
        )
    return Path(default_file)


def parse_adif_records(text: str) -> list[dict[str, str]]:
    """Parse ADIF records after the EOH marker."""
    eoh = re.search(r"<EOH\s*/?>", text, re.IGNORECASE)
    if eoh:
        text = text[eoh.end():]

    records: list[dict[str, str]] = []
    chunks = re.split(r"<EOR\s*/?>", text, flags=re.IGNORECASE)
    field_pattern = re.compile(
        r"<([^:>\s]+):(\d+)(?::([^>\s]+))?>", re.IGNORECASE
    )

    for chunk in chunks:
        if not chunk.strip():
            continue
        matches = list(field_pattern.finditer(chunk))
        record: dict[str, str] = {}
        for index, match in enumerate(matches):
            field_name = match.group(1).upper()
            length = int(match.group(2))
            value_start = match.end()
            value_end = matches[index + 1].start() if index + 1 < len(matches) else len(chunk)
            record[field_name] = chunk[value_start:value_end][:length]
        if record:
            records.append(record)

    return records


def make_datetime(record: dict[str, str], fields: list[str], date_format: str) -> str:
    if len(fields) != 2:
        raise ValueError("DateTime requires QSO_DATE and TIME_ON as source_fields.")
    date_value = record.get(fields[0].upper(), "").strip()
    time_value = record.get(fields[1].upper(), "").strip()
    if not date_value or not time_value:
        return ""
    try:
        parsed = datetime.strptime(f"{date_value} {time_value}", "%Y%m%d %H%M%S")
    except ValueError as exc:
        raise ValueError(f"Invalid ADIF date/time: {date_value} {time_value}") from exc
    return parsed.strftime(date_format)


def get_columns(config: dict[str, Any]) -> list[dict[str, Any]]:
    columns = config.get("columns", [])
    if not isinstance(columns, list) or not columns:
        raise ValueError("The configuration must contain a non-empty columns list.")

    positions: list[int] = []
    for column in columns:
        if not isinstance(column, dict):
            raise ValueError("Each column definition must be a YAML mapping.")
        for required in ("name", "source_fields", "position"):
            if required not in column:
                raise ValueError(f"Column definition is missing '{required}'.")
        if not isinstance(column["source_fields"], list) or not column["source_fields"]:
            raise ValueError(f"Column '{column['name']}' must have source_fields.")
        positions.append(int(column["position"]))

    if len(positions) != len(set(positions)):
        raise ValueError("CSV column positions must be unique.")
    if sorted(positions) != list(range(len(positions))):
        raise ValueError("CSV column positions must start at 0 and be consecutive.")
    return sorted(columns, key=lambda c: int(c["position"]))


def column_value(column: dict[str, Any], record: dict[str, str], date_format: str) -> str:
    name = str(column["name"])
    fields = [str(field).upper() for field in column["source_fields"]]

    if name.lower() == "datetime":
        return make_datetime(record, fields, date_format)

    values = [record.get(field, "").strip() for field in fields]
    return " ".join(value for value in values if value)


def write_csv(output_file: Path, records: list[dict[str, str]], columns: list[dict[str, Any]], date_format: str) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([str(column["name"]) for column in columns])
        for record in records:
            writer.writerow([column_value(column, record, date_format) for column in columns])


def main() -> int:
    try:
        config = load_config(CONFIG_FILE)
        input_file = find_input_file(config)
        input_config = config.get("input", {})
        output_config = config.get("output", {})
        input_format = str(input_config.get("format", "ADIF")).upper()
        output_format = str(output_config.get("format", "CSV")).upper()

        if input_format != "ADIF":
            raise ValueError(f"Unsupported input format: {input_format}")
        if output_format != "CSV":
            raise ValueError(f"Unsupported output format: {output_format}")

        output_name = output_config.get("default_file")
        if not output_name:
            raise ValueError("output.default_file must be specified in config.yaml.")
        output_file = Path(output_name)

        if not input_file.exists():
            raise FileNotFoundError(f"ADIF input file not found: {input_file}")

        columns = get_columns(config)
        date_format = str(config.get("date_format", "%Y-%m-%d %H:%M:%S"))
        text = input_file.read_text(encoding="utf-8-sig")
        records = parse_adif_records(text)
        if not records:
            raise ValueError(f"No ADIF records were found in {input_file}.")

        write_csv(output_file, records, columns, date_format)
        print(f"Input file : {input_file}")
        print(f"Records    : {len(records)}")
        print(f"Output file: {output_file}")
        print("Conversion completed successfully.")
        return 0
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

