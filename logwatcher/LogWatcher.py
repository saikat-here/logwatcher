import os
import re
import time
import smtplib
import socket
import logging
import csv
from logging.handlers import RotatingFileHandler
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from collections import defaultdict
from codebert_filter import classify_line


BASE_DIR = "/opt/LogWatcher"

# Test mode file count. It will parse 5 files if test mode is set to config
test_mode_file_count = 5

# Save the matched string to CSV
CSV_DIR = os.path.join(BASE_DIR, "CSV")

# Setting pattern directory
pattern_dir = os.path.join(BASE_DIR, "pattern")

# Setup logging
LOG_DIR = os.path.join(BASE_DIR, "log")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "main.log")
MATCH_LOG_FILE = os.path.join(LOG_DIR, "matches.log")

CONFIG_FILE = os.path.join(BASE_DIR, "config.txt")

logger = logging.getLogger("LogWatcher")

# Main operational log (5 MB, no rotation)
op_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5, mode='w')
op_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Match log (10 MB, no rotation)
match_logger = logging.getLogger("MatchLogger")
match_logger.setLevel(logging.INFO)
match_handler = match_handler = RotatingFileHandler(MATCH_LOG_FILE, maxBytes=10*1024*1024, backupCount=50, mode='a', delay=True)
match_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

logger.addHandler(op_handler)
match_logger.addHandler(match_handler)

def save_matches_to_csv(matches):
    output_file=f"matched_strings_{time.time()}.csv"
    logger.info(f"Saving the matched strings to CSV")
    output_file = os.path.join(CSV_DIR, output_file)
    logger.info(f"File path: {output_file}")

    # unique_matches = set(match.split(":", 2)[-1].strip() for match in matches)
    
    with open(output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['log_line','matched_str', 'label'])  # Header

        for line, match_str in matches.items():
            log(f"Saving to CSV. Line: {line}, match_str: {match_str}",3)
            writer.writerow([line,match_str,""])  # Leave label blank for manual tagging
    logger.info(f"Matched strings are save to CSV")
    
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

def configure_logging():
    config = load_config()
    debug_level = int(config.get("debug", "0").strip())

    if debug_level >= 1:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    match_logger.setLevel(logging.INFO)
    logger.info(f"Debug mode level: {debug_level}")
    return debug_level
    
DEBUG_LEVEL = configure_logging()

def log(message, level=1):
    if DEBUG_LEVEL >= level:
        logger.debug(message)
        
def send_email(subject, body, recipients, smtp_server="smtp.commvault.com"):
    logger.info("Preparing email header and body")
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
    
    logger.info("Email header and body is ready")
        
    try:
        logger.info("Sending the email")
        with smtplib.SMTP(smtp_server) as server:
            server.send_message(msg)
        logger.info("Email sent successfully.")
    except Exception as e:
        logger.error(f"Error sending email: {e}")

def search_files(directory, compiled_patterns):
    matches = []
    for_csv_file = {}
    
    logger.info("Loading the exclusions list")
    exclusions = load_exclusions()
    email_matched_values = set()

    logger.info("Starting file parsing")

    file_count = test_mode_file_count
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.zip', '.bz2', '.gz', '.xz', '.7z', '.tar', '.rar')):
                logger.info(f"Skipping compressed file: {file}")
                continue

            if int(load_config().get("test_mode", "0").strip()):
                logger.info(f"Test mode is set to TRUE, remaining file count: {file_count}")

                if file_count < 1 and matches:
                    return matches, for_csv_file
                file_count-= 1
                
            filepath = os.path.join(root, file)
            log(f"Parsing file: {filepath}")
            try:
                log(f"Opening file: {filepath}",2) 
                with open(filepath, 'r', errors='ignore') as f:
                 log("File opened successfully",2)
                 for line_num, line in enumerate(f, 1):
                    log(f"Checking line for exclusion: '{line.strip()}' against exclusions: {exclusions}",2)
                    excluded = any(ex.lower() in line.lower() for ex in exclusions)
                    
                    if excluded:
                            log(f"Matched line is part of the exclusion list. {filepath}:{line_num}:{line}", 2)
                            continue
                        
                    for pattern, pattern_text in compiled_patterns:
                        log(f"Pattern: {pattern}",3)
                        log(f"pattern_text: {pattern_text}",3)
                        match_obj = pattern.search(line)
                        log(f"Matche: {match_obj}",3)
                        if match_obj:
                            full_line = line.strip()
                            match_log_entry = f"{filepath}:{line_num}:{full_line}"
                            match_logger.info(f"{match_log_entry} [matched pattern: {pattern_text}]")

                            if classify_line(match_obj.group(0)) == "false_positive":
                                log(f"CodeBERT marked as SAFE. Matched str: {match_obj.group(0)}, Full Line: {line}", 2)
                                continue

                            log(f"CodeBERT marked as UNSAFE. Matched str: {match_obj.group(0)}, Full Line: {line}", 1)
                            matched_value = match_obj.group(0)[:200]
                            log("Checking if the matched string already added for email",3)
                            if matched_value not in email_matched_values:
                                log(f"String is not part of email content, adding that. String: {matched_value}",2)
                                email_matched_values.add(matched_value)
                                email_entry = f"{filepath}:{line_num}:{matched_value}"
                                matches.append(email_entry)
                                for_csv_file[line] = matched_value
                            else:
                                log(f"This matching line is already present in the email content; skipping.: '{matched_value}' from {filepath}:{line_num}",2)
                            log(f"Matched by: {pattern_text} in {filepath}:{line_num}", 2)
                            break
    
            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")
            
    return matches, for_csv_file

def load_patterns():
    
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


def load_exclusions():
    exclude_file = os.path.join(pattern_dir, "excluded_lines.txt")
    exclusions = set()
    try:
        with open(exclude_file, 'r') as f:
            for line in f:
                cleaned = line.strip()
                if cleaned and not cleaned.startswith("#"):
                    exclusions.add(cleaned)
    except FileNotFoundError:
        logger.info("No excluded_lines.txt found. No exclusions applied.")
    except Exception as e:
        logger.error(f"Error reading excluded_lines.txt: {e}")
    return exclusions


def main_loop():
    DEFAULT_SCAN_INTERVAL = 600  # fallback

    while True:
        start_time = time.time()

        config = load_config()
        SCAN_INTERVAL = int(load_config().get("scan_interval", DEFAULT_SCAN_INTERVAL))

        logger.info("=" * 66)
        logger.info(f"{' Starting Scan ':=^66}")
        logger.info("=" * 66)
        logger.info(f"SCAN FREQUENCY: {SCAN_INTERVAL} SEC")

        directory = config.get("directory")
        emails = config.get("emails", "").split(',')
        compiled_patterns = load_patterns()  
        
        if not directory or not compiled_patterns or not emails:
            logger.warning("Invalid config. Skipping iteration.")
        else:
            results, for_csv_file = search_files(directory, compiled_patterns)

            if results:
                if int(config.get("save_to_CSV", "0").strip()):
                    logger.info(f"Saving the matched string to CSV before sending email")
                    save_matches_to_csv(for_csv_file)
                else:
                    match_logger.info(f"save_to_CSV set to FALSE, not saving the matched result to CSV")
        
                MAX_LINES = 200
                MAX_LINE_LENGTH = 200

                grouped = defaultdict(list)
                match_count = 0

                for match in results:
                    if match_count >= MAX_LINES:
                        break
                    try:
                        # file_path, line_num, line_content = match.split(":", 2)
                        # grouped[file_path].append(f"{line_num}: {line_content.strip()[:MAX_LINE_LENGTH]}")
                        file_path, line_num, line_content = match.split(":", 2)
                        grouped[file_path].append(f"{line_num}: {line_content.strip()}")
                        match_count += 1
                    except ValueError:
                        logger.warning(f"Skipping malformed match line: {match}")

                body = "The following lines matched your pattern:\n\n"
                for file_path, lines in grouped.items():
                    body += f"\n📄 File: {file_path}\n"
                    body += "\n".join(f"  {line}" for line in lines)
                    body += "\n"
                    body += "\n"

                if len(results) > MAX_LINES:
                    body += f"\n⚠️ Only the first {MAX_LINES} matches are shown (out of {len(results)}). Please check {MATCH_LOG_FILE} log or {CSV_DIR}for complete result."

                send_email("LogWatcher Alert", body, emails)

        elapsed = time.time() - start_time
        logger.info(f"Cycle completed in {elapsed//60} mins.")

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main_loop()
