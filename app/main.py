from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api import auth, report
from app.core.config import settings


app = FastAPI(
    title="Psychometric Report Generator API",
    description="A production-ready API for generating PDF psychometric reports with AI analysis.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[''],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


REPORTS_DIR = "media/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(report.router, prefix="/report", tags=["Report Generation"])


@app.get("/", tags=["Health"])
async def root():
    """
    Simple health check to verify the API is running.
    """
    return {
        "status": "active", 
        "version": "2.0.0",
        "message": "Welcome to the Psychometric Report Generator API"
    }