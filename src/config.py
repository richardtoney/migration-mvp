"""
Configuration and constants for the migration tool.
Loads from .env file and provides typed access to settings.
"""

from pathlib import Path
import os
import logging

from dotenv import load_dotenv

# Load .env from project root (two levels up from this file, or cwd)
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

# API Configuration
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

# Project paths
TEST_PROJECT_PATH: Path = Path(
    os.getenv("TEST_PROJECT_PATH", "./test-projects/spring-petclinic")
)
if not TEST_PROJECT_PATH.is_absolute():
    TEST_PROJECT_PATH = (_project_root / TEST_PROJECT_PATH).resolve()

# OpenRewrite configuration
OPENREWRITE_VERSION: str = os.getenv("OPENREWRITE_VERSION", "6.28.0")
SPRING_BOOT_3_RECIPE: str = (
    "org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_0"
)
REWRITE_RECIPE_COORDINATES: str = (
    "org.openrewrite.recipe:rewrite-spring:RELEASE"
)

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Validation
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment")
