# skills.md

skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint into category, priority, reason, and review flag.
    input: A JSON object with a "description" field containing the raw complaint text.
    output: A JSON object with fields: category (string), priority (string), reason (string), flag (string or blank).
    error_handling: If description is empty or unreadable, output category: Other, priority: Low, reason: "Unable to classify — empty description", flag: NEEDS_REVIEW.

  - name: batch_classify
    description: Reads an input CSV of complaints, applies classify_complaint to each row, and writes the classified output CSV.
    input: A CSV file path with columns including "description" (and optionally an id column).
    output: A CSV file with columns: id, description, category, priority, reason, flag.
    error_handling: If the input file is missing or malformed, exit with a clear error message. Rows with missing descriptions are classified as category: Other, flag: NEEDS_REVIEW.
