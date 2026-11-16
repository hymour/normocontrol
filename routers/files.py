import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Response
from fastapi.concurrency import run_in_threadpool

from services.checker import check_document
from services.comment import add_comments
from services.parser import parse_docx_file
from services.rules import Standard
from services.store import Session, save, pop

from urllib.parse import quote

MAX_SIZE = 20*1024*1024
router = APIRouter()


@router.post("/api/upload")
async def upload(
    file: UploadFile = File(...), 
    standard: str = Form("GOST_7_32"),
):
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Поддерживается только формат .docx!")

    try:
        standard = Standard(standard.lower())
    except ValueError:
        raise HTTPException(400, "Указан неизвестный стандарт")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(413, "Файл слишком большой")

    try:
        parsed_data = await run_in_threadpool(
            parse_docx_file,
            file_bytes,
            file.filename,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    issues = await run_in_threadpool(check_document, parsed_data, standard)

    result_bytes = None
    if issues:
        result_bytes = await run_in_threadpool(
            add_comments,
            file_bytes,
            issues,
        )

    session_id = uuid.uuid4().hex
    save(session_id, Session(
        o_filename=file.filename,
        result_bytes=result_bytes,
        has_issues=bool(issues),
    ))

    return {
        "session_id": session_id,
        "has_issues": bool(issues),
        "issues": issues,
    }

@router.get("/api/download/{session_id}")
async def download(session_id: str):
    session = pop(session_id) 
    
    if not session:
        raise HTTPException(404, "Сессия не найдена или истекла")
        
    if not session.result_bytes:
        raise HTTPException(404, "Ошибок не обнаружено")

    original_name = session.o_filename.rsplit('.', 1)[0]
    download_name = f"{original_name}_checked.docx"
    
    encoded_filename = quote(download_name)

    return Response(
        content=session.result_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )