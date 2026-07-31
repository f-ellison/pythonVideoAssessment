import pytest
from fastapi.testclient import TestClient
from valid.main import app, video_db

# Initialize the FastAPI visual simulation testing client
client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_state():
    """Wipes the volatile in-memory dictionary before running every single test case."""
    video_db.clear()

def create_mock_video_bytes(width: int, height: int) -> bytes:
    """Generates an ultra-light, uncompressed raw AVI video stream directly in RAM."""
    import cv2
    import numpy as np
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(suffix=".avi", delete=False) as tmp:
        tmp_path = tmp.name

    # Create a simple 10-frame empty colored frame sequence block
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(tmp_path, fourcc, 10.0, (width, height))
    
    for _ in range(10):
        # Draw a solid mock gray block matrix canvas
        frame = np.ones((height, width, 3), dtype=np.uint8) * 128
        out.write(frame)
    out.release()

    # Stream out the raw bytes and clean up the temporary disk track immediately
    video_bytes = Path(tmp_path).read_bytes()
    Path(tmp_path).unlink()
    return video_bytes

def test_upload_valid_ratios():
    """Verifies that standard target aspect ratios resolve to correct buckets."""
    # Test a precise 16:9 widescreen canvas (1920x1080)
    video_data = create_mock_video_bytes(1920, 1080)
    response = client.post("/upload", files={"file": ("widescreen.mp4", video_data, "video/mp4")})
    
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["ratio_bucket"] == "16:9"
    assert "video_id" in json_data

def test_upload_tolerance_and_other_bucket():
    """Validates that items outside the 1% boundary safely land inside 'Other'."""
    # Test a custom 16:11 odd canvas resolution (1600x1100) -> 1.45 ratio
    video_data = create_mock_video_bytes(1600, 1100)
    response = client.post("/upload", files={"file": ("custom_clip.mp4", video_data, "video/mp4")})
    
    assert response.status_code == 201
    assert response.json()["ratio_bucket"] == "Other"

def test_get_all_videos_endpoint():
    """Confirms the /videos registry echoes exact uploaded schemas."""
    video_data = create_mock_video_bytes(1080, 1080) # 1:1 Canvas
    client.post("/upload", files={"file": ("square.mp4", video_data, "video/mp4")})
    
    response = client.get("/videos")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["ratio_bucket"] == "1:1"

def test_cross_ratio_matching_matrix():
    """Checks that same-bucket queries skip evaluation while cross-buckets match."""
    # Generate identical visual canvas arrays
    v1_bytes = create_mock_video_bytes(1280, 720)   # 16:9 Master
    v2_bytes = create_mock_video_bytes(1920, 1080)  # 16:9 Duplicate (Same bucket!)
    v3_bytes = create_mock_video_bytes(1080, 1920)  # 9:16 Cross-Format Cut Variant
    
    # Upload everything to tracking arrays
    client.post("/upload", files={"file": ("720p.mp4", v1_bytes, "video/mp4")})
    client.post("/upload", files={"file": ("1080p.mp4", v2_bytes, "video/mp4")})
    client.post("/upload", files={"file": ("tiktok.mp4", v3_bytes, "video/mp4")})
    
    # Evaluate matched matrices
    match_response = client.get("/match?confidence_threshold=50.0")
    assert match_response.status_code == 200
    matches = match_response.json()
    
    # 720p and 1080p are both 16:9, so they must NOT trigger a match. 
    # Only the tiktok.mp4 (9:16) should flag a cross-ratio layout match.
    assert len(matches) == 1
    assert matches[0]["filename"] == "tiktok.mp4"

def test_delete_endpoint_clears_memory():
    """Ensures deletions clear items out of the volatile memory lookup maps."""
    video_data = create_mock_video_bytes(1080, 1350) # 4:5 Portrait
    upload_res = client.post("/upload", files={"file": ("insta.mp4", video_data, "video/mp4")})
    v_id = upload_res.json()["video_id"]
    
    # Fire removal query
    del_res = client.get("/videos")
    assert len(del_res.json()) == 1
    
    client.delete(f"/videos/{v_id}")
    check_res = client.get("/videos")
    assert len(check_res.json()) == 0
