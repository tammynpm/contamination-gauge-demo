from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: Optional[str] = None
    errors: Optional[list] = None

class AnalysisMetrics(BaseModel):
    spot_coverage: float = Field(..., ge=0, le=1, description="fraction of image covered by spots")
    edge_density: float = Field(..., ge=0, le=1, description="normialized edge density")
    texture_variance: float = Field(...,ge=0, description="standard deviation of pixel intensities")
    mean_intensity: float = Field(..., ge=0, le=255, description="average pixel brightness")

class AnalysisResponse(BaseModel):
    score: float = Field(..., ge=0, le=100, description="contamination score 0-100")
<<<<<<< HEAD
=======
    label: str = Field(..., description="contamination level")
>>>>>>> master
    baseline_id: str = Field(..., description="id of baseline")
    baseline_score: float = Field(..., description="expected score for baseline")
    delta: float = Field(...)
    metrics: AnalysisMetrics = Field(..., description="detailed analysis metrics")
    sample_name: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Baseline(BaseModel):
    id: str
    name: str
    description: str
    expected_score: float = Field(..., ge=0, le=100)
