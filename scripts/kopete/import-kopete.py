import os
import argparse
import json
import sys
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from datetime import datetime
from pathlib import Path

def format_utc_seconds(dt):
  return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

def get_platform(plugin_id):
    if plugin_id == 'ICQProtocol':
        return 'icq'
    if plugin_id == 'MSNProtocol':
        return 'msn'
    if plugin_id == 'JabberProtocol':
        return 'jabbber'
    else:
        raise Exception(f"Unknown protocol {plugin_id}")

def collect_contacts(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    contacts = []
    contact_elements = root.findall("meta-contact")
    for contact_element in contact_elements:
      plugin_data = contact_element.find("plugin-data")
      if plugin_data is None:
        continue
      plugin_id = plugin_data.attrib["plugin-id"]
      platform = get_platform(plugin_id)
      plugin_data = plugin_data.findall("plugin-data-field")
      data = {}
      for row in plugin_data:
        data[row.attrib['key']] = row.text
      id = data["accountId"]
      name = data["displayName"]
      name = id if name == None else name
      contact = {
        "name": str(name),
        "platforms": [{
          "id": str(id),
          "platform": platform,
          "name": str(name),
          "avatar": "",
          "meta": {}
        }]
      }
      contacts.append(contact)

    return contacts


def parse_kopete_history(file_path, platform, on_message):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Read header info
    head = root.find("head")
    date_node = head.find("date")

    year = int(date_node.get("year"))
    month = int(date_node.get("month"))

    contacts = [c.get("contactId") for c in head.findall("contact")]
    myself = next(c.get("contactId") for c in head.findall("contact")
                  if c.get("type") == "myself")
    other = next(c for c in contacts if c != myself)

    messages = []

    for msg in root.findall("msg"):
        time_raw = msg.get("time")          # "20 20:9:48"
        day_str, time_str = time_raw.split()

        timestamp = datetime.strptime(
            f"{year}-{month}-{day_str} {time_str}",
            "%Y-%m-%d %H:%M:%S"
        )

        incoming = msg.get("in") == "1"

        sender = msg.get("from") if incoming else myself
        recipient = myself if incoming else other

        message = {
            "ts": format_utc_seconds(timestamp),
            "platform": platform,
            "from": sender,
            "to": {"type": "user", "user_id": recipient },
            "message": (msg.text or "").strip(),
        }
        on_message(message)


def collect_messages(directory, on_message):
  dmap = {
    "ICQProtocol": "icq",
    "JabberProtocol": "jabber",
    "MSNProtocol": "msn",
  }
  for subdir, platform in dmap.items():
    path = os.path.join(directory, subdir)
    if os.path.isdir(path):
      files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if os.path.splitext(f)[1] == '.xml']
      for file in files:
        parse_kopete_history(file, platform, on_message)

def cb_on_message(message):
  print(json.dumps(message, ensure_ascii=False))

def main():
  parser = argparse.ArgumentParser(description='Import Kopete logs')
  parser.add_argument('command', choices=['contacts', 'messages'])
  parser.add_argument('-d', '--directory', help='Logs root')
  parser.add_argument('-f', '--file', help='Kopete contacts file')

  args = parser.parse_args()

  if args.command == 'contacts':
    contacts = collect_contacts(args.file)
    json.dump(contacts, sys.stdout, indent=2, ensure_ascii=False)
  elif args.command == 'messages':
    collect_messages(args.directory, cb_on_message)

if __name__ == "__main__":
    main()