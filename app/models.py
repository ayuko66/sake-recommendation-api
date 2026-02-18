from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union

class TasteProfile(BaseModel):
    sweet_dry: float
    body: float
    fruity: str
    style: float

class SakeBase(BaseModel):
    sake_id: int
    name: str
    brewery: Optional[str] = None
    prefecture: Optional[str] = None

class SakeListItem(SakeBase):
    pass

class SakeDetail(SakeBase):
    rice: Optional[str] = None
    grade: Optional[str] = None
    abv: Optional[float] = None
    taste_profile: Optional[TasteProfile] = None

class SakeListResponse(BaseModel):
    items: List[SakeListItem]
    total: int
    page: int
    limit: int

class SakeSearchResponse(BaseModel):
    items: List[SakeListItem]


class RecommendationFilters(BaseModel):
    prefecture: Optional[List[str]] = None
    exclude_brewery: Optional[List[str]] = None

class RecommendationRequest(BaseModel):
    text: str
    top_k: Optional[int] = 5
    filters: Optional[RecommendationFilters] = None
    debug: Optional[bool] = False

class RecommendationItem(SakeListItem):
    score: float
    distance: float
    taste_vector: List[float]
    reason: str
    debug_info: Optional[Dict[str, Any]] = None

class RecommendationQuery(BaseModel):
    taste_vector: List[float]

class RecommendationResponse(BaseModel):
    input_text: str
    top_k: int
    mode: str = "dict"
    query: RecommendationQuery
    recommendations: List[RecommendationItem]


class VectorStatusResponse(BaseModel):
    total_sakes: int
    total_vectors: int
    pending_count: int
    last_computed_at: Optional[str] = None
