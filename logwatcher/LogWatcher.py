import os
import re
import time
import smtplib
import socket
import logging
from logging.handlers import RotatingFileHandler
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.txt")
LOG_FILE = os.path.join(BASE_DIR, "LogWatcher.log")
SCAN_INTERVAL = 600  # 10 minutes

# Setup logging with 5MB cap and truncation
logger = logging.getLogger()
logger.setLevel(logging.INFO)

log_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=0, mode='w')
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_format)
logger.addHandler(log_handler)

def load_config():
    config = {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith("#"):
                    key, val = line.strip().split('=', 1)
                    config[key.strip()] = val.strip()
    except Exception as e:
        logger.error(f"Error loading config: {e}")
    return config

def send_email(subject, body, recipients, smtp_server="smtp.commvault.com"):
    hostname = socket.gethostname()
    sender = f"noreply@{hostname}"

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid()
    msg['Reply-To'] = sender
    msg['X-Priority'] = '3'
    msg['X-Mailer'] = 'Python Email Client'
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_server) as server:
            server.send_message(msg)
        logger.info("Email sent successfully.")
    except Exception as e:
        logger.error(f"Error sending email: {e}")

def search_files(directory, regex):
    matches = []
    pattern = re.compile(regex, re.IGNORECASE)

    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            logger.info(f"Parsing file: {filepath}")
            try:
                with open(filepath, 'r', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            truncated_line = line.strip()[:200]
                            matches.append(f"{filepath}:{line_num}:{truncated_line}")
            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")
    return matches

def main_loop():
    while True:
        config = load_config()
        directory = config.get("directory")
        patterns = config.get("patterns", "")
        emails = config.get("emails", "").split(',')

        if not directory or not patterns or not emails:
            logger.warning("Invalid config. Skipping iteration.")
            time.sleep(SCAN_INTERVAL)
            continue

        regex = f"({patterns})"
        results = search_files(directory, regex)

        if results:
            MAX_LINES = 100
            MAX_LINE_LENGTH = 200

            grouped = defaultdict(list)
            match_count = 0

            for match in results:
                if match_count >= MAX_LINES:
                    break
                try:
                    file_path, line_num, line_content = match.split(":", 2)
                    grouped[file_path].append(f"{line_num}: {line_content.strip()[:MAX_LINE_LENGTH]}")
                    match_count += 1
                except ValueError:
                    logger.warning(f"Skipping malformed match line: {match}")

            body = "The following lines matched your pattern:\n\n"
            for file_path, lines in grouped.items():
                body += f"\n📄 File: {file_path}\n"
                body += "\n".join(f"  {line}" for line in lines)
                body += "\n"

            if len(results) > MAX_LINES:
                body += f"\n⚠️ Only the first {MAX_LINES} matches are shown (out of {len(results)})."

            send_email("LogWatcher Alert", body, emails)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main_loop()
