import os
import json
import argparse
import sys
import csv
from datetime import datetime, timezone
from collections import OrderedDict
from lxml import objectify
import xml.etree.ElementTree as ET

def format_utc_seconds(dt):
  return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def collect_contacts(directory, encoding):
  contacts = {}
  for filename in os.listdir(directory):
    if filename.endswith('.csv'):
      filepath = os.path.join(directory, filename)
      with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
          number = row[2].lstrip("'")
          name = row[3].lstrip("'").rstrip('?')
          contacts[number] = OrderedDict({
            "name": name,
            "platforms": [{
              "id": str(number),
              "platform": "sms",
              "name": name,
              "avatar": "",
              "meta": {},
            }]
          })
  return list(contacts.values())

def parse_date_time(dt):
  if not dt:
    return None

  formats = [
    "%d.%m.%Y г. %H:%M:%S",  # 29.12.2003 г. 21:40:05
    "%d.%m.%Y г. %H:%M",     # 29.12.2003 г. 21:40
    "%d.%m.%y 'г.' %H:%M",
    "%m/%d/%y %H:%M:%S",     # 03/01/09 18:13:51
    "%y.%m.%d 'y.' %H:%M",   # 09.11.02 'y.' 19:29 (from your XML)
    "%d.%m.%Y %H:%M:%S",     # 29.12.2003 21:40:05 (without suffix)
    "%d %m %Y %H %M %S",     # 29.12.2003 21:40:05 (without suffix)
    "%Y-%m-%d %H:%M:%S",     # Standard ISO format
    "%d/%m/%Y %H:%M:%S",
  ]

  for fmt in formats:
    try:
      return datetime.strptime(dt.strip(), fmt)
    except ValueError:
      continue

  raise Exception(f"Unknown time format: {dt}")

def collect_messages_xml(file_name, user_id, on_message, encoding):
  with open(file_name, 'r', encoding=encoding, errors='ignore') as f:
    content = f.read()
  root = ET.fromstring(content)
  for message in root.findall('MESSAGE'):
    msg = {child.tag: child.text for child in message}
    mfrom = msg['TELNUM']
    if msg['DATE'] is None:
      continue
    ts = parse_date_time(msg['DATE'])
    message = OrderedDict({
      'ts': format_utc_seconds(ts),
      'platform': 'sms',
      'from': str(mfrom),
      'to': user_id,
      'text': msg['TEXT'],
    })
    on_message(message)

def collect_messages_csv(file_name, user_id, on_message, encoding):
  with open(file_name, 'r', encoding=encoding, errors='ignore') as f:
    reader = csv.DictReader(f, delimiter=";")
    for row in reader:
      ts = parse_date_time(row['Date'])
      number = row['Number']
      text = row['Text']
      message = OrderedDict({
        'ts': format_utc_seconds(ts),
        'platform': 'sms',
        'from': str(number),
        'to': user_id,
        'text': text,
      })
      on_message(message)

def get_number(num):
  a = num.split('<')
  if len(a) > 1:
    return a[0].strip()
  return num

def collect_messages_txt(file_name, user_id, on_message, encoding):
  records = []
  with open(file_name, 'r', encoding=encoding, errors='ignore') as f:
    current_record = {}
    # We use this to capture multi-line messages
    capturing_message = False
    message_lines = []

    for line in f:
        # Step 1: Detect the start of a new record
        if line.startswith("Received SMS."):
            # If we were already working on a record, save it before starting new one
            if current_record:
                current_record['message'] = "\n".join(message_lines).strip()
                records.append(current_record)

            # Reset for the new record
            current_record = {}
            message_lines = []
            capturing_message = False
            continue

        # Step 2: Extract specific fields
        if line.startswith("Id:"):
            current_record['id'] = line.replace("Id:", "").strip()
        elif line.startswith("Date:"):
            date_str = line.replace("Date:", "").strip()
            current_record['date'] = parse_date_time(date_str)
        elif line.startswith("Numbers:"):
            current_record['numbers'] = get_number(line.replace("Numbers:", "").strip())
            # After 'Numbers:', the remaining lines until the next separator are the message
            capturing_message = True

        # Step 3: Capture the message body
        elif capturing_message and not line.startswith("---") and line != "":
            message_lines.append(line)

    # Add the very last record after the loop finishes
    if current_record:
        current_record['message'] = "\n".join(message_lines).strip()
        records.append(current_record)

  for record in records:
    message = OrderedDict({
      'ts': format_utc_seconds(record['date']),
      'platform': 'sms',
      'from': str(record['numbers']),
      'to': user_id,
      'text': record['message'],
    })
    on_message(message)

def collect_messages(directory, user, on_message, encoding):
  for filename in os.listdir(directory):
    if filename.endswith('.xml'):
      collect_messages_xml(os.path.join(directory, filename),  user, on_message, encoding)
    elif filename.endswith('.csv'):
      collect_messages_csv(os.path.join(directory, filename),  user, on_message, encoding)
    elif filename.endswith('.txt'):
      collect_messages_txt(os.path.join(directory, filename),  user, on_message, encoding)
    else:
      raise Exception(f"unknown file type: {filetype}")

def cb_on_message(message):
  print(json.dumps(message, ensure_ascii=False))

def main():
  parser = argparse.ArgumentParser(description='Import Skypelog jsonl exports')
  parser.add_argument('command', choices=['contacts', 'messages'])
  parser.add_argument('-d', '--directory', required=True, help='Directory containing files')
  parser.add_argument('-e', '--encoding', default='utf-8', help='File encoding (default: utf-8)')
  parser.add_argument('-u', '--user', help='Receiver user ID')

  args = parser.parse_args()

  if args.command == 'contacts':
    contacts = collect_contacts(args.directory, args.encoding)
    json.dump(contacts, sys.stdout, indent=2, ensure_ascii=False)
  elif args.command == 'messages':
    collect_messages(args.directory, args.user, cb_on_message, args.encoding)

if __name__ == "__main__":
    main()