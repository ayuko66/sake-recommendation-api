from pydantic import BaseModel
from typing import List, Optional

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
