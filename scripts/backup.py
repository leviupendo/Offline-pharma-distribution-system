import base64
import hashlib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

PLACEHOLDER_KEY = "change-me"

source = Path(os.getenv("DATABASE_FILE", "pharma.db"))
destination = Path(os.getenv("BACKUP_DIR", "backups"))
destination.mkdir(parents=True, exist_ok=True)

if not source.exists():
    raise SystemExit(f"Database file not found: {source}")

backup_key = os.getenv("BACKUP_KEY", PLACEHOLDER_KEY)
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
raw_bytes = source.read_bytes()

if backup_key == PLACEHOLDER_KEY:
    print(
        "WARNING: BACKUP_KEY is not set (or is still the placeholder value). "
        "Writing an UNENCRYPTED backup. Set BACKUP_KEY in your environment "
        "before treating backups as suitable for offline storage."
    )
    target = destination / f"pharma-{stamp}.db"
    shutil.copy2(source, target)
    payload = target.read_bytes()
else:
    # Derive a Fernet key from the configured passphrase using a
    # per-install salt so the same BACKUP_KEY can restore any backup
    # made on this install. The salt is not a secret; it just needs
    # to stay paired with its backups.
    salt_path = destination / ".salt"
    if salt_path.exists():
        salt = salt_path.read_bytes()
    else:
        salt = os.urandom(16)
        salt_path.write_bytes(salt)

    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390_000)
    fernet_key = base64.urlsafe_b64encode(kdf.derive(backup_key.encode("utf-8")))
    token = Fernet(fernet_key).encrypt(raw_bytes)

    target = destination / f"pharma-{stamp}.db.enc"
    target.write_bytes(token)
    payload = token
    print(f"Backup encrypted with key derived from BACKUP_KEY (salt: {salt_path}).")

digest = hashlib.sha256(payload).hexdigest()
target.with_suffix(target.suffix + ".sha256").write_text(digest + "\n", encoding="utf-8")
print(f"Backup: {target}")
print(f"SHA-256: {digest}")
