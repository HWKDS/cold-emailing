# Cold Emailer

This codebase helps you automatically send personalized internship inquiry outreach emails to a defined list of contacts (like an Apollo export). It supports mapping names and companies seamlessly into a customizable email template and optionally attaching your resume.

## Files

- `cold_emailer.py`: The main script that sends the emails.
- `convert_apollo_to_recipients.py`: A dedicated script to clean and convert an Apollo CSV export into the properly formatted `recipients.csv`.
- `generate_recipients_csv.py`: A utility script to generate templates, import from simple text files, or read Apollo exports.

## 1. Setup Your Credentials

Create a `.env` file in this folder to hold your email credentials. **This file is git-ignored and should never be shared.**

```env
EMAIL_ADDRESS=your.email@example.com
EMAIL_PASSWORD=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

_Note: Use an App Password (not your standard sign-in password) if your email provider (like Gmail) requires it for external script access._

## 2. Prepare Your Recipients

The `cold_emailer.py` script needs a `recipients.csv` file with exactly three columns: `email`, `name`, and `company`. You can create this easily using the included utilities depending on where your contacts came from:

**If you have an Apollo contacts export:**
Run the dedicated converter to extract only "Verified" emails and automatically format the full name and company:

```bash
python convert_apollo_to_recipients.py --input apollo-contacts-export.csv
```

_(Optional flags: `--all` to include unverified emails, or `--output my_list.csv` to save to a different file name)_

**If you have a plain text file of emails (`emails.txt`):**

```bash
python generate_recipients_csv.py --emails-file emails.txt --default-company "Example Corp" --output recipients.csv
```

_(Line formats supported: `email@example.com`, or `email@example.com,Name`, or `email@example.com,Name,Company`)_

**If you just want a blank template to fill out manually in Excel:**

```bash
python generate_recipients_csv.py --template-rows 20 --output recipients.csv
```

## 3. Test Run (Dry Run)

Always preview your emails before blasting them out! This will print exactly what the email looks like without actually sending it:

```bash
python cold_emailer.py --recipients recipients.csv --dry-run
```

## 4. Send For Real

When you are happy with the preview and your `.env` is setup, fire away:

```bash
python cold_emailer.py --recipients recipients.csv --send --confirm
```

**Send after a delay (e.g. 10 minutes):**

```bash
python cold_emailer.py --recipients recipients.csv --send --confirm --wait-seconds 600
```

_(Note: This leaves the terminal open and waits script-side before sending. It does not use the Gmail 'Scheduled' tab.)_

**Send at a specific local time:**

```bash
python cold_emailer.py --recipients recipients.csv --send --confirm --start-at "2026-05-30 08:30"
```

## Useful Optional Flags for `cold_emailer.py`

- `--subject`: Change the subject line of the email.
- `--body`: Use a different plain-text email body template.
- `--limit 5`: Send to only the first set of rows (useful for testing on a small batch first).
- `--delay 2`: Wait `N` seconds between each email send to prevent rate-limiting.
- `--attachments path/to/resume.pdf path/to/cover_letter.pdf`: Attach one or more files to every email.
- `--preview 5`: Show only the first N previews in a dry-run.

## Important Note

To stay compliant and avoid spam/privacy issues, ONLY use contacts you already have or manually sourced public contact details. Do not spam.
