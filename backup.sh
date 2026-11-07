#!/bin/sh
set -e
DATE=$(date +%Y-%m-%d_%H%M%S)
DEST="/backups"
KEEP=30

sqlite3 /data/conso.db ".backup '$DEST/conso-$DATE.db'"
gzip "$DEST/conso-$DATE.db"

ls -1t "$DEST"/conso-*.db.gz 2>/dev/null | tail -n +$((KEEP+1)) | xargs -r rm -f

echo "[$(date)] backup OK -> conso-$DATE.db.gz" >> "$DEST/backup.log"
