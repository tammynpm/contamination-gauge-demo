from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import io
from PIL import Image, UnidentifiedImageError
from typing import Optional
import asyncio
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


from database.db import engine
from sqlalchemy import text, func

from middleware.request_id import RequestIDMiddleware
from middleware.auth import APIKeyMiddleware

from models.schemas import AnalysisMetrics, AnalysisResponse, ErrorResponse
from analysis.baselines import BaselineManager
from analysis.scorer import ContaminationScorer

from database.db import init_db, get_db
from database.models import Scan

def get_rate_limit_key(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"
    return f"ip:{get_remote_address(request)}"
limiter = Limiter(key_func=get_rate_limit_key)

app = FastAPI(
    title="contamination gauge API",
    description="image analysis API for surface contamination scoring",
    version="0.1.0"
)

origins = [
    "http://localhost",
    "http://localhost:8000"
]

app.state.limiter = limiter
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(APIKeyMiddleware)

logger = logging.getLogger(__name__)

#initialize components
baseline_manager = BaselineManager()
scorer = ContaminationScorer()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {
        "message": "contamination gauge API",
        "version": "0.1.0",
        "endpoints": {
            "analyze": "POST /analyze",
            "health": "GET /health"
        }
    }


@app.get("/ready")
async def readiness_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "database": "disconnected", "error": str(e)}
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/jpg", "image/png"]
ALLOWED_FORMATS = {"JPEG", "PNG"}
MIN_IMAGE_DIM = 100
MAX_IMAGE_DIM = 4096
ANALYZE_TIMEOUT_SECONDS = 30

def _build_error_response(request: Request, status_code: int, message: str, errors: Optional[list] = None) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    error = {
        400: "bad_request",
        422: "validation_error",
        429: "rate_limit_exceeded",
        500: "server_error",
        504: "timeout"
    }.get(status_code, "error")
    payload = ErrorResponse(
        error=error,
        message=message,
        request_id=request_id,
        errors=errors
    ).dict()
    return JSONResponse(status_code=status_code, content=payload)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("http_exception", extra={"request_id": getattr(request.state, "request_id", None), "status_code": exc.status_code})
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return _build_error_response(request, exc.status_code, message)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("validation_error", extra={"request_id": getattr(request.state, "request_id", None), "errors": exc.errors()})
    return _build_error_response(request, 422, "Validation error", errors=exc.errors())

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception", extra={"request_id": getattr(request.state, "request_id", None)})
    return _build_error_response(request, 500, "Internal server error")

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    request_id = getattr(request.state, "request_id", None)
    retry_after = int(exc.retry_after) if exc.retry_after else 60
    response = _build_error_response(
        request,
        429,
        f"Rate limit exceeded. Try again after {retry_after} seconds"
    )
    response.headers["Retry-After"] = str(retry_after)
    logger.warning(
        "rate_limit_exceeded",
        extra = {
            "request_id": request_id,
            "retry_after": retry_after,
            "endpoint": request.url.path
        }
    )
    return response

@app.post("/analyze", response_model=AnalysisResponse)
@limiter.limit("60/minute")
async def analyze_image(
    request: Request,
    image: UploadFile = File(...),
    baseline_id: str = Form(default="clean_surface"),
    sample_name: Optional[str] = Form(default=None),
    location: Optional[str] = Form(default=None),
    notes: Optional[str] = Form(default=None)
):
    try:

        contents = await image.read()
        
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        if image.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {ALLOWED_CONTENT_TYPES}"
            )

        # validate image  
        try:
            with Image.open(io.BytesIO(contents)) as img:
                img.verify()
                if img.format not in ALLOWED_FORMATS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid image format. Allowed: {sorted(ALLOWED_FORMATS)}"
                    )
            pil_image = Image.open(io.BytesIO(contents))
        except UnidentifiedImageError:
            raise HTTPException(status_code=400, detail="Invalid or corrupted image")

        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        width, height = pil_image.size
        if width < MIN_IMAGE_DIM or height < MIN_IMAGE_DIM or width > MAX_IMAGE_DIM or height > MAX_IMAGE_DIM:
            raise HTTPException(
                status_code=400,
                detail=f"Image dimensions must be between {MIN_IMAGE_DIM}x{MIN_IMAGE_DIM} and {MAX_IMAGE_DIM}x{MAX_IMAGE_DIM}"
            )

        try:
            score, metrics = await asyncio.wait_for(
                asyncio.to_thread(scorer.analyze, pil_image),
                timeout=ANALYZE_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Image processing timed out")

        baseline = baseline_manager.get_baseline(baseline_id)
        delta = score - baseline.expected_score
        
        label = _get_contamination_label(score)

        with get_db() as db:
            scan = Scan(
                score=round(score,2),
                baseline_id = baseline_id,
                baseline_score=baseline.expected_score,
                delta=round(delta,2),
                label=label,
                spot_coverage=metrics.spot_coverage,
                edge_density=metrics.edge_density,
                texture_variance=metrics.texture_variance,
                mean_intensity=metrics.mean_intensity,
                sample_name=sample_name,
                location=location,
                notes=notes
            )
            db.add(scan)

        return AnalysisResponse(
            score=round(score,2),
            baseline_id=baseline_id,
            baseline_score=baseline.expected_score,
            delta=round(delta,2),
            label=label,
            metrics=metrics,
            sample_name=sample_name,
            location=location,
            notes=notes
        )
    except HTTPException: 
        raise 
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.exception(
            "analysis_failed",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "error": error_msg,
                "error_type": error_type,
            }
        )

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {error_type}: {error_msg}"
        )

def _get_contamination_label(score:float) ->str:
    if score < 33:
        return "low"
    elif score < 67:
        return "moderate"
    else:
        return "high"

@app.get("/baselines")
async def list_baselines():
    baselines_dict = baseline_manager.list_baselines()
    # Convert dict to list for JSON serialization
    return {"baselines": [baseline.dict() for baseline in baselines_dict.values()]}

@app.get("/stats")
async def get_stats():
    with get_db() as db:
        total_scans = db.query(func.count(Scan.id)).scalar() or 0
        if total_scans==0:
            return {
                "total_scans": 0,
                "average_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
                "by_label": {
                    "low": 0,
                    "moderate": 0,
                    "high": 0
                }
            }
        stats = db.query(
            func.avg(Scan.score).label('avg_score'),
            func.min(Scan.score).label('min_score'),
            func.max(Scan.score).label('max_score')
        ).first()

        label_counts=db.query(
            Scan.label,
            func.count(Scan.id).label('count')
        ).group_by(Scan.label).all()

        by_label={"low":0, "moderate":0, "high":0}
        for label, count in label_counts:
            by_label[label] = count
        return {
            "total_scans": total_scans,
            "average_score": round(stats.avg_score or 0.0,2),
            "min_score": round(stats.min_score or 0.0,2),
            "max_score": round(stats.max_score or 0.0,2),
            "by_label": by_label
        } 

if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
