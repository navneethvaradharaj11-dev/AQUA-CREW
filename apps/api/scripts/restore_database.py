"""
AQUA CREW — Database Restore and Verification Script (Task 17)
Restores database from backup after verifying SHA-256 cryptographic checksum.
"""
import os
import sys
import shutil
import hashlib
import json
import time
from datetime import datetime, timezone

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.database.session import SessionLocal, init_db
from app.repositories.rover_repository import RoverRepository
from app.repositories.pipeline_repository import PipelineRepository


def calculate_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def restore_backup(metadata_path: str, target_db_path: str = None) -> dict:
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    backup_path = meta.get("backup_path")
    expected_sha256 = meta.get("sha256_checksum")

    if not os.path.exists(backup_path):
        # Look in same directory as metadata
        dirname = os.path.dirname(metadata_path)
        backup_path = os.path.join(dirname, meta.get("backup_filename"))

    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    t0 = time.perf_counter()

    # Step 1: Verify cryptographic checksum
    actual_sha256 = calculate_sha256(backup_path)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"Integrity check failed! Expected SHA-256: {expected_sha256}, actual: {actual_sha256}"
        )
    print("SHA-256 integrity verified successfully.")

    # Step 2: Restore
    if meta.get("engine_type") == "sqlite":
        if not target_db_path:
            db_url = settings.DATABASE_URL
            target_db_path = db_url.replace("sqlite:///", "")
            if target_db_path.startswith("./"):
                target_db_path = target_db_path[2:]

        shutil.copy2(backup_path, target_db_path)
        print(f"Database restored to: {target_db_path}")

    duration_sec = round(time.perf_counter() - t0, 4)

    # Step 3: Verification query
    db = SessionLocal()
    try:
        rover_count = len(RoverRepository.get_all(db))
        pipe_count = len(PipelineRepository.get_all(db))
    finally:
        db.close()

    result = {
        "status": "RESTORE_SUCCESSFUL",
        "backup_id": meta.get("backup_id"),
        "duration_sec": duration_sec,
        "restored_to": target_db_path,
        "verified_sha256": actual_sha256,
        "verified_records": {
            "rovers": rover_count,
            "pipelines": pipe_count,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    print(f"Restore completed in {duration_sec}s. Verified {rover_count} rovers, {pipe_count} pipelines.")
    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        meta_file = sys.argv[1]
    else:
        # Find latest metadata file
        backup_dir = "backups"
        meta_files = [f for f in os.listdir(backup_dir) if f.endswith("_metadata.json")]
        if not meta_files:
            print("No backup metadata found in backups/")
            sys.exit(1)
        meta_files.sort(reverse=True)
        meta_file = os.path.join(backup_dir, meta_files[0])

    restore_backup(meta_file)

