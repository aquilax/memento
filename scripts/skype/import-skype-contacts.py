# A script to import skype contacts export as memento users for the skype platform,
# all additional fields to be put as meta data and avatars to be downloaded in ./data/skype/avatar
# with filename same as the user id

# Skype contacts export is a CSV file with the following headers:
# type	id	display_name	blocked	favorite	profile.avatar_url	profile.gender	profile.locations[0].type	profile.locations[0].country	profile.locations[0].city	profile.locations[0].state	profile.mood	profile.name.first	profile.name.surname	profile.phones[0].number	profile.phones[0].type	profile.about	profile.phones[1].number	profile.phones[1].type	profile.website	profile.skype_handle	sources	creation_time

# Usage: import-contacts.py contacts.csv > skype-contacts.json

import argparse
import csv
import json
import os
import re
import sys
import requests

def download_avatar(avatar_url, user_id, avatar_dir):
    if not avatar_url:
        return None

    # Sanitize filename: replace invalid characters with underscores
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', user_id) + '.jpg'
    file_path = os.path.join(avatar_dir, safe_filename)

    if os.path.exists(file_path):
        return safe_filename

    try:
        response = requests.get(avatar_url)
        response.raise_for_status()

        # Get file extension from MIME type
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return safe_filename
    except Exception as e:
        print(f"Failed to download avatar for {user_id}: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Import contacts from skype export")
    parser.add_argument("-f", "--file", required=True, help="conacts.csv file")

    args = parser.parse_args()

    csv_file = args.file
    avatar_dir = os.path.join(os.getcwd(), 'data', 'skype', 'avatar')
    os.makedirs(avatar_dir, exist_ok=True)

    users = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            user_id = row.get('id', '').strip()
            skype_handle = row.get('profile.skype_handle', '').strip()
            display_name = row.get('display_name', '').strip()
            avatar_url = row.get('profile.avatar_url', '').strip()

            if not skype_handle:
                continue  # Skip if no skype handle

            # Download avatar
            avatar_filename = download_avatar(avatar_url, user_id, avatar_dir) if avatar_url else None

            # Meta data: all fields except the ones used for main structure
            meta = {}
            exclude_fields = {'id', 'profile.skype_handle', 'display_name', 'profile.avatar_url'}
            for key, value in row.items():
                if key not in exclude_fields and value.strip():
                    meta[key] = value.strip()

            platform = {
                "id": str(skype_handle),
                "platform": "skype",
                "name": display_name,
                "avatar": avatar_filename,
                "meta": meta
            }

            user = {
                "name": display_name,
                "platforms": [platform]
            }

            users.append(user)

    print(json.dumps(users, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()