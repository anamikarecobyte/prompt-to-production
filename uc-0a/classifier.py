"""
UC-0A — Complaint Classifier
Deterministic keyword-based classifier guided by agents.md and skills.md.
"""
import argparse
import csv
import re
import sys

VALID_CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
]

URGENT_KEYWORDS = [
    "injury", "child", "children", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse"
]

CATEGORY_RULES = [
    ({"pothole", "potholes", "pothole"}, "Pothole"),
    ({"flood", "flooded", "flooding", "knee-deep", "waterlogged", "waterlogging"}, "Flooding"),
    ({"streetlight", "streetlights", "street light", "street lights", "lamp", "floodlight"}, "Streetlight"),
    ({"garbage", "waste", "trash", "rubbish", "overflowing", "dumped", "litter", "dead animal", "rotting"}, "Waste"),
    ({"noise", "loud", "music", "blaring", "midnight", "loudspeaker", "dj"}, "Noise"),
    ({"road surface", "road damaged", "cracked", "sinking", "road crack", "broken road", "tarmac", "asphalt"}, "Road Damage"),
    ({"heritage", "heritage street", "old city", "historic", "monument"}, "Heritage Damage"),
    ({"heat", "heatwave", "extreme heat", "hot weather", "scorching", "sunstroke"}, "Heat Hazard"),
    ({"drain blocked", "drainage blocked", "clogged drain", "sewer blocked", "manhole", "blocked drain", "drainage"}, "Drain Blockage"),
    ({"footpath", "sidewalk", "tiles broken", "pavement"}, "Road Damage"),
]

EXCLUDE_FROM_REASONS = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "for", "of", "to", "and", "or", "near", "with", "this", "that"}


def _find_citing_words(text: str, max_words: int = 8) -> str:
    """Extract meaningful words from text to cite in the reason field."""
    words = re.findall(r"[A-Za-z]{3,}", text)
    meaningful = [w for w in words if w.lower() not in EXCLUDE_FROM_REASONS]
    return " ".join(meaningful[:max_words]) if meaningful else text[:50]


def _match_category(description: str) -> str:
    """Match description against keyword rules. Returns category or Other."""
    lower = description.lower()
    for keywords, category in CATEGORY_RULES:
        if any(kw in lower for kw in keywords):
            return category
    return "Other"


def _is_urgent(description: str) -> bool:
    """Check if description contains any urgency keywords."""
    lower = description.lower()
    return any(kw in lower for kw in URGENT_KEYWORDS)


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Input: dict with 'description' (and optionally 'complaint_id').
    Output: dict with complaint_id, category, priority, reason, flag.
    """
    description = row.get("description", "").strip()
    complaint_id = row.get("complaint_id", "")

    if not description:
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Low",
            "reason": "Unable to classify — empty description",
            "flag": "NEEDS_REVIEW",
        }

    category = _match_category(description)
    priority = "Urgent" if _is_urgent(description) else "Standard"
    flag = "NEEDS_REVIEW" if category == "Other" else ""

    citing = _find_citing_words(description)
    reason = f"Based on description citing: {citing}"

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    Handles missing files, bad rows, and nulls gracefully.
    """
    try:
        with open(input_path, newline="", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            if "description" not in (reader.fieldnames or []):
                print(f"Error: Input CSV missing 'description' column.", file=sys.stderr)
                sys.exit(1)

            rows = []
            for row in reader:
                rows.append(classify_complaint(row))

    except FileNotFoundError:
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    except csv.Error as e:
        print(f"Error: Malformed CSV: {e}", file=sys.stderr)
        sys.exit(1)

    fieldnames = ["complaint_id", "description", "category", "priority", "reason", "flag"]

    try:
        with open(input_path, newline="", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            original_rows = list(reader)
    except Exception:
        original_rows = [{"description": ""}] * len(rows)

    with open(output_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for orig, classified in zip(original_rows, rows):
            writer.writerow({
                "complaint_id": classified["complaint_id"],
                "description": orig.get("description", ""),
                "category": classified["category"],
                "priority": classified["priority"],
                "reason": classified["reason"],
                "flag": classified["flag"],
            })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
