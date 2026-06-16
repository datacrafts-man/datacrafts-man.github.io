"""Shared constants for blog automation scripts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
DRAFTS_DIR = CONTENT_DIR / "drafts"
PROMPTS_DIR = ROOT / "prompts"

CATEGORIES = [
    "python",
    "automation",
    "ai",
    "data-analysis",
    "quant",
    "projects",
    "career",
]

CATEGORY_LABELS = {
    "python": "Python",
    "automation": "Automation",
    "ai": "AI",
    "data-analysis": "Data Analysis",
    "quant": "Quant",
    "projects": "Projects",
    "career": "Career",
}
