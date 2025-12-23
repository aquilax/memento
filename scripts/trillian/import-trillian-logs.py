# A script to import Trillian logs from sudirectories under a base directory
# A base directory contains the following subdirectories: ICQ, IRC, MSN, YAHOO
# where each of them corresponds to the platform.
# In each of those directories there are files containing logs for each contact chat sessions.
# The name of the file is [ID].log where id is the platform identifier for the user.
# The content of the files:
# Each file one or more sections e.g.:
#
# ```
# Session Start (ICQ - 000001:Alice): Thu Jan 24 21:54:39 2002
# Alice: Hi Bob
# Bob: Hi Alice.
# What a nice day!
# Session Close (Alice): Thu Jan 24 23:05:59 2002
# ```
# Where Bob is the owner of the account, Alice is the one with UIN 000001
#
# When converting to messages assume 5 second intervals between messages to calculate timestamps.
#
# Usage:
# python3 import-trillian-logs.py contacts -d "TrillianLogs/" > contacts.json
# python3 import-trillian-logs.py messages -d "TrillianLogs/" > messages.jsonl

import os
import json
import argparse
import sys
from datetime import datetime, timedelta
import re
from collections import OrderedDict

# Map directory names to platforms
PLATFORM_MAP = {
    "ICQ": "icq",
    "IRC": "irc",
    "MSN": "msn",
    "YAHOO": "yahoo"
}

def parse_session_start(line):
    # Session Start (ICQ - 000001:Alice): Thu Jan 24 21:54:39 2002
    match = re.match(r"Session Start \((\w+) - ([^:]+):(.+?)\): (.+)", line)
    if match:
        platform_type, user_id, name, date_str = match.groups()
        dt = datetime.strptime(date_str.strip(), "%a %b %d %H:%M:%S %Y")
        return {
            "platform": PLATFORM_MAP.get(platform_type, platform_type.lower()),
            "user_id": user_id,
            "name": name.strip(),
            "timestamp": dt
        }
    return None

def parse_session_close(line):
    # Session Close (Alice): Thu Jan 24 23:05:59 2002
    match = re.match(r"Session Close \((.+?)\): (.+)", line)
    if match:
        name, date_str = match.groups()
        dt = datetime.strptime(date_str.strip(), "%a %b %d %H:%M:%S %Y")
        return {
            "name": name.strip(),
            "timestamp": dt
        }
    return None

def parse_message_line(line):
    # "Alice: Hi Bob"
    match = re.match(r"^(.+?): (.*)$", line)
    if match:
        sender, text = match.groups()
        return {
            "sender": sender,
            "text": text
        }
    return None

def collect_contacts(directory, encoding='utf-8'):
    contacts = {}
    for platform_dir, platform in PLATFORM_MAP.items():
        platform_path = os.path.join(directory, platform_dir)
        if os.path.isdir(platform_path):
            for filename in os.listdir(platform_path):
                if filename.endswith('.log'):
                    filepath = os.path.join(platform_path, filename)
                    # filename (without .log) is the contact UIN
                    contact_id = filename[:-4]
                    with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                        # find first Session Start line to get contact display name and account owner UIN
                        for l in f:
                            session_info = parse_session_start(l.strip())
                            if session_info:
                                contact_name = session_info['name']

                                contact_key = f"{platform}_{contact_id}"
                                if contact_key not in contacts:
                                    contacts[contact_key] = OrderedDict({
                                        "name": contact_name,
                                        "platform_ids": [{
                                            "id": contact_id,
                                            "platform": platform,
                                            "avatar": "",
                                            "meta": {}
                                        }]
                                    })
                                break

    return list(contacts.values())

def collect_messages(directory, on_message, encoding='utf-8'):
    for platform_dir, platform in PLATFORM_MAP.items():
        platform_path = os.path.join(directory, platform_dir)
        if os.path.isdir(platform_path):
            for filename in os.listdir(platform_path):
                if filename.endswith('.log'):
                    filepath = os.path.join(platform_path, filename)
                    # filename (without .log) is the contact UIN
                    contact_id = filename[:-4]

                    with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                        lines = f.readlines()

                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        session_info = parse_session_start(line)
                        if session_info:
                            session_start_time = session_info['timestamp']
                            # session_info['user_id'] is the account owner's UIN
                            account_owner_id = session_info['user_id']
                            contact_name = session_info['name']

                            # Parse messages until session close
                            i += 1
                            msg_index = 0
                            while i < len(lines):
                                line = lines[i].strip()

                                # Check for session close or next session start
                                if line.startswith("Session Close") or line.startswith("Session Start"):
                                    i += 1
                                    break

                                # Parse message line (format: "sender: text")
                                msg_info = parse_message_line(line)
                                if msg_info:
                                    sender = msg_info['sender']
                                    text = msg_info['text']

                                    # Collect continuation lines for this message
                                    i += 1
                                    while i < len(lines):
                                        next_line = lines[i].strip()

                                        # Stop if we hit session marker or next message
                                        if (next_line.startswith("Session Close") or
                                            next_line.startswith("Session Start") or
                                            parse_message_line(next_line)):
                                            break

                                        # Add continuation line to message text
                                        if next_line:
                                            text += "\n" + next_line
                                        i += 1

                                    # Calculate timestamp (5 second intervals)
                                    msg_time = session_start_time + timedelta(seconds=msg_index * 5)

                                    # Determine from/to based on sender
                                    if sender == contact_name:
                                        # Message from contact
                                        from_id = contact_id
                                        to_id = account_owner_id
                                    else:
                                        # Message from account owner
                                        from_id = account_owner_id
                                        to_id = contact_id

                                    message = OrderedDict({
                                        "ts": msg_time.isoformat() + "Z",
                                        "platform": platform,
                                        "from": from_id,
                                        "to": {
                                            "type": "user",
                                            "user_id": to_id
                                        },
                                        "text": text,
                                        "meta": {}
                                    })

                                    on_message(message)
                                    msg_index += 1
                                else:
                                    i += 1
                        else:
                            i += 1

def cb_on_message(message):
    print(json.dumps(message, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="Import Trillian logs")
    parser.add_argument('command', choices=['contacts', 'messages'])
    parser.add_argument('-d', '--directory', required=True, help='Base directory containing Trillian logs')
    parser.add_argument('-e', '--encoding', default='utf-8', help='File encoding (default: utf-8)')

    args = parser.parse_args()

    if args.command == 'contacts':
        contacts = collect_contacts(args.directory, args.encoding)
        json.dump(contacts, sys.stdout, indent=2, ensure_ascii=False)
    elif args.command == 'messages':
        collect_messages(args.directory, cb_on_message, args.encoding)

if __name__ == '__main__':
    main()
