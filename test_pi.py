from app.core.database import SessionLocal, User, SeenJob
from sqlalchemy import select
import time

with SessionLocal() as session:
    user = session.execute(select(User).where(User.email == "ai.ahmad.3a4@gmail.com")).scalar_one_or_none()
    if not user:
        print("User not found!")
    else:
        # Use a timestamp in the link to make it a "new" job every time we run this test
        unique_link = f"https://careerlens.ai/test-job-{int(time.time())}"
        
        test_job = SeenJob(
            user_id=user.id,
            job_link=unique_link,
            job_title="Senior AI Architect (Trigger Test)",
            job_company="Arabic.AI (VPRO TEST)",
            job_score=98,
            pi_alerted=False
        )
        session.add(test_job)
        session.commit()
        print(f"Test Trigger Sent! Score: 98%. Link: {unique_link}")
