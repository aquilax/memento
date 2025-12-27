import json
import argparse
import sys
from datetime import datetime, timezone
from collections import OrderedDict

def format_utc_seconds(dt):
  return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

def collect_contacts(file, encoding='utf-8'):
  contacts = {}
  with open(file, 'r', encoding=encoding, errors='ignore') as fh:
    for line in fh:
      line = line.strip().rstrip(',')
      if not line:
        continue
      rec = json.loads(line)

      name = rec.get('from_dispname')
      uid = rec.get('author')
      if uid not in contacts:
        contacts[uid] = OrderedDict({
          'name': name,
          'platform_ids': [{
            'id': uid,
            'platform': 'skype',
            'avatar': '',
            'meta': {}
          }]
        })
  return list(contacts.values())

def collect_messages(file, on_message, encoding='utf-8'):
  with open(file, 'r', encoding=encoding, errors='ignore') as fh:
    for line in fh:
      line = line.strip().rstrip(',')
      if not line:
        continue
      rec = json.loads(line)

      from_uid = rec.get('author')
      to_uid = rec.get('dialog_partner')
      text = rec.get('body_xml')

      ts = datetime.fromtimestamp(rec.get('timestamp'), timezone.utc)

      message = OrderedDict({
        'ts': format_utc_seconds(ts),
        'platform': 'skype',
        'from': str(from_uid),
        'to': {
          'type': 'user',
          'user_id': str(to_uid)
        },
        'text': text,
      })
      on_message(message)

def cb_on_message(message):
  print(json.dumps(message, ensure_ascii=False))

def main():
  parser = argparse.ArgumentParser(description='Import Skypelog jsonl exports')
  parser.add_argument('command', choices=['contacts', 'messages'])
  parser.add_argument('-f', '--file', required=True, help='JSONL export file')
  parser.add_argument('-e', '--encoding', default='utf-8', help='File encoding (default: utf-8)')

  args = parser.parse_args()

  if args.command == 'contacts':
    contacts = collect_contacts(args.file, args.encoding)
    json.dump(contacts, sys.stdout, indent=2, ensure_ascii=False)
  elif args.command == 'messages':
    collect_messages(args.file, cb_on_message, args.encoding)


if __name__ == '__main__':
  main()
