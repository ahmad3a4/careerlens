import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.database import SessionLocal, SeenJob, User
from app.services.background import schedule_user_job, register_all_user_jobs, check_user_trigger
from app.services.cv_parser import get_structured_cv
from app.services.extractor import extract_cv_data
from app.services.job_search import fetch_jobs
from app.services.scorer import calculate_score
from app.services.roadmap import get_roadmap
from app.services.pdf_generator import generate_pdf
from app.services.docx_generator import generate_docx
from app.services.salary_predictor import predict_salary_jod
from app.services.cv_resume_builder import build_resume_docx
from app.core.llm import chat_completion, conversational_completion

BASE_DIR = Path(__file__).resolve().parent.parent
PREFERENCES_PATH = BASE_DIR / "user_preferences.json"
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="CV Matcher API")


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


class InterviewRequest(BaseModel):
    job_title: str
    company: str
    description: str
    cv_summary: dict[str, Any]

class EvaluateRequest(BaseModel):
    question: str
    answer: str
    job_description: str
    cv_summary: dict[str, Any]



@app.on_event("startup")
async def startup_event():
    register_all_user_jobs()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ====== FRONTEND ROUTES ======

@app.get("/")
async def root():
    path = STATIC_DIR / "html" / "index.html"
    if not path.is_file():
        path = BASE_DIR / "index.html"
    if not path.is_file():
        path = BASE_DIR / "front_page.html"
    if not path.is_file():
        path = BASE_DIR / "careerlens.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Front page not found")
    return FileResponse(path, media_type="text/html")


@app.get("/index")
async def index():
    return await root()


@app.get("/front")
async def front_page():
    path = BASE_DIR / "front_page.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="front_page.html not found")
    return FileResponse(path, media_type="text/html")


@app.get("/upload")
async def upload_page():
    path = STATIC_DIR / "html" / "upload.html"
    if not path.is_file():
        path = BASE_DIR / "upload_page.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="upload_page.html not found")
    return FileResponse(path, media_type="text/html")


@app.get("/dashboard")
async def careerlens_dashboard():
    path = STATIC_DIR / "html" / "careerlens.html"
    if not path.is_file():
        path = BASE_DIR / "careerlens.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="careerlens.html not found")
    return FileResponse(path, media_type="text/html")


@app.get("/careerlens.html")
async def serve_careerlens():
    return await careerlens_dashboard()


@app.get("/settings.html")
async def serve_settings_html():
    path = BASE_DIR / "settings.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="settings.html not found")
    return FileResponse(path, media_type="text/html")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "CareerLens API"}


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

    cv_dict = get_structured_cv(content)
    if "error" in cv_dict:
        raise HTTPException(status_code=422, detail=f"Document parsing failed: {cv_dict['error']}")

    cv_data = extract_cv_data(cv_dict)
    if "error" in cv_data:
        raise HTTPException(status_code=422, detail=f"CV extraction failed: {cv_data['error']}")

    query = (job_query or "AI Engineer").strip()
    jobs = fetch_jobs(query)
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found from API")

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
        # Predict salary for each job
        try:
            is_remote = job.get("is_remote", False)
            remote_ratio = 100 if is_remote else 0
            job_country = job.get("country", "JO")
            
            base_salary = predict_salary_jod(
                job_title=job.get("title", ""),
                industry=cv_data.get("industry", "Tech"),
                experience=str(cv_data.get("years_exp", 0)),
                education=cv_data.get("education", "Bachelors"),
                location=job_country,
                remote_ratio=remote_ratio
            )
            
            if base_salary:
                # Add deterministic variation based on company name (-10% to +10%)
                company_name = job.get("company") or "Unknown"
                company_hash = sum(ord(c) for c in company_name) % 21
                variation = (company_hash - 10) / 100.0  # -0.10 to +0.10
                adjusted_salary = base_salary * (1 + variation)
                
                # Create a rounded range (nearest 50)
                lower = int((adjusted_salary * 0.9) / 50) * 50
                upper = int((adjusted_salary * 1.1) / 50) * 50
                if lower == upper:
                    upper += 50
                
                predicted_salary = f"{lower} - {upper} JOD"
            else:
                predicted_salary = "—"
        except Exception:
            predicted_salary = "—"

        ranked_results.append({
            "company": job.get("company"),
            "title": job.get("title"),
            "link": job.get("link"),
            "score": f"{scoring.get('match_score', 0)}%",
            "raw_score": scoring.get("match_score", 0),
            "cosine_score": job.get("cosine_score"),
            "rerank_score": job.get("rerank_score"),
            "verdict": scoring.get("verdict"),
            "can_apply": scoring.get("can_apply"),
            "match_summary": scoring.get("match_summary"),
            "missing_skills": scoring.get("missing_skills_analysis"),
            "application_message": scoring.get("application_message"),
            "final_advice": scoring.get("final_advice"),
            "predicted_salary": predicted_salary,
        })

    ranked_results.sort(key=lambda x: x["raw_score"], reverse=True)

    roadmap = get_roadmap(cv_data["skills"], ranked_results[0]["title"])

    return {
        "candidate_summary": cv_data,
        "job_leaderboard": ranked_results,
        "learning_roadmap": roadmap
    }


@app.post("/generate-pdf")
async def generate_pdf_report(request: Request):
    """Accept pre-computed apiData JSON from frontend and generate PDF."""
    try:
        api_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not api_data.get("job_leaderboard"):
        raise HTTPException(status_code=400, detail="Missing job_leaderboard in request body")

    pdf_bytes = generate_pdf(api_data, "CV")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=CareerLens_Report.pdf"}
    )


@app.post("/generate-docx")
async def generate_docx_report(request: Request):
    """Accept pre-computed apiData JSON from frontend and generate DOCX."""
    try:
        api_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not api_data.get("job_leaderboard"):
        raise HTTPException(status_code=400, detail="Missing job_leaderboard in request body")

    docx_bytes = generate_docx(api_data, "CV")
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=CareerLens_Report.docx"}
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


@app.post("/generate-resume")
async def generate_resume(request: Request):
    """Accept structured resume data from the CV Creator form and return a DOCX."""
    try:
        resume_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not resume_data.get("full_name"):
        raise HTTPException(status_code=400, detail="full_name is required")

    docx_bytes = build_resume_docx(resume_data)
    safe_name = resume_data.get("full_name", "Resume").replace(" ", "_")
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={safe_name}_Resume.docx"}
    )


class ImproveTextRequest(BaseModel):
    text: str
    field_type: str


@app.post("/improve-text")
async def improve_text(req: ImproveTextRequest):
    """Rewrite CV text based on field type using the LLM."""
    if not req.text.strip():
        return {"improved_text": ""}

    prompts = {
        "summary": "You are an expert resume writer. Rewrite the following professional summary to be 2-3 sentences long, highly professional, ATS-friendly, and focused on impact and skills. Output ONLY the rewritten text, with no introductory or conversational text:\n\n",
        "experience": "You are an expert resume writer. Rewrite the following experience bullet points to start with strong action verbs, quantify results where possible, and be highly professional and ATS-friendly. Output ONLY the rewritten bullet points (separated by newlines), with no introductory or conversational text:\n\n",
        "projects": "You are an expert resume writer. Rewrite the following project description to clearly convey the technical scope, tools used, and business/technical outcome. Keep it concise, professional, and ATS-friendly. Output ONLY the rewritten description, with no introductory or conversational text:\n\n"
    }

    base_prompt = prompts.get(req.field_type, "You are an expert resume writer. Improve the following text to be more professional, concise, and ATS-friendly. Output ONLY the rewritten text:\n\n")
    full_prompt = base_prompt + req.text

    try:
        # Run synchronous chat_completion in a threadpool to not block the event loop
        loop = asyncio.get_running_loop()
        improved_text = await loop.run_in_executor(None, chat_completion, full_prompt)
        return {"improved_text": improved_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    user_context: Optional[dict] = None

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Context-aware chatbot endpoint strictly bounded to career advice."""
    
    # Construct a strong system prompt
    system_prompt = (
        "You are the CareerLens AI Assistant, a core feature of the CareerLens VPRO web platform. "
        "Your purpose is to help users with their career, resume, job matching, professional advice, "
        "and answering questions about how the CareerLens platform works. "
        "CareerLens features include AI-powered resume building, ATS-friendly document generation, "
        "automated job matching via the JSearch API, personalized salary predictions, and an automated background job alert system.\n"
        "You MUST STRICTLY refuse to answer any questions outside of career advice, resumes, job searching, or the platform itself "
        "(e.g., general trivia, unrelated coding requests, math problems). If asked an off-topic question, "
        "politely say 'I am a career assistant and can only help with resumes, job searching, career advice, or explaining this platform.'\n\n"
    )
    
    if req.user_context:
        # Inject the user's CV context so the bot can be personalized
        skills = req.user_context.get("skills", [])
        exp = req.user_context.get("years_exp", 0)
        ind = req.user_context.get("industry", "Unknown")
        summary = req.user_context.get("summary", "")
        
        system_prompt += f"Here is the user's context:\n- Industry: {ind}\n- Experience: {exp} years\n- Skills: {', '.join(skills)}\n"
        if summary:
            system_prompt += f"- Professional Summary: {summary}\n"
        system_prompt += "\nUse this context to provide highly personalized advice and directly answer questions about their summary or profile."

    # Convert Pydantic models to dicts
    messages_dict = [{"role": m.role, "content": m.content} for m in req.messages]

    try:
        loop = asyncio.get_running_loop()
        reply = await loop.run_in_executor(None, conversational_completion, messages_dict, system_prompt)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-interview")
async def generate_interview(req: InterviewRequest):
    """Generate 10 technical and behavioral interview questions."""
    prompt = f"""
    You are an expert technical recruiter and hiring manager. 
    Generate 10 challenging and highly relevant interview questions for the following role:
    Role: {req.job_title} at {req.company}
    
    Job Description Snippet:
    {req.description[:1500]}
    
    Candidate Summary:
    - Industry: {req.cv_summary.get('industry', 'Unknown')}
    - Experience: {req.cv_summary.get('years_exp', 0)} years
    - Skills: {', '.join([s['name'] if isinstance(s, dict) else s for s in req.cv_summary.get('skills', [])])}
    - Summary: {req.cv_summary.get('summary', '')}

    
    Instructions:
    1. Generate 5 Technical questions based on the JD and candidate's skills.
    2. Generate 5 Behavioral questions (STAR method style).
    3. Return ONLY a valid JSON array of objects.
    
    Format:
    [
        {{"type": "technical", "question": "..."}},
        {{"type": "behavioral", "question": "..."}}
    ]
    """
    try:
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, chat_completion, prompt)
        print(f"DEBUG: /generate-interview RAW: {text[:500]}")
        
        # Robust JSON extraction
        if "```json" in text:
            clean = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            clean = text.split("```")[1].split("```")[0].strip()
        else:
            clean = text.strip()
            
        questions = json.loads(clean)
        return {"questions": questions}
    except Exception as e:
        print(f"DEBUG: /generate-interview ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate-interview-answer")
async def evaluate_interview_answer(req: EvaluateRequest):
    """Evaluate a user's answer to an interview question."""
    prompt = f"""
    Evaluate the following interview answer.
    
    Job Description: {req.job_description[:1000]}
    Candidate Skills: {', '.join([s['name'] if isinstance(s, dict) else s for s in req.cv_summary.get('skills', [])])}
    
    Question: {req.question}

    User Answer: {req.answer}
    
    Return ONLY a valid JSON object with:
    1. "score": integer 0-10
    2. "strengths": string
    3. "weaknesses": string
    4. "better_answer": a sample better version of their answer
    5. "tips": specific tips for improvement
    
    JSON Format:
    {{
        "score": 8,
        "strengths": "...",
        "weaknesses": "...",
        "better_answer": "...",
        "tips": "..."
    }}
    """
    try:
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, chat_completion, prompt)
        print(f"DEBUG: /evaluate-interview-answer RAW: {text[:500]}")

        # Robust JSON extraction
        if "```json" in text:
            clean = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            clean = text.split("```")[1].split("```")[0].strip()
        else:
            clean = text.strip()

        evaluation = json.loads(clean)
        return evaluation
    except Exception as e:
        print(f"DEBUG: /evaluate-interview-answer ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pi/poll-alert")
async def pi_poll_alert(email: str):
    """Endpoint for Raspberry Pi to poll for high-score matches."""
    with SessionLocal() as session:
        user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user:
            return {"match": False}
        
        match = session.execute(
            select(SeenJob)
            .where(SeenJob.user_id == user.id)
            .where(SeenJob.job_score >= 90)
            .where(SeenJob.pi_alerted == False)
            .order_by(SeenJob.job_score.desc())
        ).scalars().first()
        
        if match:
            # Get user context for better salary prediction
            sumry = user.candidate_summary or {}
            salary = predict_salary_jod(
                match.job_title,
                sumry.get("industry", "Technology"),
                str(sumry.get("years_exp", "0")),
                sumry.get("education", "Bachelor"),
                "Jordan",
                0
            )
            match.pi_alerted = True
            session.commit()
            return {
                "match": True,
                "title": match.job_title,
                "company": match.job_company,
                "score": match.job_score,
                "link": match.job_link,
                "salary": salary
            }
        return {"match": False}


class PiChatRequest(BaseModel):
    email: str
    text: str


@app.post("/api/pi/chat")
async def pi_chat_endpoint(req: PiChatRequest):
    """Dedicated endpoint for Raspberry Pi voice chat with full CV context."""
    with SessionLocal() as session:
        user = session.execute(select(User).where(User.email == req.email)).scalar_one_or_none()
        if not user:
            return {"response": "I'm sorry, I couldn't find your user profile. Please upload a CV first."}
        
        ctx = user.candidate_summary or {}
        system_prompt = (
            "You are the CareerLens AI Assistant speaking through a Raspberry Pi device. "
            "You have access to the user's CV. Keep your answers concise, professional, and friendly, "
            "as they will be read out loud via text-to-speech. Focus strictly on career advice.\n\n"
            f"User Context:\n- Industry: {ctx.get('industry', 'Unknown')}\n"
            f"- Experience: {ctx.get('years_exp', '0')} years\n"
            f"- Skills: {', '.join([s['name'] if isinstance(s, dict) else s for s in ctx.get('skills', [])])}\n"
            f"- Summary: {ctx.get('summary', '')}\n\n"
        )
        
        full_prompt = system_prompt + f"User Question: {req.text}"
        
        try:
            loop = asyncio.get_running_loop()
            response_text = await loop.run_in_executor(None, chat_completion, full_prompt)
            return {"response": response_text}
        except Exception as e:
            return {"response": f"I encountered an error while thinking: {str(e)}"}






