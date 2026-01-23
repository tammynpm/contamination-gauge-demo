
analysis algorithm
- grayscale conversion
- gaussian blur 
- spot detection
- edge detection
- score = weighte_sum(spot_density, edge_density)

endpoints
POST /analyze
- input: multipart/form-data (image, baseline_id, metadata)
- output: {score, baseline_id, delta, label, metrics}

POST /baselines/create
GET /scans?limit=N

example payload
{

    "score": 72.3,
    "baseline_id": "clean_lab",
    "delta": +47.2,
    "label": "high",
    "metrics": {
        "spot_coverage": 0.15,
        "edge_density": 0.68
    }
}


---
