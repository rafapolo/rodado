#!/bin/bash
# Idempotently (re)mounts beelink's SMB share at ~/mnt/homelab.
# Called at login by ~/Library/LaunchAgents/com.rodado.mount-homelab.plist
# so scripts/sync/prepara_db_beelink.py's BEELINK_MOUNT path (and the ask
# TUI's local data/basedosdados.duckdb) keep working after reboots/sleep
# without a manual remount. Deliberately mounts under $HOME, not /Volumes:
# diskutil/automount removes /Volumes/* mountpoint dirs on unmount, which
# would require re-running `sudo mkdir` every time — a plain user-owned
# directory persists across mount cycles with no sudo needed.
MOUNT_POINT="$HOME/mnt/homelab"
mkdir -p "$MOUNT_POINT"
if [ ! -d "$MOUNT_POINT/rodado" ]; then
  PW=$(security find-internet-password -a polo -s 192.168.100.2 -w)
  mount_smbfs "//polo:${PW}@192.168.100.2/homelab" "$MOUNT_POINT"
  unset PW
fi
