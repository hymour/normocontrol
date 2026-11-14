from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import files

app = FastAPI(title="test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(files.router)