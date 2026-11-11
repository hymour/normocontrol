from fastapi import APIRouter, UploadFile, File, HTTPException
from services.parser import parse_docx_file
from pathlib import Path

MAX_SIZE = 20*1024*1024
BASE_DIR = Path("storage/documents").resolve()
router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".docx") or not file.filename:
        raise HTTPException(400, "Поддерживается только формат .docx!")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(413, "Файл слишком большой");

    try:
        return await run_in_threadpool(parse_docx_file, file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(422, "Не удалось разобрать файл")
