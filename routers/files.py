import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.concurrency import run_in_threadpool

from services.checker import check_document
from services.store import Session, save
from services.parser import parse_docx_file
from services.comment import add_comments

MAX_SIZE = 20*1024*1024
router = APIRouter()

@router.post("/api/upload")
async def upload(
    file: UploadFile = File(...), 
    standard: str = Form("GOST_732")
    ):
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Поддерживается только формат .docx!")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(413, "Файл слишком большой");

    try:
        parsed_data = await run_in_threadpool(parse_docx_file, file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    errors = await run_in_threadpool(check_document, parsed_data, standard)

    result_bytes = None
    if errors:
        result_bytes = await run_in_threadpool(add_comments, file_bytes, errors)

    session_id = uuid.uuid4().hex
    save(session_id, Session(
        o_filename=file.filename,
        result_bytes=result_bytes,
        has_errors=bool(errors),
    ))

    return {
        "session_id": session_id,
        "has_errors": bool(errors),
        "errors": errors if errors else [],
    }
