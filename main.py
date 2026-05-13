import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from app.services.salary_predictor import predict_salary_jod
from fastapi.staticfiles import StaticFiles # تأكد من وجود هذا السطر
import os

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.database import SessionLocal, SeenJob, User, init_db
from app.services.background import schedule_user_job, register_all_user_jobs, check_user_trigger
from app.services.cv_parser import get_structured_cv
from app.services.extractor import extract_cv_data
from app.services.job_search import fetch_jobs
from app.services.scorer import calculate_score
from app.services.roadmap import get_roadmap
from app.services.pdf_generator import generate_pdf
from app.services.docx_generator import generate_docx

BASE_DIR = Path(__file__).resolve().parent.parent
PREFERENCES_PATH = BASE_DIR / "user_preferences.json"

app = FastAPI(title="CV Matcher API")
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class PreferencesBody(BaseModel):
    email: str = ""
    interval_hours: int = 3
    threshold: int = 80
    alerts_enabled: bool = True
    attach_pdf: bool = True
    alert_no_match: bool = False
    job_query: str = "AI Engineer"


class SaveUserBody(BaseModel):
    email: str
    job_query: str = "AI Engineer"
    alert_interval_hours: int = 6
    candidate_summary: dict[str, Any]
    best_score: int = 0
    job_links: list[str] = Field(default_factory=list)


@app.on_event("startup")
async def startup_event():
    init_db()
    register_all_user_jobs()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return RedirectResponse(url="/careerlens.html", status_code=302)


@app.get("/careerlens.html")
async def serve_careerlens():
    path = BASE_DIR / "careerlens.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="careerlens.html not found")
    return FileResponse(path)


@app.get("/settings.html")
async def serve_settings_html():
    path = BASE_DIR / "settings.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="settings.html not found")
    return FileResponse(path)


# Legacy preference storage and trigger stub; replaced by database-backed state.
# @app.post("/save-preferences")
# async def save_preferences(body: PreferencesBody):
#     PREFERENCES_PATH.write_text(
#         json.dumps(body.model_dump(), indent=2),
#         encoding="utf-8",
#     )
#     return {"ok": True}


# @app.post("/run-trigger")
# async def run_trigger():
#     email = ""
#     if PREFERENCES_PATH.exists():
#         try:
#             data = json.loads(PREFERENCES_PATH.read_text(encoding="utf-8"))
#             email = (data.get("email") or "").strip()
#         except (json.JSONDecodeError, OSError):
#             pass
#     # Stub: background job monitoring is not wired; UI expects this shape.
#     return {"matches_found": 0, "email": email or "—"}


@app.post("/save-user")
async def save_user(body: SaveUserBody):
    with SessionLocal() as session:
        existing_user = session.scalar(select(User).where(User.email == body.email))
        if existing_user:
            existing_user.job_query = body.job_query
            existing_user.alert_interval_hours = max(1, body.alert_interval_hours)
            existing_user.candidate_summary = body.candidate_summary
            existing_user.best_score = max(existing_user.best_score or 0, body.best_score or 0)
            user = existing_user
        else:
            user = User(
                email=body.email,
                job_query=body.job_query,
                alert_interval_hours=max(1, body.alert_interval_hours),
                candidate_summary=body.candidate_summary,
                best_score=body.best_score,
                created_at=datetime.utcnow(),
            )
            session.add(user)
            session.flush()

        existing_links = set(
            session.scalars(
                select(SeenJob.job_link).where(SeenJob.user_id == user.id)
            ).all()
        )
        for link in body.job_links:
            if link and link not in existing_links:
                session.add(SeenJob(user_id=user.id, job_link=link, job_score=0))

        user.last_triggered_at = datetime.utcnow()
        session.commit()

        # Store values INSIDE session before it closes
        user_id = user.id
        user_interval = user.alert_interval_hours
        user_email = user.email
        user_query = user.job_query
        user_best = user.best_score

    schedule_user_job(user_id, user_interval)
    return {
        "ok": True,
        "user_id": user_id,
        "email": user_email,
        "job_query": user_query,
        "alert_interval_hours": user_interval,
        "best_score": user_best,
    }


@app.post("/ultimate-match")
async def ultimate_match(
    file: UploadFile = File(...),
    email: Optional[str] = Form(None),
    job_query: Optional[str] = Form("AI Engineer"),
):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    content = await file.read()

    # Step 1: Parse & Extract CV Data
    cv_dict = get_structured_cv(content)
    if "error" in cv_dict:
        raise HTTPException(status_code=422, detail=f"Document parsing failed: {cv_dict['error']}")
    
    cv_data = extract_cv_data(cv_dict)
    if "error" in cv_data:
        raise HTTPException(status_code=422, detail=f"CV extraction failed: {cv_data['error']}")

    # Step 2: Fetch jobs
    query = (job_query or "AI Engineer").strip()
    jobs = fetch_jobs(query)
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found from API")

    # Step 3: Initial Matching
    matched_jobs = jobs
    if not matched_jobs:
        raise HTTPException(status_code=404, detail="No matches found")

    # Step 4: Multi-threaded Scoring with Gemini
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(executor, calculate_score, cv_data, job.get("description", ""))
            for job in matched_jobs[:3]
        ]
        scores = await asyncio.gather(*tasks)

    # Step 5: Build Final Results (Including Salary Prediction)
    ranked_results = []
    for job, scoring in zip(matched_jobs[:3], scores):
        
        # --- نداء موديل CatBoost الجديد ---
        expected_salary = predict_salary_jod(
            job_title=job.get("title", query),
            industry=cv_data.get("industry", "Technology"), 
            experience=cv_data.get("experience_level", "mid-level"),
            education=cv_data.get("education", "bachelor's"),
            location="JO", 
            remote_ratio=100 if "remote" in job.get("title", "").lower() else 0
        )

        ranked_results.append({
            "company": job.get("company"),
            "title": job.get("title"),
            "link": job.get("link"),
            "score": f"{scoring.get('match_score', 0)}%",
            "predicted_salary": f"{expected_salary:,} JOD", # إضافة الراتب المتوقع بالدينار
            "raw_score": scoring.get("match_score", 0),
            "verdict": scoring.get("verdict"),
            "can_apply": scoring.get("can_apply"),
            "match_summary": scoring.get("match_summary"),
            "missing_skills": scoring.get("missing_skills_analysis"),
            "application_message": scoring.get("application_message"),
            "final_advice": scoring.get("final_advice")
        })

    # ترتيب النتائج بناءً على النتيجة الأعلى
    ranked_results.sort(key=lambda x: x["raw_score"], reverse=True)

    # Step 6: Roadmap for the top matched job
    roadmap = get_roadmap(cv_data["skills"], ranked_results[0]["title"])

    
    return {
        "candidate_summary": cv_data,
        "job_leaderboard": ranked_results,
        "learning_roadmap": roadmap
    }

@app.post("/generate-pdf")
async def generate_pdf_report(file: UploadFile = File(...), email: str = Form(""), job_query: str = Form("AI Engineer")):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    content = await file.read()
    cv_dict = get_structured_cv(content)
    cv_data = extract_cv_data(cv_dict)

    if "error" in cv_data:
        raise HTTPException(status_code=422, detail=f"CV extraction failed: {cv_data['error']}")

    jobs = fetch_jobs((job_query or "AI Engineer").strip())
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found")

    query = (job_query or "AI Engineer").strip()
    loop = asyncio.get_event_loop()
    matched_jobs = jobs

    if not matched_jobs:
        raise HTTPException(status_code=404, detail="No matches found")

    with ThreadPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(executor, calculate_score, cv_data, job.get("description", ""))
            for job in matched_jobs[:3]
        ]
        scores = await asyncio.gather(*tasks)

    ranked_results = []
    for job, scoring in zip(matched_jobs[:3], scores):
        # Calculate salary prediction
        expected_salary = predict_salary_jod(
            job_title=job.get("title", query),
            industry=cv_data.get("industry", "Technology"),
            experience=cv_data.get("experience_level", "mid-level"),
            education=cv_data.get("education", "bachelor's"),
            location="JO",
            remote_ratio=100 if "remote" in job.get("title", "").lower() else 0
        )
        
        ranked_results.append({
            "company": job.get("company"),
            "title": job.get("title"),
            "link": job.get("link"),
            "score": f"{scoring.get('match_score', 0)}%",
            "predicted_salary": f"{expected_salary:,} JOD",
            "raw_score": scoring.get("match_score", 0),
            "verdict": scoring.get("verdict"),
            "can_apply": scoring.get("can_apply"),
            "match_summary": scoring.get("match_summary"),
            "missing_skills": scoring.get("missing_skills_analysis"),
            "application_message": scoring.get("application_message"),
            "final_advice": scoring.get("final_advice")
        })

    ranked_results.sort(key=lambda x: x["raw_score"], reverse=True)
    roadmap = get_roadmap(cv_data["skills"], ranked_results[0]["title"])

    api_data = {
        "candidate_summary": cv_data,
        "job_leaderboard": ranked_results,
        "learning_roadmap": roadmap
    }

    pdf_bytes = generate_pdf(api_data, file.filename)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=CareerLens_Report.pdf"}
    )

@app.post("/generate-docx")
async def generate_docx_report(file: UploadFile = File(...), email: str = Form(""), job_query: str = Form("AI Engineer")):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    content = await file.read()
    cv_dict = get_structured_cv(content)
    cv_data = extract_cv_data(cv_dict)

    if "error" in cv_data:
        raise HTTPException(status_code=422, detail=f"CV extraction failed: {cv_data['error']}")

    jobs = fetch_jobs((job_query or "AI Engineer").strip())
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found")

    loop = asyncio.get_event_loop()
    matched_jobs = jobs

    if not matched_jobs:
        raise HTTPException(status_code=404, detail="No matches found")

    with ThreadPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(executor, calculate_score, cv_data, job.get("description", ""))
            for job in matched_jobs[:3]
        ]
        scores = await asyncio.gather(*tasks)

    ranked_results = []
    query = (job_query or "AI Engineer").strip()
    for job, scoring in zip(matched_jobs[:3], scores):
        # Calculate salary prediction
        expected_salary = predict_salary_jod(
            job_title=job.get("title", query),
            industry=cv_data.get("industry", "Technology"),
            experience=cv_data.get("experience_level", "mid-level"),
            education=cv_data.get("education", "bachelor's"),
            location="JO",
            remote_ratio=100 if "remote" in job.get("title", "").lower() else 0
        )
        
        ranked_results.append({
            "company": job.get("company"),
            "title": job.get("title"),
            "link": job.get("link"),
            "score": f"{scoring.get('match_score', 0)}%",
            "predicted_salary": f"{expected_salary:,} JOD",
            "raw_score": scoring.get("match_score", 0),
            "verdict": scoring.get("verdict"),
            "can_apply": scoring.get("can_apply"),
            "match_summary": scoring.get("match_summary"),
            "missing_skills": scoring.get("missing_skills_analysis"),
            "application_message": scoring.get("application_message"),
            "final_advice": scoring.get("final_advice")
        })

    ranked_results.sort(key=lambda x: x["raw_score"], reverse=True)
    roadmap = get_roadmap(cv_data["skills"], ranked_results[0]["title"])

    api_data = {
        "candidate_summary": cv_data,
        "job_leaderboard": ranked_results,
        "learning_roadmap": roadmap
    }

    docx_bytes = generate_docx(api_data, file.filename)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=CareerLens_Report.docx"}
    )

class TriggerBody(BaseModel):
    alert_no_match: bool = False

@app.post("/run-trigger")
async def run_trigger(background_tasks: BackgroundTasks, body: TriggerBody):
    with SessionLocal() as session:
        users = session.scalars(select(User)).all()
        user_ids = [u.id for u in users]
    for uid in user_ids:
        background_tasks.add_task(check_user_trigger, uid, body.alert_no_match)
    return {"ok": True, "triggered": len(user_ids)}
@app.get("/front_page")
async def serve_front_page():
    path = BASE_DIR / "front_page.html"

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="front_page.html not found"
        )

    return FileResponse(path)


@app.get("/upload_page")
async def serve_upload_page():
    path = BASE_DIR / "upload_page.html"

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="upload_page.html not found"
        )

    return FileResponse(path)