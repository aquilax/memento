# A python script which given a base directory `Google Chat/Groups/` from
# Google Takeout export of Google Chat logs, walks through the subdirectories,
# collects contacts or messages and generates the structs defined in message.go.
#
# Each subdirectory contains two files:
#
# `group_info.json`
# {
#   "members": [
#     {
#       "name": "Alice",
#       "email": "alice@example.com",
#       "user_type": "Human"
#     },
#     {
#       "name": "Bob",
#       "email": "bob@example.com",
#       "user_type": "Human"
#     }
#   ]
# }
#
#`messages.json`
# {
#   "messages": [
#     {
#       "creator": {
#         "name": "Alive",
#         "email": "alice@example.com",
#         "user_type": "Human"
#       },
#       "created_date": "Sunday, 1 March 2000 at 09:33:50 UTC",
#       "text": "Hi Bob",
#       "topic_id": "1379OfKLSoU"
#     }
#   ]
# }

# Usage:
# python3 import-google-chat-takeout.py contacts -d "Google Chat/Groups/" > contacts.json
# python3 import-google-chat-takeout.py messages -d "Google Chat/Groups/" > messages.jsonl

import os
import json
import argparse
import sys
from datetime import datetime, timezone

PLATFORM = "google"

def parse_date(date_str):
    # "Sunday, 1 March 2000 at 09:33:50 UTC"
    dt = datetime.strptime(date_str[:-4], "%A, %d %B %Y at %H:%M:%S")
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

def collect_contacts(directory):
    contacts = {}
    for root, _dirs, files in os.walk(directory):
        if 'group_info.json' in files:
            with open(os.path.join(root, 'group_info.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for member in data.get('members', []):
                    email = member['email']
                    if email not in contacts:
                        platform_id = {
                            "id": email,
                            "platform": PLATFORM,
                            "avatar": "",
                            "meta": {}
                        }
                        contacts[email] = {
                            "name": member['name'],
                            "platform_ids": [platform_id]
                        }
    return list(contacts.values())

def collect_messages(directory, on_message):
    for root, _dirs, files in os.walk(directory):
        if 'messages.json' in files and 'group_info.json' in files:
            with open(os.path.join(root, 'group_info.json'), 'r', encoding='utf-8') as f:
                group_data = json.load(f)
            members = group_data.get('members', [])
            with open(os.path.join(root, 'messages.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for msg in data.get('messages', []):
                    creator = msg['creator']
                    if len(members) == 2:
                        # Direct message
                        other = [m for m in members if m['email'] != creator['email']][0]
                        to = {
                            "type": "user",
                            "user_id": other['email']
                        }
                    else:
                        # Group
                        to = {
                            "type": "group",
                            "group_id": msg['topic_id']
                        }
                    # if not 'text' in msg:
                    #     raise Exception(msg)
                    message = {
                        "ts": parse_date(msg['created_date']),
                        "platform": PLATFORM,
                        "from": creator['email'],
                        "to": to,
                        "text": msg.get('text', ''),
                        "meta": {
                            "topic_id": msg['topic_id'],
                        }
                    }
                    on_message(message)

def cb_on_message(message):
    print(json.dumps(message, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="Import Google Chat Takeout data")
    parser.add_argument('command', choices=['contacts', 'messages'])
    parser.add_argument('-d', '--directory', required=True, help='Base directory containing Google Chat/Groups/')

    args = parser.parse_args()

    if args.command == 'contacts':
        contacts = collect_contacts(args.directory)
        json.dump(contacts, sys.stdout, indent=2)
    elif args.command == 'messages':
        collect_messages(args.directory, cb_on_message)

if __name__ == '__main__':
    main()
