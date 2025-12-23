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
