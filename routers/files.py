from fastapi import APIRouter, UploadFile, File, HTTPException
from services.parser import parse_docx_file

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Поддерживается только формат .docx!")

    file_bytes = await file.read()

    result = parse_docx_file(file_bytes, file.filename)
    return result