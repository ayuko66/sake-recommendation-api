from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from . import database as db
from .models import (
    SakeListResponse, 
    SakeDetail, 
    SakeSearchResponse,
    SakeListItem,
    VectorStatusResponse,
    RecommendationRequest,
    RecommendationResponse
)
from .reco import engine

app = FastAPI(title="Sake Recommendation API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/vectors/status", response_model=VectorStatusResponse)
def get_vector_status():
    return db.get_vector_status()

@app.get("/sakes", response_model=SakeListResponse)
def list_sakes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    items = db.get_sakes(page, limit)
    total = db.get_total_sakes()
    return SakeListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit
    )

@app.get("/sakes/{sake_id}", response_model=SakeDetail)
def get_sake(sake_id: int):
    sake = db.get_sake_by_id(sake_id)
    if not sake:
        raise HTTPException(status_code=404, detail="Sake not found")
    return sake

@app.get("/search", response_model=SakeSearchResponse)
def search_sakes(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100)
):
    items = db.search_sakes(q, limit)
    return SakeSearchResponse(items=items)

@app.post("/recommend", response_model=RecommendationResponse)
def recommend_sakes(request: RecommendationRequest):
    return engine.recommend(request)
