import argparse
import csv
import mimetypes
import os
import smtplib
import ssl
import time
from datetime import datetime
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path


DEFAULT_SUBJECT = "Software Engineering Internship Inquiry - Keshav Dev Sharma"
DEFAULT_BODY = """Hi {name},

I hope you're having a great week!

I'm Keshav, a Computer Science undergraduate (Class of 2027) with a strong foundation in full-stack development (Python, JavaScript) and a keen interest in integrating AI/ML into web applications. 

I am very inspired by {company}'s work and technological innovation. I'm reaching out to inquire if you might have any upcoming Software Engineering Internship opportunities available on your team. I have hands-on experience building and testing web applications across both front-end and back-end, and I would love the opportunity to contribute and learn from the innovative engineers at {company}.

I would really appreciate any guidance, a brief chat about your experience at {company} if you have the time, or any advice you have for a prospective intern.

Thank you for your time and consideration!

Best regards,
Keshav Dev Sharma

GitHub: https://github.com/HWKDS
LinkedIn: https://linkedin.com/in/keshavdevsharma
Portfolio: https://hwkds.dev
x: https://x.com/KDSAMF
"""

@dataclass
class Recipient:
    email: str
    name: str
    company: str


def is_valid_email(email_address: str) -> bool:
    parsed = parseaddr(email_address)[1]
    if parsed != email_address:
        return False
    if parsed.count("@") != 1:
        return False
    local_part, domain = parsed.split("@", 1)
    if not local_part or not domain or "." not in domain:
        return False
    return True


def load_recipients(csv_path: Path) -> list[Recipient]:
    recipients: list[Recipient] = []
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        required = {"email", "name", "company"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

        for row_number, row in enumerate(reader, start=2):
            email_address = (row.get("email") or "").strip()
            name = (row.get("name") or "").strip() or "there"
            company = (row.get("company") or "").strip() or "your team"

            if not email_address:
                continue
            if not is_valid_email(email_address):
                print(f"Skipping invalid email at row {row_number}: {email_address}")
                continue

            recipients.append(Recipient(email=email_address, name=name, company=company))

    return recipients


def build_message(
    sender: str,
    recipient: Recipient,
    subject: str,
    body_template: str,
    attachments: list[Path],
    cc_addresses: list[str] = [],
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient.email
    if cc_addresses:
        message["Cc"] = ", ".join(cc_addresses)
    message["Subject"] = subject
    message.set_content(body_template.format(name=recipient.name, company=recipient.company))

    for attachment_path in attachments:
        ctype, encoding = mimetypes.guess_type(str(attachment_path))
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        
        with attachment_path.open("rb") as f:
            message.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=attachment_path.name,
            )

    return message


def preview_message(
    recipient: Recipient,
    subject: str,
    body_template: str,
    attachments: list[Path],
    cc_addresses: list[str] = [],
) -> str:
    body = body_template.format(name=recipient.name, company=recipient.company)
    attachment_names = ", ".join(a.name for a in attachments) if attachments else "none"
    lines = [
        f"To: {recipient.email}",
    ]
    if cc_addresses:
        lines.append(f"Cc: {', '.join(cc_addresses)}")
    
    lines.extend([
        f"Subject: {subject}",
        f"Attachments: {attachment_names}",
        "",
        body,
    ])
    return "\n".join(lines)


def send_email(host: str, port: int, username: str, password: str, message: EmailMessage) -> None:
    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        if port == 587:
            smtp.starttls(context=context)
            smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(message)


def wait_for_scheduled_start(start_at: str | None, wait_seconds: int | None) -> None:
    delay_seconds = 0.0

    if wait_seconds is not None:
        if wait_seconds < 0:
            raise ValueError("--wait-seconds must be >= 0")
        delay_seconds = float(wait_seconds)

    if start_at is not None:
        try:
            scheduled_time = datetime.strptime(start_at, "%Y-%m-%d %H:%M")
        except ValueError as exc:
            raise ValueError("--start-at must be in format YYYY-MM-DD HH:MM (24-hour local time)") from exc

        now = datetime.now()
        delta_seconds = (scheduled_time - now).total_seconds()
        if delta_seconds <= 0:
            raise ValueError("--start-at is in the past. Please choose a future time.")
        delay_seconds = delta_seconds

    if delay_seconds > 0:
        target_time = datetime.now().timestamp() + delay_seconds
        print(f"Scheduled start in {int(delay_seconds)} seconds.")
        print(f"Expected send start: {datetime.fromtimestamp(target_time).strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(delay_seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description="Send personalized internship outreach emails.")
    parser.add_argument("--recipients", required=True, type=Path, help="CSV with email,name,company columns")
    parser.add_argument("--attachments", type=Path, nargs="*", default=[], help="Optional paths to files to attach (e.g. resume.pdf cover_letter.pdf)")
    parser.add_argument("--cc", type=str, nargs="*", default=[], help="Optional CC email addresses")
    parser.add_argument("--subject", default=DEFAULT_SUBJECT, help="Email subject line")
    parser.add_argument("--body", default=DEFAULT_BODY, help="Plain-text email body template")
    parser.add_argument("--host", default=os.getenv("SMTP_HOST", "smtp.gmail.com"), help="SMTP host")
    parser.add_argument("--port", type=int, default=int(os.getenv("SMTP_PORT", "587")), help="SMTP port")
    parser.add_argument("--username", default=os.getenv("EMAIL_ADDRESS"), help="SMTP username / sender email")
    parser.add_argument("--password", default=os.getenv("EMAIL_PASSWORD"), help="SMTP password or app password")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between emails in seconds")
    parser.add_argument("--limit", type=int, default=0, help="Optional cap on number of emails to send")
    schedule_group = parser.add_mutually_exclusive_group()
    schedule_group.add_argument(
        "--wait-seconds",
        type=int,
        help="Wait this many seconds before script starts sending (not Gmail Scheduled tab)",
    )
    schedule_group.add_argument(
        "--start-at",
        help="Script starts sending at local time YYYY-MM-DD HH:MM (not Gmail Scheduled tab)",
    )

    parser.add_argument("--send", action="store_true", help="Actually send emails")
    parser.add_argument("--dry-run", action="store_true", help="Preview emails without sending")
    parser.add_argument("--preview", type=int, default=5, help="Number of emails to preview")
    parser.add_argument("--confirm", action="store_true", help="Ask before sending")

    args = parser.parse_args()

    if not args.recipients.exists():
        raise FileNotFoundError(f"Recipient CSV not found: {args.recipients}")
    for attachment in args.attachments:
        if not attachment.exists():
            raise FileNotFoundError(f"Attachment not found: {attachment}")
    if not args.username:
        raise ValueError("Missing sender email. Set EMAIL_ADDRESS or pass --username.")
    if args.send and not args.password:
        raise ValueError("Missing SMTP password. Set EMAIL_PASSWORD or pass --password.")

    recipients = load_recipients(args.recipients)
    if args.limit > 0:
        recipients = recipients[:args.limit]

    if not recipients:
        print("No recipients found.")
        return 0

    if args.dry_run or not args.send:
        print("DRY RUN MODE (no emails will be sent)")
        print()

        for index, recipient in enumerate(recipients[: args.preview], start=1):
            print(f"--- Preview {index} ---")
            print(f"Company: {recipient.company}")
            print(preview_message(recipient, args.subject, args.body, args.attachments, args.cc))
            print("-" * 60)

        print()
        print(f"Total recipients loaded: {len(recipients)}")
        return 0

    if args.confirm:
        confirm = input(f"You are about to send {len(recipients)} emails. Continue? (y/n): ")
        if confirm.lower() != "y":
            print("Cancelled.")
            return 0

    wait_for_scheduled_start(args.start_at, args.wait_seconds)
    if args.wait_seconds is not None or args.start_at is not None:
        print("Note: This is script-side scheduling. Gmail Scheduled tab is not used by SMTP sends.")

    for index, recipient in enumerate(recipients, start=1):
        message = build_message(args.username, recipient, args.subject, args.body, args.attachments, args.cc)
        send_email(args.host, args.port, args.username, args.password, message)
        print(f"Sent {index}/{len(recipients)} to {recipient.email} ({recipient.name})")
        time.sleep(max(args.delay, 0.0))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
