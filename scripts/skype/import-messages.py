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
# Usage:
# python3 scripts/skype/import-messages.py data/import/skype/contacts/messages.json messages.json > data/import/skype/messages.json

