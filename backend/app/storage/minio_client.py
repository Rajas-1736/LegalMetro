import os
import io
import logging
from typing import Optional, Tuple
from minio import Minio
from minio.error import S3Error
from app.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.minio_client: Optional[Minio] = None
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.local_dir = settings.STORAGE_LOCAL_DIR
        os.makedirs(self.local_dir, exist_ok=True)
        
        import socket
        try:
            # Fast check: verify port is actually open before letting urllib3 hang on retries
            host, port = (settings.MINIO_ENDPOINT.split(":") + ["9000"])[:2]
            with socket.create_connection((host, int(port)), timeout=0.2):
                pass

            client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            # Test connection
            if not client.bucket_exists(self.bucket_name):
                client.make_bucket(self.bucket_name)
            self.minio_client = client
            logger.info(f"Connected to MinIO at {settings.MINIO_ENDPOINT}, bucket: {self.bucket_name}")
        except Exception as e:
            logger.info(f"MinIO not active at {settings.MINIO_ENDPOINT}. Using local storage at {self.local_dir}")
            self.minio_client = None

    def upload_file(self, file_data: bytes, filename: str, content_type: str = "image/jpeg") -> str:
        """Uploads file to MinIO or fallback local directory. Returns access URL or relative path."""
        safe_filename = os.path.basename(filename)
        
        if self.minio_client:
            try:
                data_stream = io.BytesIO(file_data)
                self.minio_client.put_object(
                    bucket_name=self.bucket_name,
                    object_name=safe_filename,
                    data=data_stream,
                    length=len(file_data),
                    content_type=content_type,
                )
                return f"/api/v1/storage/file/{safe_filename}"
            except Exception as e:
                logger.error(f"MinIO upload error: {e}. Falling back to local disk.")

        # Local disk fallback
        local_path = os.path.join(self.local_dir, safe_filename)
        with open(local_path, "wb") as f:
            f.write(file_data)
        return f"/api/v1/storage/file/{safe_filename}"

    def get_file(self, filename: str) -> Optional[Tuple[bytes, str]]:
        """Retrieves file bytes and content type."""
        safe_filename = os.path.basename(filename)
        if self.minio_client:
            try:
                response = self.minio_client.get_object(self.bucket_name, safe_filename)
                data = response.read()
                response.close()
                response.release_conn()
                return data, "application/octet-stream"
            except Exception as e:
                logger.warning(f"Failed to fetch {safe_filename} from MinIO: {e}")

        # Local fallback
        local_path = os.path.join(self.local_dir, safe_filename)
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                data = f.read()
            return data, "application/octet-stream"
        return None

storage_service = StorageService()
