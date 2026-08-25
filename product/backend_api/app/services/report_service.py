import os
from pathlib import Path

# Paths are returned project-relative and resolved against this root so the
# API works regardless of the server's current working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[4]

def get_reports():
    reports = []
    # We'll look in the reports directory
    reports_dir = PROJECT_ROOT / "reports"
    if reports_dir.exists():
        for file in reports_dir.iterdir():
            if file.is_file() and file.suffix == ".md":
                reports.append({
                    "type": "phase_report",
                    "name": file.stem,
                    "path": file.relative_to(PROJECT_ROOT).as_posix()
                })
    # We'll also look in the artifacts/final_evaluation and artifacts/research_tables for final evaluation reports
    final_eval_dir = PROJECT_ROOT / "artifacts" / "final_evaluation"
    if final_eval_dir.exists():
        for file in final_eval_dir.iterdir():
            if file.is_file():
                reports.append({
                    "type": "final_evaluation",
                    "name": file.stem,
                    "path": file.relative_to(PROJECT_ROOT).as_posix()
                })
    research_tables_dir = PROJECT_ROOT / "artifacts" / "research_tables"
    if research_tables_dir.exists():
        for file in research_tables_dir.iterdir():
            if file.is_file():
                reports.append({
                    "type": "research_table",
                    "name": file.stem,
                    "path": file.relative_to(PROJECT_ROOT).as_posix()
                })
    # We'll also look in the docs/paper for the research paper
    paper_dir = PROJECT_ROOT / "docs" / "paper"
    if paper_dir.exists():
        for file in paper_dir.iterdir():
            if file.is_file():
                reports.append({
                    "type": "research_paper",
                    "name": file.stem,
                    "path": file.relative_to(PROJECT_ROOT).as_posix()
                })
    return reports