
"""Optional AWS S3 storage for bicycle theft data."""

import hashlib
import os
import re
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


def upload_file_to_s3(
    local_path: str,
    bucket_name: str,
    s3_key: str,
    profile_name: str | None = None,
    region_name: str = "eu-north-1",
) -> None:
    """Upload a local file to a private S3 bucket."""

    path = Path(local_path)

    if not path.is_file():
        raise FileNotFoundError(f"Local file not found: {path}")

    session = boto3.Session(
        profile_name=profile_name,
        region_name=region_name,
    )

    s3 = session.client("s3")

    s3.upload_file(
        Filename=str(path),
        Bucket=bucket_name,
        Key=s3_key,
        ExtraArgs={
            "ServerSideEncryption": "AES256",
            "Metadata": {"sha256": file_sha256(path)},
        },
    )

    print(f"Uploaded {path} to s3://{bucket_name}/{s3_key}")


def file_sha256(path: Path) -> str:
    """Calculate SHA-256 checksum for a local file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            digest.update(chunk)

    return digest.hexdigest()


def sync_raw_to_s3(
    bucket_name: str,
    profile_name: str | None = None,
    region_name: str = "eu-north-1",
    dry_run: bool = True,
) -> None:
    """Synchronize local raw JSON files with S3."""

    session = boto3.Session(
        profile_name=profile_name,
        region_name=region_name,
    )

    s3 = session.client("s3")

    raw_dir = Path("data/raw")
    files = sorted(raw_dir.glob("*/*.json"))

    uploaded = 0
    skipped = 0
    pending = 0

    for path in files:
        key = f"raw/{path.relative_to(raw_dir).as_posix()}"
        checksum = file_sha256(path)

        try:
            response = s3.head_object(
                Bucket=bucket_name,
                Key=key,
            )

            remote_checksum = response.get(
                "Metadata", {}
            ).get("sha256")

            # Preferred comparison: SHA-256 metadata
            if remote_checksum == checksum:
                skipped += 1
                continue

            # Fallback for older single-part uploads
            if not remote_checksum:
                etag = response.get("ETag", "").strip('"')

                if re.fullmatch(r"[a-fA-F0-9]{32}", etag):
                    local_md5 = hashlib.md5(
                        path.read_bytes(),
                        usedforsecurity=False,
                    ).hexdigest()

                    if local_md5.lower() == etag.lower():
                        skipped += 1
                        continue

        except ClientError as error:
            error_code = error.response["Error"]["Code"]

            if error_code not in ("404", "NoSuchKey"):
                raise

        # Upload only new or changed files
        if dry_run:
            pending += 1
            print(f"[DRY RUN] Would upload: {key}")

        else:
            s3.upload_file(
                Filename=str(path),
                Bucket=bucket_name,
                Key=key,
                ExtraArgs={
                    "ServerSideEncryption": "AES256",
                    "Metadata": {"sha256": checksum},
                },
            )

            uploaded += 1
            print(f"Uploaded: {key}")

    print(
        f"Finished: {uploaded} uploaded, "
        f"{skipped} unchanged, "
        f"{pending} pending, "
        f"dry_run={dry_run}"
    )


if __name__ == "__main__":
    bucket = os.environ.get("BIKE_THEFT_S3_BUCKET")

    if not bucket:
        raise SystemExit(
            "Set BIKE_THEFT_S3_BUCKET before uploading."
        )

    upload_file_to_s3(
        local_path="data/raw/2026-09/london_centre.json",
        bucket_name=bucket,
        s3_key="raw/2026-09/london_centre.json",
        profile_name=os.environ.get("AWS_PROFILE"),
    )
