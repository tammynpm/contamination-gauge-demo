"""Test database functionality."""
import io
from PIL import Image
from fastapi.testclient import TestClient
from database.db import get_db, init_db
from database.models import Scan
from sqlalchemy import func
from main import app

def create_test_image():
    """Create a simple test image."""
    img = Image.new('RGB', (500, 500), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def test_scan_saved_to_database():
    """Test that /analyze saves scan to database."""
    # Initialize database
    init_db()
    
    client = TestClient(app)
    
    # Get initial scan count
    with get_db() as db:
        initial_count = db.query(func.count(Scan.id)).scalar()
    
    # Create and analyze an image
    image_file = create_test_image()
    response = client.post(
        "/analyze",
        files={"image": ("test.png", image_file, "image/png")},
        data={
            "baseline_id": "clean_surface",
            "sample_name": "Database-Test"
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    
    # Check database - should have one more scan
    with get_db() as db:
        new_count = db.query(func.count(Scan.id)).scalar()
        assert new_count == initial_count + 1
        
        # Get the scan we just created
        latest_scan = db.query(Scan).filter(
            Scan.sample_name == "Database-Test"
        ).first()
        
        assert latest_scan is not None
        assert latest_scan.score == data["score"]
        assert latest_scan.baseline_id == "clean_surface"
        assert latest_scan.label == data["label"]

def test_stats_returns_real_data():
    """Test that /stats returns real database data."""
    client = TestClient(app)
    
    # Make sure we have at least one scan
    image_file = create_test_image()
    client.post(
        "/analyze",
        files={"image": ("test.png", image_file, "image/png")},
        data={"baseline_id": "clean_surface"}
    )
    
    # Get stats
    response = client.get("/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_scans"] > 0
    assert "average_score" in data
    assert "min_score" in data
    assert "max_score" in data
    assert "by_label" in data
    assert isinstance(data["by_label"], dict)

if __name__ == "__main__":
    # Run tests manually
    print("Testing database functionality...")
    test_scan_saved_to_database()
    print("✅ Scan saved to database test passed")
    
    test_stats_returns_real_data()
    print("✅ Stats returns real data test passed")
    
    print("\nAll tests passed! 🎉")
