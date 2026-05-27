import argparse
import csv
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Convert an Apollo contacts CSV to a recipients.csv file.")
    parser.add_argument("--input", type=Path, required=True, help="Path to the Apollo contacts CSV (e.g. apollo-contacts-export.csv)")
    parser.add_argument("--output", type=Path, default=Path("recipients.csv"), help="Path to the output CSV (default: recipients.csv)")
    parser.add_argument("--verified-only", action="store_true", default=True, help="Only include contacts with Verified email status")
    parser.add_argument("--all", action="store_false", dest="verified_only", help="Include all contacts regardless of verification status")
    
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file {args.input} does not exist.")
        return 1

    seen_emails = set()
    rows = []

    with args.input.open(newline="", encoding="utf-8") as in_file:
        reader = csv.DictReader(in_file)
        
        # Check if the expected columns exist
        headers = reader.fieldnames or []
        if "Email" not in headers:
            print("Error: Input CSV must contain an 'Email' column.")
            return 1

        for row in reader:
            email = row.get("Email", "").strip()
            if not email:
                continue
                
            if args.verified_only:
                status = row.get("Email Status", "").strip().lower()
                if status != "verified":
                    continue

            key = email.lower()
            if key in seen_emails:
                continue
            seen_emails.add(key)

            first_name = row.get("First Name", "").strip()
            last_name = row.get("Last Name", "").strip()
            # Combine first and last name, fallback to "there" if both are missing
            name = f"{first_name} {last_name}".strip() or "there"
            
            company = row.get("Company Name", "").strip() or "your company"

            rows.append({
                "email": email,
                "name": name,
                "company": company
            })

    if not rows:
        print("No valid recipients found to write.")
        return 0

    with args.output.open("w", newline="", encoding="utf-8") as out_file:
        writer = csv.DictWriter(out_file, fieldnames=["email", "name", "company"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully converted {len(rows)} contacts to {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
