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

BASE_DIR = "/opt/LogWatcher"

# Setup logging
LOG_DIR = os.path.join(BASE_DIR, "log")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "LogWatcher.log")
MATCH_LOG_FILE = os.path.join(LOG_DIR, "matches.log")

CONFIG_FILE = os.path.join(BASE_DIR, "config.txt")

logger = logging.getLogger("LogWatcher")
logger.setLevel(logging.DEBUG)

# Main operational log (5 MB, no rotation)
op_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=0, mode='w')
op_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Match log (10 MB, no rotation)
match_logger = logging.getLogger("MatchLogger")
match_logger.setLevel(logging.INFO)
match_handler = RotatingFileHandler(MATCH_LOG_FILE, maxBytes=10*1024*1024, backupCount=0, mode='w')
match_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

logger.addHandler(op_handler)
match_logger.addHandler(match_handler)


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

def search_files(directory, compiled_patterns):
    matches = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.zip', '.bz2', '.gz', '.xz', '.7z', '.tar', '.rar')):
                logger.info(f"Skipping compressed file: {file}")
                continue

            filepath = os.path.join(root, file)
            logger.info(f"Parsing file: {filepath}")
            try:
                with open(filepath, 'r', errors='ignore') as f:
                 for line_num, line in enumerate(f, 1):
                    for pattern, pattern_text in compiled_patterns:
                        if pattern.search(line):
                            full_line = line.strip()
                            match_log_entry = f"{filepath}:{line_num}:{full_line}"
                            match_logger.info(f"{match_log_entry} [matched pattern: {pattern_text}]")

                            truncated_line = full_line[:200]
                            email_entry = f"{filepath}:{line_num}:{truncated_line}"
                            matches.append(email_entry)
                            logger.debug(f"Matched by: {pattern_text} in {filepath}:{line_num}")
                            break

            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")
    return matches

def load_patterns():
    pattern_dir = os.path.join(BASE_DIR, "pattern")
    default_file = os.path.join(pattern_dir, "defaultpattern.txt")
    custom_file = os.path.join(pattern_dir, "custompattern.txt")

    patterns = set()
    for file_path in [default_file, custom_file]:
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    cleaned = line.strip()
                    if cleaned and not cleaned.startswith("#"):
                        patterns.add(cleaned)
        except FileNotFoundError:
            logger.warning(f"Pattern file not found: {file_path}")
        except Exception as e:
            logger.error(f"Error reading pattern file {file_path}: {e}")

    return [(re.compile(p, re.IGNORECASE), p) for p in patterns]


def main_loop():
    
    DEFAULT_SCAN_INTERVAL = 600  # fallback

    while True:
    start_time = time.time()

    try:
        config = load_config()
        SCAN_INTERVAL = int(config.get("scan_interval", DEFAULT_SCAN_INTERVAL))

        logger.info("=" * 66)
        logger.info(f"{' Starting Scan ':=^66}")
        logger.info("=" * 66)
        logger.info(f"SCAN FREQUENCY: {SCAN_INTERVAL} SEC")

        directory = config.get("directory")
        compiled_patterns = load_patterns()
        emails = config.get("emails", "").split(',')

        if not directory or not compiled_patterns or not emails:
            logger.warning("Invalid config. Skipping iteration.")

        else:
            results = search_files(directory, compiled_patterns)
            # [ ... email and reporting logic ... ]

    except Exception as e:
        logger.error(f"Exception during scan loop: {e}")

    elapsed = time.time() - start_time
    logger.info(f"⏱️ Cycle completed in {elapsed:.2f} seconds.")

    time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main_loop()
