# -*- coding: utf-8 -*-

import csv
import io
import re

from aqt import mw


def extract_directives(content: str) -> dict:
    directives = {}
    for line in content.splitlines():
        if not line.strip():
            continue
        if not line.lstrip().startswith("#"):
            break
        m = re.match(r"^\s*#\s*([A-Za-z0-9_\-]+)\s*:\s*(.+?)\s*$", line)
        if m:
            directives[m.group(1).lower()] = m.group(2)
    return directives


def strip_directive_lines(content: str) -> str:
    out = []
    skipping = True
    for line in content.splitlines():
        if skipping and line.strip().startswith("#"):
            continue
        skipping = skipping and not line.strip()
        if not skipping:
            out.append(line)
    return "\n".join(out)


def normalize_name(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[\s_\-]+", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    return s


def detect_cloze_in_text(content: str) -> bool:
    return bool(re.search(r"{{c\d+::", content))


def find_model_index_by_name(model_infos, name: str):
    if not name:
        return None
    target = name.strip().lower()
    alias_map = {
        "cloze": "cloze",
        "basic": "basic",
        "basic (and reversed card)": "basic (and reversed card)",
        "basic (type in the answer)": "basic (type in the answer)",
    }
    target = alias_map.get(target, target)
    for i, m in enumerate(model_infos):
        if m.name.strip().lower() == target:
            return i
    return None


def detect_csv_format(content: str):
    sample = content[:2048]
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = fallback_delimiter_detection(sample)
    reader = csv.reader(io.StringIO(content), delimiter=delimiter)
    rows = sum(1 for _ in reader)
    return delimiter, rows


def fallback_delimiter_detection(sample: str):
    lines = sample.split("\n")[:5]
    if not lines:
        return ","
    delims = [",", "\t", ";", "|"]
    delimiter_counts = {}
    for d in delims:
        counts = [line.count(d) for line in lines if line.strip()]
        if counts:
            avg = sum(counts) / len(counts)
            if len(set(counts)) == 1 and counts[0] > 0:
                delimiter_counts[d] = (avg, True)
            elif avg > 0:
                delimiter_counts[d] = (avg, False)
    if delimiter_counts:
        sorted_delims = sorted(
            delimiter_counts.items(),
            key=lambda x: (x[1][1], x[1][0]),
            reverse=True,
        )
        return sorted_delims[0][0]
    return ","


def get_delimiter_name(delimiter: str):
    names = {
        ",": "Comma (,)",
        "\t": "Tab",
        ";": "Semicolon (;)",
        "|": "Pipe (|)",
    }
    return names.get(delimiter, f"'{delimiter}'")


def auto_pick_note_type(content: str, delimiter: str, model_infos, header_check):
    # Prefer Cloze if we detect cloze patterns
    if detect_cloze_in_text(content):
        cloze_idx = find_model_index_by_name(model_infos, "Cloze")
        if cloze_idx is not None:
            try:
                cloze_model = mw.col.models.get(model_infos[cloze_idx].id)
                return (
                    model_infos[cloze_idx].name,
                    len(cloze_model["flds"]),
                    cloze_idx,
                )
            except Exception:
                pass  # fall through

    try:
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        rows = [r for r in reader if any(c.strip() for c in r)]
    except Exception:
        rows = []

    if not rows:
        return None, None, None

    # Header guess
    header_hint = header_check.isChecked()
    try:
        sniffer = csv.Sniffer()
        has_header_guess = sniffer.has_header(content[:2048])
    except Exception:
        has_header_guess = False
    has_header = header_hint or has_header_guess

    header = [c.strip() for c in rows[0]] if has_header else None
    sample_rows = rows[1:21] if has_header else rows[:20]
    col_counts = [len(r) for r in sample_rows] or [len(rows[0])]
    observed_cols = max(col_counts) if col_counts else len(rows[0])

    if not model_infos:
        return None, None, None

    best = None
    best_idx = None
    best_name = None
    best_fields = None

    header_norm = [normalize_name(h) for h in (header or [])]
    for idx, m in enumerate(model_infos):
        try:
            nt = mw.col.models.get(m.id)
            field_names = [f["name"] for f in nt["flds"]]
        except Exception:
            continue

        field_count = len(field_names)
        fields_norm = [normalize_name(x) for x in field_names]

        # header-name similarity
        score_name = 0
        if header_norm:
            for h in header_norm:
                if not h:
                    continue
                if h in fields_norm:
                    score_name += 3
                else:
                    if any(h in fn or fn in h for fn in fields_norm if fn):
                        score_name += 1

        # column closeness
        diff = abs(observed_cols - field_count)
        if diff == 0:
            score_cols = 3
        elif diff == 1:
            score_cols = 2
        elif diff == 2:
            score_cols = 1
        else:
            score_cols = 0

        score_tuple = (score_name, score_cols, -field_count)
        if (best is None) or (score_tuple > best):
            best = score_tuple
            best_idx = idx
            best_name = m.name
            best_fields = field_count

    if best_idx is None:
        return None, None, None

    return best_name, best_fields, best_idx
