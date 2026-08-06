from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import verify_kiosk_grant
from backend.schemas.api import AIFeedbackRequest,AIRequest,RecommendRequest
from backend.models.entities import AIFeedback,AIInteraction
from backend.services.recommendation_service import ai_search,recommendations
router=APIRouter(prefix="/ai",tags=["AI Assistant"])
@router.post("/search")
def search(payload:AIRequest,db:Session=Depends(get_db)):
    if payload.user_id:verify_kiosk_grant(payload.user_verification_token,payload.user_id)
    return ai_search(db,payload.query,payload.user_id)
@router.post("/recommend")
def recommend(payload:RecommendRequest,db:Session=Depends(get_db)):
    if payload.user_id:verify_kiosk_grant(payload.user_verification_token,payload.user_id)
    return recommendations(db,payload.user_id,payload.kind)

@router.post("/feedback",status_code=201)
def feedback(payload:AIFeedbackRequest,db:Session=Depends(get_db)):
    if payload.user_id:verify_kiosk_grant(payload.user_verification_token,payload.user_id)
    interaction=db.get(AIInteraction,payload.interaction_id)
    if not interaction:raise HTTPException(404,"AI interaction not found.")
    if interaction.user_id is not None and interaction.user_id!=payload.user_id:raise HTTPException(403,"This interaction belongs to another user.")
    existing=db.scalar(select(AIFeedback).where(AIFeedback.interaction_id==interaction.id,AIFeedback.user_id==payload.user_id)) if payload.user_id else None
    if existing:
        existing.helpful=payload.helpful;existing.reason=payload.reason
    else:db.add(AIFeedback(interaction_id=interaction.id,user_id=payload.user_id,helpful=payload.helpful,reason=payload.reason))
    db.commit();return {"message":"Thank you. Your feedback will improve library recommendations."}
