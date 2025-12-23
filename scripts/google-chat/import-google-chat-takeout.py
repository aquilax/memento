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
