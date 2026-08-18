import argparse
import base64
import hashlib
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

parser = argparse.ArgumentParser(description="Restore a backup produced by scripts/backup.py")
parser.add_argument("backup_file", help="Path to the .db or .db.enc backup file")
parser.add_argument("-o", "--output", default="restored.db", help="Output path for the restored database file")
args = parser.parse_args()

backup_path = Path(args.backup_file)
if not backup_path.exists():
    raise SystemExit(f"Backup file not found: {backup_path}")

checksum_path = backup_path.with_suffix(backup_path.suffix + ".sha256")
if checksum_path.exists():
    expected = checksum_path.read_text(encoding="utf-8").strip()
    actual = hashlib.sha256(backup_path.read_bytes()).hexdigest()
    if expected != actual:
        raise SystemExit(
            f"CHECKSUM MISMATCH: {backup_path} does not match {checksum_path}. "
            f"Do not restore from this file."
        )
    print("Checksum verified.")
else:
    print(f"WARNING: no checksum file found at {checksum_path}; skipping verification.")

output_path = Path(args.output)

if backup_path.suffix == ".enc":
    backup_key = os.getenv("BACKUP_KEY")
    if not backup_key:
        raise SystemExit("BACKUP_KEY environment variable must be set to decrypt this backup.")

    salt_path = backup_path.parent / ".salt"
    if not salt_path.exists():
        raise SystemExit(f"Salt file not found: {salt_path}. Cannot derive the decryption key.")
    salt = salt_path.read_bytes()

    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390_000)
    fernet_key = base64.urlsafe_b64encode(kdf.derive(backup_key.encode("utf-8")))

    try:
        plaintext = Fernet(fernet_key).decrypt(backup_path.read_bytes())
    except InvalidToken:
        raise SystemExit("Decryption failed: BACKUP_KEY is incorrect or the backup is corrupted.")

    output_path.write_bytes(plaintext)
    print(f"Decrypted and restored to: {output_path}")
else:
    output_path.write_bytes(backup_path.read_bytes())
    print(f"Restored to: {output_path}")

print("Next: point DATABASE_URL at the restored file, run schema/startup checks, "
      "then run scripts/verify_audit.py before trusting this data.")
