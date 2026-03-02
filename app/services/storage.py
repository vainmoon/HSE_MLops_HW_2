import os
import boto3
from botocore.client import Config

MINIO_ENDPOINT = os.environ["MINIO_ENDPOINT"]
MINIO_PUBLIC_URL = os.environ["MINIO_PUBLIC_URL"]
MINIO_ACCESS_KEY = os.environ["MINIO_ACCESS_KEY"]
MINIO_SECRET_KEY = os.environ["MINIO_SECRET_KEY"]
BUCKET = os.environ["MINIO_BUCKET"]

_cfg = dict(
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
)

_internal = boto3.client("s3", endpoint_url=f"http://{MINIO_ENDPOINT}", **_cfg)

_public = boto3.client("s3", endpoint_url=MINIO_PUBLIC_URL, **_cfg)

PRESIGN_TTL = 3600


def ensure_bucket() -> None:
    existing = [b["Name"] for b in _internal.list_buckets()["Buckets"]]
    if BUCKET not in existing:
        _internal.create_bucket(Bucket=BUCKET)


def object_key(model_id: int, version_id: int) -> str:
    return f"models/{model_id}/versions/{version_id}/artifact"


def presigned_upload_url(model_id: int, version_id: int) -> str:
    return _public.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET, "Key": object_key(model_id, version_id)},
        ExpiresIn=PRESIGN_TTL,
    )


def presigned_download_url(model_id: int, version_id: int) -> str:
    return _public.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET, "Key": object_key(model_id, version_id)},
        ExpiresIn=PRESIGN_TTL,
    )
