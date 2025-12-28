# A script to import jsonl telegram exports.
# The format for each record looks like:
# {
#   "out": false,
#   "service": false,
#   "event": "message",
#   "to": {
#     "id": "$0000001",
#     "flags": 32322,
#     "peer_type": "user",
#     "peer_id": 1343486,
#     "username": "alice",
#     "last_name": "Anderson",
#     "print_name": "Alice Anderson",
#     "when": "2017-02-01 09:23:03",
#     "first_name": "Alice",
#     "phone": "09090909022"
#   },
#   "id": "902384920384092384092384",
#   "flags": 2256,
#   "text": "Ok",
#   "unread": false,
#   "date": 145230849,
#   "from": {
#     "flags": 1,
#     "id": "$234234324320056092acf9a3ee3930",
#     "peer_type": "user",
#     "peer_id": 8492342394,
#     "username": "bob",
#     "last_name": "Benson",
#     "print_name": "Benson",
#     "first_name": "Bob"
#   }
# }
#
# The exports are multiple jsonl files in a single directory
# Usage:
# python3 import-telegram-jsonl.py contacts -d "telegram/" > contacts.json
# python3 import-telegram-jsonl.py messages -d "telegram/" > messages.jsonl

import os
import json
import argparse
import sys
from datetime import datetime, timezone
from collections import OrderedDict


def _safe_id(obj):
  if not obj:
    return None
  if isinstance(obj, dict):
    if obj.get('id'):
      return str(obj.get('id'))
    if obj.get('peer_id') is not None:
      return str(obj.get('peer_id'))
  return None


def _display_name(obj):
  if not obj:
    return ""
  for k in ('print_name', 'full_name', 'name'):
    v = obj.get(k)
    if v:
      return v
  fn = obj.get('first_name') or ''
  ln = obj.get('last_name') or ''
  if fn or ln:
    return (fn + ' ' + ln).strip()
  if obj.get('username'):
    return obj.get('username')
  if obj.get('phone'):
    return obj.get('phone')
  return obj.get('id')


def _parse_timestamp(record):
  # Try `date` numeric, then `when` strings in nested objects
  d = record.get('date')
  if isinstance(d, (int, float)):
    # heuristic: if milliseconds (>= 1e12) convert to seconds
    ts = int(d)
    if ts > 10 ** 12:
      ts = ts / 1000
    try:
      return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace('+00:00', 'Z')
    except Exception:
      pass

  # look for when fields in from/to
  for side in ('from', 'to'):
    s = record.get(side)
    if s and isinstance(s, dict):
      when = s.get('when')
      if when:
        # common format: 2017-02-01 09:23:03
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
          try:
            dt = datetime.strptime(when, fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z')
          except Exception:
            pass

  # fallback to current time
  return datetime.now(tz=timezone.utc).isoformat().replace('+00:00', 'Z')


def collect_contacts(directory, encoding='utf-8'):
  contacts = {}

  for root, _, files in os.walk(directory):
    for fname in files:
      if not (fname.endswith('.jsonl') or fname.endswith('.json')):
        continue
      path = os.path.join(root, fname)
      with open(path, 'r', encoding=encoding, errors='ignore') as fh:
        for line in fh:
          line = line.strip()
          if not line:
            continue
          rec = json.loads(line)
          for side in ('from', 'to'):
            obj = rec.get(side)
            uid = _safe_id(obj)
            if not uid:
              continue
            uname = _display_name(obj)
            if uid not in contacts:
              contacts[uid] = OrderedDict({
                'name': uname,
                'platforms': [{
                  'id': uid,
                  'platform': 'telegram',
                  'name': uname,
                  'avatar': '',
                  'meta': {}
                }]
              })

  return list(contacts.values())


def collect_messages(directory, on_message, encoding='utf-8'):
  for root, _, files in os.walk(directory):
    for fname in files:
      if not (fname.endswith('.jsonl') or fname.endswith('.json')):
        continue
      path = os.path.join(root, fname)
      try:
        with open(path, 'r', encoding=encoding, errors='ignore') as fh:
          for line in fh:
            line = line.strip()
            if not line:
              continue
            try:
              rec = json.loads(line)
            except Exception:
              continue

            # only handle message events
            if rec.get('event') and rec.get('event') != 'message':
              continue

            frm = rec.get('from') or {}
            to = rec.get('to') or {}

            from_id = _safe_id(frm) or ''
            to_id = _safe_id(to) or ''

            target_type = 'user'
            if isinstance(to, dict) and to.get('peer_type') and to.get('peer_type') != 'user':
              target_type = 'group'

            ts = _parse_timestamp(rec)

            text = rec.get('text')
            # some exports use 'message' key
            if text is None:
              text = rec.get('message')
            if text is None:
              # no textual payload, try to describe media
              if rec.get('media'):
                text = '[media]'
              else:
                text = ''

            if target_type == 'user':
              to = {
                'type': target_type,
                'user_id': str(to_id) if target_type == 'user' else None,
              }
            else:
              to = {
                'type': target_type,
                'group_id': str(to_id) if target_type == 'group' else None,
              }

            message = OrderedDict({
              'ts': ts,
              'platform': 'telegram',
              'from': str(from_id),
              'to': to,
              'text': text,
            })

            on_message(message)
      except FileNotFoundError:
        continue


def cb_on_message(message):
  print(json.dumps(message, ensure_ascii=False))


def main():
  parser = argparse.ArgumentParser(description='Import Telegram jsonl exports')
  parser.add_argument('command', choices=['contacts', 'messages'])
  parser.add_argument('-d', '--directory', required=True, help='Base directory containing JSONL exports')
  parser.add_argument('-e', '--encoding', default='utf-8', help='File encoding (default: utf-8)')

  args = parser.parse_args()

  if args.command == 'contacts':
    contacts = collect_contacts(args.directory, args.encoding)
    json.dump(contacts, sys.stdout, indent=2, ensure_ascii=False)
  elif args.command == 'messages':
    collect_messages(args.directory, cb_on_message, args.encoding)


if __name__ == '__main__':
  main()
