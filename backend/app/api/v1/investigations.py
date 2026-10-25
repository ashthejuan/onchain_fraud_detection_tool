from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import InvestigationReport
from app.services.investigation import make_report

router = APIRouter(tags=["investigations"])


class GenerateRequest(BaseModel):
    regenerate: bool = False


class GenerateResponse(BaseModel):
    report_id: int
    assessment_id: int
    status: str
    report: dict[str, object]


def serialize_report(report: InvestigationReport) -> GenerateResponse:
    return GenerateResponse(report_id=report.id, assessment_id=report.assessment_id, status=report.status, report=report.report_json or {})


@router.post("/assessments/{assessment_id}/investigation-report", response_model=GenerateResponse)
def create_investigation_report(assessment_id: int, body: GenerateRequest, session: Annotated[Session, Depends(get_db)]) -> GenerateResponse:
    return serialize_report(make_report(session, assessment_id, body.regenerate))


@router.get("/reports/{report_id}", response_model=GenerateResponse)
def get_investigation_report(report_id: int, session: Annotated[Session, Depends(get_db)]) -> GenerateResponse:
    report = session.scalar(select(InvestigationReport).where(InvestigationReport.id == report_id))
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return serialize_report(report)
