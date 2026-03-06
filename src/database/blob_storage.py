"""
Azure Blob Storage Service
Handles file upload, download, and management in Azure Blob Storage.
"""

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import AzureError, ResourceNotFoundError
from datetime import datetime, timedelta
from typing import Optional, BinaryIO, Dict, Any
import uuid
import os
import logging
import mimetypes

from .config import get_db_settings

logger = logging.getLogger(__name__)
settings = get_db_settings()


class AzureBlobService:
    """
    Azure Blob Storage service for document storage.
    Handles upload, download, delete, and SAS URL generation.
    """

    def __init__(self):
        self._client: Optional[BlobServiceClient] = None
        self._container_name = settings.AZURE_STORAGE_CONTAINER

    @property
    def client(self) -> BlobServiceClient:
        """Lazy initialization of blob service client."""
        if self._client is None:
            if settings.AZURE_STORAGE_CONNECTION_STRING:
                self._client = BlobServiceClient.from_connection_string(
                    settings.AZURE_STORAGE_CONNECTION_STRING
                )
            elif settings.AZURE_STORAGE_ACCOUNT_NAME and settings.AZURE_STORAGE_ACCOUNT_KEY:
                account_url = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
                self._client = BlobServiceClient(
                    account_url=account_url,
                    credential=settings.AZURE_STORAGE_ACCOUNT_KEY
                )
            else:
                raise ValueError(
                    "Azure Storage credentials not configured. "
                    "Set AZURE_STORAGE_CONNECTION_STRING or "
                    "AZURE_STORAGE_ACCOUNT_NAME + AZURE_STORAGE_ACCOUNT_KEY"
                )
        return self._client

    @property
    def container(self) -> ContainerClient:
        """Get container client."""
        return self.client.get_container_client(self._container_name)

    async def ensure_container_exists(self) -> None:
        """Create container if it doesn't exist."""
        try:
            container = self.container
            if not container.exists():
                container.create_container()
                logger.info(f"Created container: {self._container_name}")
        except AzureError as e:
            logger.error(f"Failed to create container: {e}")
            raise

    def generate_blob_name(
        self,
        user_id: uuid.UUID,
        original_filename: str
    ) -> str:
        """
        Generate unique blob name with path structure.
        Format: users/{user_id}/documents/{uuid}_{original_filename}
        """
        file_id = uuid.uuid4()
        # Sanitize filename
        safe_filename = "".join(c for c in original_filename if c.isalnum() or c in "._-")
        return f"users/{user_id}/documents/{file_id}_{safe_filename}"

    async def upload_file(
        self,
        user_id: uuid.UUID,
        file_data: BinaryIO,
        original_filename: str,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Azure Blob Storage.

        Returns:
            dict with blob_name, blob_url, file_size
        """
        try:
            blob_name = self.generate_blob_name(user_id, original_filename)

            # Detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(original_filename)
                content_type = content_type or "application/octet-stream"

            # Get blob client
            blob_client = self.container.get_blob_client(blob_name)

            # Upload with metadata
            file_data.seek(0)
            content = file_data.read()
            file_size = len(content)

            blob_client.upload_blob(
                content,
                content_settings={
                    "content_type": content_type
                },
                metadata={
                    "user_id": str(user_id),
                    "original_filename": original_filename,
                    "uploaded_at": datetime.utcnow().isoformat()
                },
                overwrite=True
            )

            logger.info(f"Uploaded blob: {blob_name}, size: {file_size}")

            return {
                "blob_name": blob_name,
                "blob_url": blob_client.url,
                "file_size": file_size,
                "content_type": content_type
            }

        except AzureError as e:
            logger.error(f"Failed to upload blob: {e}")
            raise

    async def upload_bytes(
        self,
        user_id: uuid.UUID,
        data: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload bytes directly."""
        from io import BytesIO
        return await self.upload_file(
            user_id=user_id,
            file_data=BytesIO(data),
            original_filename=filename,
            content_type=content_type
        )

    async def download_file(self, blob_name: str) -> bytes:
        """Download a file from Azure Blob Storage."""
        try:
            blob_client = self.container.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            return download_stream.readall()
        except ResourceNotFoundError:
            logger.error(f"Blob not found: {blob_name}")
            raise FileNotFoundError(f"File not found: {blob_name}")
        except AzureError as e:
            logger.error(f"Failed to download blob: {e}")
            raise

    async def delete_file(self, blob_name: str) -> bool:
        """Delete a file from Azure Blob Storage."""
        try:
            blob_client = self.container.get_blob_client(blob_name)
            blob_client.delete_blob()
            logger.info(f"Deleted blob: {blob_name}")
            return True
        except ResourceNotFoundError:
            logger.warning(f"Blob not found for deletion: {blob_name}")
            return False
        except AzureError as e:
            logger.error(f"Failed to delete blob: {e}")
            raise

    def generate_sas_url(
        self,
        blob_name: str,
        expires_in_hours: int = 1,
        permission: str = "r"
    ) -> str:
        """
        Generate a SAS URL for temporary access to a blob.

        Args:
            blob_name: The blob path
            expires_in_hours: How long the URL should be valid
            permission: "r" for read, "w" for write, "d" for delete

        Returns:
            SAS URL string
        """
        permissions = BlobSasPermissions(
            read="r" in permission,
            write="w" in permission,
            delete="d" in permission
        )

        sas_token = generate_blob_sas(
            account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
            container_name=self._container_name,
            blob_name=blob_name,
            account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
            permission=permissions,
            expiry=datetime.utcnow() + timedelta(hours=expires_in_hours)
        )

        blob_url = (
            f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/"
            f"{self._container_name}/{blob_name}?{sas_token}"
        )

        return blob_url

    async def get_blob_properties(self, blob_name: str) -> Dict[str, Any]:
        """Get blob metadata and properties."""
        try:
            blob_client = self.container.get_blob_client(blob_name)
            props = blob_client.get_blob_properties()

            return {
                "name": blob_name,
                "size": props.size,
                "content_type": props.content_settings.content_type,
                "created_at": props.creation_time,
                "last_modified": props.last_modified,
                "metadata": props.metadata
            }
        except ResourceNotFoundError:
            raise FileNotFoundError(f"File not found: {blob_name}")

    async def list_user_files(
        self,
        user_id: uuid.UUID,
        prefix: Optional[str] = None
    ) -> list:
        """List all files for a user."""
        user_prefix = f"users/{user_id}/documents/"
        if prefix:
            user_prefix = f"{user_prefix}{prefix}"

        blobs = []
        for blob in self.container.list_blobs(name_starts_with=user_prefix):
            blobs.append({
                "name": blob.name,
                "size": blob.size,
                "last_modified": blob.last_modified
            })

        return blobs

    async def copy_file(
        self,
        source_blob_name: str,
        dest_user_id: uuid.UUID,
        dest_filename: str
    ) -> Dict[str, Any]:
        """Copy a file to a new location."""
        dest_blob_name = self.generate_blob_name(dest_user_id, dest_filename)

        source_blob = self.container.get_blob_client(source_blob_name)
        dest_blob = self.container.get_blob_client(dest_blob_name)

        # Start copy
        dest_blob.start_copy_from_url(source_blob.url)

        return {
            "blob_name": dest_blob_name,
            "blob_url": dest_blob.url
        }


# Singleton instance
_blob_service: Optional[AzureBlobService] = None


def get_blob_service() -> AzureBlobService:
    """Get blob service singleton."""
    global _blob_service
    if _blob_service is None:
        _blob_service = AzureBlobService()
    return _blob_service

