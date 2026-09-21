import mimetypes
from fastapi import APIRouter, HTTPException, Response
from app.storage.minio_client import storage_service

router = APIRouter(prefix="/storage", tags=["Storage"])

@router.get("/file/{filename}")
def serve_storage_file(filename: str):
    res = storage_service.get_file(filename)
    if not res:
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    
    file_bytes, _ = res
    content_type, _ = mimetypes.guess_type(filename)
    if not content_type:
        content_type = "application/octet-stream"

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"}
    )
