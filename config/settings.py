"""
Application settings. Uses pydantic-settings for env and default values.
Paths are relative to the project root (where main.py lives).
"""
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

# Project root: directory containing main.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application configuration."""

    # Database
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'telemetry.db'}"

    # Data file paths (relative to project root or absolute)
    telemetry_logs_path: str = str(PROJECT_ROOT / "telemetry_logs.jsonl")
    employees_csv_path: str = str(PROJECT_ROOT / "employees.csv")

    # App
    debug: bool = False
    app_title: str = "Claude Code Telemetry Analytics"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
