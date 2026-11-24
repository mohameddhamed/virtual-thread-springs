#!/usr/bin/env python3
"""Count a canonical abstract and optionally check the dated OTDK38 profile.

Standard library only. Reads UTF-8 files and writes a JSON report to stdout.
Exit 0: selected checks pass; 1: selected checks fail; 2: input/argument error.
The count-only profile asserts no institutional length requirement.
"""

import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata


def read_text(path):
    return Path(path).read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").strip()


def phrase_key(text):
    return " ".join(re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold(), flags=re.UNICODE))


def check(body, profile="count-only", title=None, keywords=None):
    paragraphs = [p.strip() for p in re.split(r"\n[ \t]*\n+", body) if p.strip()]
    report = {
        "profile": profile,
        "convention": "Unicode code points; internal whitespace included; LF newlines; outer whitespace excluded",
        "characters": len(body),
        "characters_without_whitespace": sum(not c.isspace() for c in body),
        "utf16_units": len(body.encode("utf-16-le")) // 2,
        "paragraphs": len(paragraphs),
        "paragraph_characters": [len(p) for p in paragraphs],
        "unicode_nfc": body == unicodedata.normalize("NFC", body),
        "errors": [],
        "notes": [],
    }
    if not body:
        report["errors"].append("Abstract body is empty.")
    if not report["unicode_nfc"]:
        report["notes"].append("Canonicalize the final text and all copies to Unicode NFC, then rerun counts.")
    if profile == "otdk38":
        if not 800 <= len(body) <= 2500:
            report["errors"].append("OTDK38 body must contain 800-2500 characters under the reported convention.")
        if len(paragraphs) != 4:
            report["errors"].append("The four-component profile requires exactly four logical paragraphs.")
        if any(len(p) < 200 for p in paragraphs):
            report["errors"].append("Each of the four components must contain at least 200 characters.")
        report["notes"].append("This dated national profile is not automatically a faculty TDK requirement.")
    else:
        report["notes"].append("Counts only: no official limit or component minimum has been asserted.")
    if keywords is not None:
        keys = [phrase_key(k) for k in keywords]
        invalid = [i + 1 for i, key in enumerate(keys) if not key]
        duplicates = len(keys) != len(set(keys))
        overlap = []
        if title is not None:
            title_key = " " + phrase_key(title) + " "
            overlap = [i + 1 for i, key in enumerate(keys) if key and " " + key + " " in title_key]
        report["keywords"] = {
            "count": len(keywords), "duplicate_normalized_entries": duplicates,
            "invalid_entry_numbers": invalid, "title_overlap_entry_numbers": overlap,
            "title_checked": title is not None,
        }
        if len(keywords) != 5:
            report["errors"].append("Five keywords are required for this optional national keyword check.")
        if invalid or duplicates:
            report["errors"].append("Keywords must be nonempty, meaningful and distinct.")
        if title is None:
            report["errors"].append("Supply a title to check that keywords are absent from it.")
        elif not phrase_key(title):
            report["errors"].append("Title is empty or contains no words.")
        elif overlap:
            report["errors"].append("One or more keywords occur literally in the title.")
        report["notes"].append("Human review must also check keyword relevance, near-duplicates and inflections.")
    report["passed"] = not report["errors"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("abstract_file", type=Path)
    parser.add_argument("--profile", choices=["count-only", "otdk38"], default="count-only")
    parser.add_argument("--title-file", type=Path)
    parser.add_argument("--keywords-file", type=Path, help="One keyword or phrase per nonblank line.")
    args = parser.parse_args()
    try:
        body = read_text(args.abstract_file)
        title = read_text(args.title_file) if args.title_file else None
        keywords = ([x.strip() for x in read_text(args.keywords_file).splitlines() if x.strip()]
                    if args.keywords_file else None)
    except (OSError, UnicodeError) as error:
        parser.error(str(error))
    result = check(body, args.profile, title, keywords)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
