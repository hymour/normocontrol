import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import files
#uvicorn main:app --reload

app = FastAPI(title="test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(files.router)
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
@app.get("/")
def read_root():
    return FileResponse("frontend/page.html")