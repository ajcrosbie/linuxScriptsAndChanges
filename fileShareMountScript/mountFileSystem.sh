#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# fail if no env present
if [ ! -f "$SCRIPT_DIR/.env" ]; then
	echo "No env found please add one following the docs"
	exit 1
fi
source "$SCRIPT_DIR/.env"



# === Mount location ===
LOCAL_MOUNT=~/Documents/sharedFiles
mkdir -p "$LOCAL_MOUNT"

# === Mount the share ===
if sudo mount -t cifs "//$SMB_IP/$SMB_SHARE" "$LOCAL_MOUNT" -o username=$SMB_USER,password=$SMB_PASS,vers=3.0,uid=1000,gid=1000
then
	echo "Mounted //$SMB_IP/$SMB_SHARE at $LOCAL_MOUNT"
else 
	echo "mount failed"
fi