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
