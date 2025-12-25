# A script to import skype messages export from messages.json export file
# matching users against to contacts.json exported from import-contacts.py
#
# The format of the exported messages.json is as follows:
# {
#   "userId": "user-id",
#   "exportDate": "2023-12-21T06:51",
#   "conversations": [
#     {
#       "id": "other-user-id",
#       "displayName": "name of null",
#       "version": 166681267820,
#       "properties": {
#         "conversationblocked": false,
#         "lastimreceivedtime": "2022-10-16T19:30:27.53Z",
#         "consumptionhorizon": null,
#         "conversationstatus": null
#       },
#       "threadProperties": null,
#       "MessageList": [
#         {
#           "id": "166681262750",
#           "displayName": null,
#           "originalarrivaltime": "2022-10-28T19:30:27.53Z",
#           "messagetype": "Notice",
#           "version": 166681267820,
#           "content": "test content",
#           "conversationid": "other-user-id",
#           "from": "other-user-id",
#           "properties": null,
#           "amsreferences": null
#         }
#       ]
#     }
#   ]
# }
#
# Output must match the ty.Message struct
#
# Usage: python3 scripts/skype/import-messages.py messages.json > skype-messages.json

import argparse
import json
from datetime import timezone, datetime
import re
from collections import OrderedDict


def format_utc_seconds(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

def strip_html(text):
    # Simple HTML tag remover
    return re.sub(r'<[^>]+>', '', text)

def get_user_id(s: str) -> str:
    _before, sep, after = s.partition(":")
    return after if sep else s

def main():
    parser = argparse.ArgumentParser(description="Import messages from skype export")
    parser.add_argument("-f", "--file", required=True, help="messages.json file")
    parser.add_argument("-u", "--user", required=True, help="UserID of the owner")

    args = parser.parse_args()

    messages_file = args.file
    owner_id = args.user

    with open(messages_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for conv in data['conversations']:
        conv_id = str(get_user_id(conv['id']))
        for msg in conv['MessageList']:
            ts_str = msg['originalarrivaltime']
            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            from_id = str(get_user_id(msg['from']))

            # Assume user conversation for now
            if from_id == conv_id:
                to_user_id = owner_id
            else:
                to_user_id = conv_id

            to = {"type": "user", "user_id": str(to_user_id)}
            content = msg.get('content', '')
            raw = content
            text = strip_html(content)
            meta = {}
            if msg.get('properties'):
                for k, v in msg['properties'].items():
                    if v is not None:
                        meta[str(k)] = str(v)

            # Extract additional data
            links = re.findall(r'https?://[^\s]+', content)
            mentions = re.findall(r'@(\w+)', content)
            if links:
                meta['links'] = links
            if mentions:
                meta['mentions'] = mentions

            message = OrderedDict({
                "ts": format_utc_seconds(ts),
                "platform": "skype",
                "from": from_id,
                "to": to,
                "text": text,
                "raw": raw,
                "meta": meta
            })
            print(json.dumps(message, ensure_ascii=False))

if __name__ == "__main__":
    main()
