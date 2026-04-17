#!/usr/bin/env python3

import csv
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from collections import Counter
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKBENCH_DIR = ROOT / "workbench"
CSV_DIR = WORKBENCH_DIR / "normalized_csv"
DB_PATH = WORKBENCH_DIR / "everyaction_workbench.sqlite"
PROFILE_JSON_PATH = ROOT / "analysis" / "dataset_profiles.json"
REPORT_MD_PATH = ROOT / "analysis" / "eda_summary.md"
EXPORT_DATE = date(2026, 4, 9)

DATASETS = [
    {
        "source": "Activist Codes List 4.9.26.xls",
        "table": "activist_codes_list",
        "kind": "html",
        "candidate_keys": [["type", "long_name"], ["short"]],
        "index_columns": ["type", "short"],
    },
    {
        "source": "Activist Code List  2.xlsx",
        "table": "activist_codes_list_xlsx",
        "kind": "xlsx",
        "candidate_keys": [["type", "long_name"], ["short"]],
        "index_columns": ["type", "short"],
    },
    {
        "source": "Addresses Report 4.9.26.xls",
        "table": "addresses_report",
        "kind": "tsv",
        "candidate_keys": [["address_id"], ["vanid", "street_address", "city", "state_province", "zip_postal"]],
        "index_columns": ["address_id", "vanid", "state_province"],
    },
    {
        "source": "All Activist Codes Applied 9.27.21-4.9.26.xls",
        "table": "all_activist_codes_applied",
        "kind": "tsv",
        "candidate_keys": [["vanid", "activistcodeid", "datecreated", "inputtype"]],
        "index_columns": ["vanid", "activistcodeid", "datecreated"],
    },
    {
        "source": "All Contributions Ever 4.9.26.xls",
        "table": "all_contributions_ever",
        "kind": "tsv",
        "candidate_keys": [["contribution_id"]],
        "index_columns": ["contribution_id", "vanid", "date_received"],
    },
    {
        "source": "All Event Participant Report 4.9.26.xls",
        "table": "all_event_participant_report",
        "kind": "tsv",
        "candidate_keys": [["vanid", "event_name", "signup_date", "role", "status"]],
        "index_columns": ["vanid", "event_name", "event_date"],
    },
    {
        "source": "All Online Action Data 4.9.26.xls",
        "table": "all_online_action_data",
        "kind": "tsv",
        "candidate_keys": [["vanid", "form_name", "date_submitted", "source_code"]],
        "index_columns": ["vanid", "form_name", "date_submitted"],
    },
    {
        "source": "Database List 4.9.26.xls",
        "table": "database_list",
        "kind": "tsv",
        "candidate_keys": [["vanid"]],
        "index_columns": ["vanid", "preferredemail", "state_province"],
    },
    {
        "source": "Tags 2.xlsx",
        "table": "tags_list",
        "kind": "xlsx",
        "candidate_keys": [["id"], ["name"], ["path"]],
        "index_columns": ["id", "name", "path"],
    },
]

DATE_PATTERNS = (
    ("%Y-%m-%d", "date"),
    ("%m/%d/%Y", "date"),
    ("%Y-%m-%d %H:%M:%S.%f %z", "datetime"),
    ("%Y-%m-%d %H:%M:%S %z", "datetime"),
)

CATEGORICAL_HINTS = {
    "activist",
    "created_by",
    "name",
    "path",
    "type",
    "status",
    "scope",
    "country",
    "countrycode",
    "countryname",
    "state_province",
    "payment_method",
    "contribution_type",
    "event_type",
    "role",
    "source_code",
    "designation",
    "period",
    "cycle",
    "form_type",
    "is_new_contact",
    "type_of_contact",
}

XLSX_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
EXCEL_DATE_ORIGIN = datetime(1899, 12, 30)


def quote_ident(value):
    return '"' + value.replace('"', '""') + '"'


def normalize_header(value, fallback):
    value = clean_value(value).lower()
    value = re.sub(r"[^0-9a-z]+", "_", value).strip("_")
    if not value:
        value = f"column_{fallback}"
    if value[0].isdigit():
        value = f"col_{value}"
    return value


def clean_value(value):
    if value is None:
        return ""
    value = value.replace("\ufeff", "").replace("\x00", "").strip()
    if value.startswith('="') and value.endswith('"') and len(value) >= 4:
        value = value[2:-1]
    return value


def infer_scalar_type(value):
    if value == "":
        return "empty"
    if value in {"0", "1", "True", "False", "true", "false"}:
        return "booleanish"
    if re.fullmatch(r"-?\d+", value):
        return "integer"
    if re.fullmatch(r"-?\d+\.\d+", value):
        return "float"
    for fmt, label in DATE_PATTERNS:
        try:
            datetime.strptime(value, fmt)
            return label
        except ValueError:
            continue
    return "text"


def parse_dateish(value):
    if value == "":
        return None
    for fmt, _label in DATE_PATTERNS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


class HtmlTableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self._cell_parts = []
        self._row = []
        self._in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in {"th", "td"}:
            self._in_cell = True
            self._cell_parts = []

    def handle_endtag(self, tag):
        if tag in {"th", "td"} and self._in_cell:
            self._row.append(clean_value("".join(self._cell_parts)))
            self._in_cell = False
        elif tag == "tr" and self._row:
            self.rows.append(self._row)

    def handle_data(self, data):
        if self._in_cell:
            self._cell_parts.append(data)


class ColumnProfiler:
    def __init__(self, name):
        self.name = name
        self.non_null = 0
        self.blank = 0
        self.type_counts = Counter()
        self.samples = []
        self.samples_seen = set()
        self.min_numeric = None
        self.max_numeric = None
        self.min_date = None
        self.max_date = None
        self.future_dates = 0
        self.categorical_counts = Counter() if self._track_categories(name) else None

    @staticmethod
    def _track_categories(name):
        return name in CATEGORICAL_HINTS or name.endswith("_type") or name.endswith("_status")

    def add(self, value):
        if value == "":
            self.blank += 1
            self.type_counts["empty"] += 1
            return

        self.non_null += 1
        scalar_type = infer_scalar_type(value)
        self.type_counts[scalar_type] += 1

        if len(self.samples) < 5 and value not in self.samples_seen:
            self.samples.append(value)
            self.samples_seen.add(value)

        if scalar_type in {"integer", "float"}:
            numeric_value = float(value)
            if self.min_numeric is None or numeric_value < self.min_numeric:
                self.min_numeric = numeric_value
            if self.max_numeric is None or numeric_value > self.max_numeric:
                self.max_numeric = numeric_value
        elif scalar_type in {"date", "datetime"}:
            parsed = parse_dateish(value)
            if parsed is not None:
                if self.min_date is None or parsed < self.min_date:
                    self.min_date = parsed
                if self.max_date is None or parsed > self.max_date:
                    self.max_date = parsed
                if parsed.date() > EXPORT_DATE:
                    self.future_dates += 1

        if self.categorical_counts is not None:
            self.categorical_counts[value] += 1

    def summary(self, row_count):
        missing_rate = round(self.blank / row_count, 4) if row_count else 0.0
        top_values = []
        if self.categorical_counts:
            top_values = [
                {"value": value, "count": count}
                for value, count in self.categorical_counts.most_common(5)
            ]
        return {
            "column": self.name,
            "non_null": self.non_null,
            "blank": self.blank,
            "missing_rate": missing_rate,
            "type_counts": dict(self.type_counts),
            "samples": self.samples,
            "min_numeric": self.min_numeric,
            "max_numeric": self.max_numeric,
            "min_date": self.min_date.isoformat() if self.min_date else None,
            "max_date": self.max_date.isoformat() if self.max_date else None,
            "future_dates_after_export": self.future_dates,
            "top_values": top_values,
        }


def make_unique_headers(headers):
    result = []
    seen = Counter()
    for idx, header in enumerate(headers, start=1):
        base = normalize_header(header, idx)
        seen[base] += 1
        result.append(base if seen[base] == 1 else f"{base}_{seen[base]}")
    return result


def excel_col_index(ref):
    letters = "".join(ch for ch in ref if ch.isalpha())
    value = 0
    for char in letters:
        value = value * 26 + (ord(char.upper()) - ord("A") + 1)
    return max(value - 1, 0)


def iter_tsv_rows(path):
    with path.open("r", encoding="utf-16", errors="replace", newline="") as handle:
        def sanitized_lines():
            for line in handle:
                yield line.replace("\x00", "")

        reader = csv.reader(sanitized_lines(), delimiter="\t")
        for row in reader:
            yield [cell.replace("\ufeff", "").replace("\x00", "") for cell in row]


def iter_html_rows(path):
    parser = HtmlTableParser()
    parser.feed(path.read_text(encoding="utf-16", errors="replace"))
    for row in parser.rows:
        yield row


def iter_xlsx_rows(path):
    with ZipFile(path) as workbook:
        shared_strings = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
            for item in root.findall("main:si", XLSX_NS):
                shared_strings.append("".join(text.text or "" for text in item.findall(".//main:t", XLSX_NS)))

        workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
        rel_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rel_root}

        first_sheet = workbook_root.find("main:sheets", XLSX_NS)[0]
        relation_id = first_sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        target = rel_map[relation_id]
        if target.startswith("worksheets/"):
            target = "xl/" + target
        else:
            target = "xl/" + target.replace("../", "")

        sheet_root = ET.fromstring(workbook.read(target))
        for row in sheet_root.findall(".//main:sheetData/main:row", XLSX_NS):
            values_by_index = {}
            max_index = -1
            for cell in row.findall("main:c", XLSX_NS):
                ref = cell.attrib.get("r", "")
                idx = excel_col_index(ref)
                max_index = max(max_index, idx)
                cell_type = cell.attrib.get("t")
                value_node = cell.find("main:v", XLSX_NS)
                cell_value = ""
                if value_node is not None:
                    raw = value_node.text or ""
                    if cell_type == "s" and raw.isdigit():
                        shared_index = int(raw)
                        cell_value = shared_strings[shared_index] if shared_index < len(shared_strings) else raw
                    else:
                        cell_value = raw
                else:
                    inline = cell.find("main:is/main:t", XLSX_NS)
                    if inline is not None:
                        cell_value = inline.text or ""
                values_by_index[idx] = cell_value

            if max_index < 0:
                yield []
            else:
                yield [values_by_index.get(i, "") for i in range(max_index + 1)]


def padded_row(row, width):
    row = row[:width]
    if len(row) < width:
        row = row + [""] * (width - len(row))
    return row


def convert_excel_serial_to_iso(value):
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return value

    if numeric <= 0:
        return value

    if numeric.is_integer():
        dt = EXCEL_DATE_ORIGIN + timedelta(days=int(numeric))
        return dt.date().isoformat()

    dt = EXCEL_DATE_ORIGIN + timedelta(days=numeric)
    return dt.isoformat(sep=" ", timespec="seconds")


def transform_cleaned_row(dataset, headers, cleaned_row):
    if dataset["table"] == "tags_list":
        row_map = {header: value for header, value in zip(headers, padded_row(cleaned_row, len(headers)))}
        if "date_created" in row_map:
            row_map["date_created"] = convert_excel_serial_to_iso(row_map["date_created"])
        return [row_map.get(header, "") for header in headers]

    return padded_row(cleaned_row, len(headers))


def should_skip_row(dataset, cleaned_row, header_width):
    if not any(cleaned_row):
        return "blank_row"

    if dataset["table"] == "activist_codes_list" and len(cleaned_row) != header_width:
        return "report_footer"

    if dataset["table"] == "activist_codes_list_xlsx":
        if len(cleaned_row) != header_width:
            return "report_footer"
        first_cell = cleaned_row[0] if cleaned_row else ""
        if "Activist Codes" in first_cell:
            return "report_footer"

    if dataset["table"] == "all_contributions_ever" and len(cleaned_row) != header_width:
        return "report_footer"

    return None


def create_table(conn, table_name, headers):
    conn.execute(f"DROP TABLE IF EXISTS {quote_ident(table_name)}")
    column_sql = ", ".join(f"{quote_ident(col)} TEXT" for col in headers)
    conn.execute(f"CREATE TABLE {quote_ident(table_name)} ({column_sql})")


def insert_batch(conn, table_name, headers, batch):
    placeholders = ", ".join("?" for _ in headers)
    column_sql = ", ".join(quote_ident(col) for col in headers)
    conn.executemany(
        f"INSERT INTO {quote_ident(table_name)} ({column_sql}) VALUES ({placeholders})",
        batch,
    )


def duplicate_summary(conn, table_name, key_columns):
    missing = [column for column in key_columns if not column_exists(conn, table_name, column)]
    if missing:
        return {
            "key_columns": key_columns,
            "status": "missing_columns",
            "missing_columns": missing,
        }

    cols = ", ".join(quote_ident(column) for column in key_columns)
    query = f"""
        SELECT COALESCE(SUM(cnt - 1), 0), COUNT(*)
        FROM (
            SELECT COUNT(*) AS cnt
            FROM {quote_ident(table_name)}
            GROUP BY {cols}
            HAVING COUNT(*) > 1
        )
    """
    extra_rows, duplicate_groups = conn.execute(query).fetchone()
    return {
        "key_columns": key_columns,
        "status": "ok",
        "duplicate_extra_rows": int(extra_rows or 0),
        "duplicate_groups": int(duplicate_groups or 0),
    }


def column_exists(conn, table_name, column_name):
    pragma = conn.execute(f"PRAGMA table_info({quote_ident(table_name)})").fetchall()
    return any(row[1] == column_name for row in pragma)


def create_indexes(conn, table_name, columns):
    for column in columns:
        if not column_exists(conn, table_name, column):
            continue
        index_name = f"idx_{table_name}_{column}"
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS {quote_ident(index_name)} "
            f"ON {quote_ident(table_name)} ({quote_ident(column)})"
        )


def is_identifier_like(name):
    return (
        name == "vanid"
        or name.endswith("_id")
        or "phone" in name
        or "zip" in name
        or "district" in name
        or name in {"cycle", "cd", "address", "city", "last", "first", "mid", "suf"}
    )


def should_report_as_date(column_summary):
    name = column_summary["column"]
    non_null = column_summary["non_null"]
    if non_null == 0:
        return False

    date_like = column_summary["type_counts"].get("date", 0) + column_summary["type_counts"].get("datetime", 0)
    if date_like == 0:
        return False

    if any(token in name for token in ("date", "time", "dob", "expiration")):
        return True

    return (date_like / non_null) >= 0.8


def should_report_as_numeric(column_summary):
    name = column_summary["column"]
    non_null = column_summary["non_null"]
    if non_null == 0 or is_identifier_like(name):
        return False

    numeric_like = column_summary["type_counts"].get("integer", 0) + column_summary["type_counts"].get("float", 0)
    if numeric_like == 0:
        return False

    numeric_hints = (
        "amount",
        "count",
        "number_of_",
        "average",
        "avg",
        "memoed",
        "tier",
        "hpc_ever",
    )
    if any(token in name for token in numeric_hints):
        return (numeric_like / non_null) >= 0.8

    return False


def analyze_dataset(conn, dataset):
    source_path = ROOT / dataset["source"]
    csv_path = CSV_DIR / f"{dataset['table']}.csv"

    if dataset["kind"] == "html":
        row_iter = iter_html_rows(source_path)
    elif dataset["kind"] == "xlsx":
        row_iter = iter_xlsx_rows(source_path)
    else:
        row_iter = iter_tsv_rows(source_path)
    try:
        raw_headers = next(row_iter)
    except StopIteration:
        raise RuntimeError(f"{source_path.name} is empty")

    headers = make_unique_headers(raw_headers)
    profilers = [ColumnProfiler(name) for name in headers]
    row_count = 0
    row_length_issues = 0
    excel_wrapped_cells = 0
    skipped_rows = Counter()
    sample_rows = []

    create_table(conn, dataset["table"], headers)

    with csv_path.open("w", encoding="utf-8", newline="") as csv_handle:
        writer = csv.writer(csv_handle)
        writer.writerow(headers)
        batch = []

        for raw_row in row_iter:
            raw_row = raw_row[:]
            for value in raw_row:
                stripped = value.strip()
                if stripped.startswith('="') and stripped.endswith('"') and len(stripped) >= 4:
                    excel_wrapped_cells += 1

            cleaned_row = [clean_value(cell) for cell in raw_row]
            skip_reason = should_skip_row(dataset, cleaned_row, len(headers))
            if skip_reason:
                skipped_rows[skip_reason] += 1
                continue

            row = transform_cleaned_row(dataset, headers, cleaned_row)
            if len(cleaned_row) != len(headers):
                row_length_issues += 1

            row_count += 1
            for profiler, value in zip(profilers, row):
                profiler.add(value)

            if len(sample_rows) < 3:
                sample_rows.append(dict(zip(headers, row)))

            writer.writerow(row)
            batch.append(row)

            if len(batch) >= 500:
                insert_batch(conn, dataset["table"], headers, batch)
                conn.commit()
                batch = []

        if batch:
            insert_batch(conn, dataset["table"], headers, batch)
            conn.commit()

    create_indexes(conn, dataset["table"], dataset["index_columns"])

    column_summaries = [profiler.summary(row_count) for profiler in profilers]
    duplicate_checks = [
        duplicate_summary(conn, dataset["table"], key_columns)
        for key_columns in dataset["candidate_keys"]
    ]

    mostly_empty_columns = [
        summary for summary in column_summaries if summary["missing_rate"] >= 0.5
    ]
    mostly_empty_columns.sort(key=lambda item: item["missing_rate"], reverse=True)

    date_columns = [
        summary
        for summary in column_summaries
        if should_report_as_date(summary)
    ]

    numeric_columns = [
        summary
        for summary in column_summaries
        if should_report_as_numeric(summary)
    ]

    return {
        "source_file": dataset["source"],
        "table": dataset["table"],
        "row_count": row_count,
        "column_count": len(headers),
        "headers": headers,
        "csv_path": str(csv_path),
        "row_length_issues": row_length_issues,
        "excel_wrapped_cells": excel_wrapped_cells,
        "skipped_rows": dict(skipped_rows),
        "sample_rows": sample_rows,
        "mostly_empty_columns": mostly_empty_columns[:15],
        "date_columns": date_columns,
        "numeric_columns": numeric_columns,
        "duplicate_checks": duplicate_checks,
        "columns": column_summaries,
    }


def build_report(profiles):
    lines = [
        "# EveryAction Exports EDA Summary",
        "",
        f"Export date assumed from filenames: {EXPORT_DATE.isoformat()}",
        "",
        "## Workbench outputs",
        "",
        f"- SQLite database: `{DB_PATH}`",
        f"- Normalized CSV directory: `{CSV_DIR}`",
        f"- Profile JSON: `{PROFILE_JSON_PATH}`",
        "",
    ]

    for profile in profiles:
        lines.extend(
            [
                f"## {profile['table']}",
                "",
                f"- Source file: `{profile['source_file']}`",
                f"- Rows: {profile['row_count']:,}",
                f"- Columns: {profile['column_count']}",
                f"- Normalized CSV: `{profile['csv_path']}`",
                f"- Row length issues: {profile['row_length_issues']:,}",
                f"- Excel-style wrapped cells fixed: {profile['excel_wrapped_cells']:,}",
                f"- Skipped rows: `{profile['skipped_rows']}`",
                "",
                "### Duplicate checks",
                "",
            ]
        )

        for check in profile["duplicate_checks"]:
            if check["status"] != "ok":
                lines.append(
                    f"- `{', '.join(check['key_columns'])}`: skipped, missing columns {check['missing_columns']}"
                )
            else:
                lines.append(
                    f"- `{', '.join(check['key_columns'])}`: {check['duplicate_groups']:,} duplicate groups, "
                    f"{check['duplicate_extra_rows']:,} extra rows"
                )

        lines.extend(["", "### High-missing columns", ""])
        if not profile["mostly_empty_columns"]:
            lines.append("- None above 50% missing")
        else:
            for column in profile["mostly_empty_columns"][:10]:
                lines.append(
                    f"- `{column['column']}`: {column['missing_rate']:.1%} missing"
                )

        lines.extend(["", "### Date ranges", ""])
        if not profile["date_columns"]:
            lines.append("- No date-like columns detected")
        else:
            for column in profile["date_columns"][:12]:
                lines.append(
                    f"- `{column['column']}`: {column['min_date']} -> {column['max_date']}, "
                    f"future after export = {column['future_dates_after_export']}"
                )

        lines.extend(["", "### Numeric ranges", ""])
        if not profile["numeric_columns"]:
            lines.append("- No numeric-like columns detected")
        else:
            for column in profile["numeric_columns"][:12]:
                lines.append(
                    f"- `{column['column']}`: {column['min_numeric']} -> {column['max_numeric']}"
                )

        lines.extend(["", "### Sample categorical values", ""])
        categorical_columns = [
            column for column in profile["columns"] if column["top_values"]
        ]
        if not categorical_columns:
            lines.append("- No tracked categorical columns")
        else:
            for column in categorical_columns[:8]:
                summary = ", ".join(
                    f"{item['value']} ({item['count']:,})" for item in column["top_values"]
                )
                lines.append(f"- `{column['column']}`: {summary}")

        lines.extend(["", "### Sample rows", ""])
        for idx, row in enumerate(profile["sample_rows"], start=1):
            lines.append(f"- Row {idx}: `{json.dumps(row, ensure_ascii=True)}`")
        lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    WORKBENCH_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")

    profiles = []
    try:
        for dataset in DATASETS:
            profiles.append(analyze_dataset(conn, dataset))
        PROFILE_JSON_PATH.write_text(json.dumps(profiles, indent=2), encoding="utf-8")
        build_report(profiles)
    finally:
        conn.close()

    print(f"Built workbench database: {DB_PATH}")
    print(f"Wrote normalized CSV files to: {CSV_DIR}")
    print(f"Wrote profile JSON to: {PROFILE_JSON_PATH}")
    print(f"Wrote report to: {REPORT_MD_PATH}")


if __name__ == "__main__":
    main()
