from __future__ import annotations

import io
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import uuid4

import boto3


class BaseStorageProvider(ABC):
    @abstractmethod
    async def save_file(self, file_name: str, content: bytes, content_type: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def read_file(self, storage_key: str) -> bytes:
        raise NotImplementedError


class LocalStorageProvider(BaseStorageProvider):
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path
        self.root_path.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file_name: str, content: bytes, content_type: str) -> dict:
        storage_key = f"{uuid4().hex}_{file_name}"
        path = self.root_path / storage_key
        path.write_bytes(content)
        return {"storage_key": storage_key, "url": str(path), "content_type": content_type}

    async def read_file(self, storage_key: str) -> bytes:
        return (self.root_path / storage_key).read_bytes()


class MinIOStorageProvider(BaseStorageProvider):
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False) -> None:
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=f"http{'s' if secure else ''}://{endpoint}",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        try:
            self.client.head_bucket(Bucket=bucket)
        except Exception:
            self.client.create_bucket(Bucket=bucket)

    async def save_file(self, file_name: str, content: bytes, content_type: str) -> dict:
        storage_key = f"{uuid4().hex}_{file_name}"
        self.client.upload_fileobj(io.BytesIO(content), self.bucket, storage_key, ExtraArgs={"ContentType": content_type})
        return {"storage_key": storage_key, "url": f"s3://{self.bucket}/{storage_key}", "content_type": content_type}

    async def read_file(self, storage_key: str) -> bytes:
        buffer = io.BytesIO()
        self.client.download_fileobj(self.bucket, storage_key, buffer)
        return buffer.getvalue()

