import pytest
from fastapi.testclient import TestClient
from valid.main import app, video_db

# Initialize the FastAPI visual simulation testing client
client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_state():
    """Wipes the volatile in-memory dictionary before running every single test case."""
    video_db.clear()

def create_mock_video_bytes(width: int, height: int, unique_marker: str = "A") -> bytes:
    """Generates an ultra-light raw AVI video stream using universally supported codecs."""
    import cv2
    import numpy as np
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(suffix=".avi", delete=False) as tmp:
        tmp_path = tmp.name

    # FIX: Use 'MJPG' (Motion JPEG) instead of 'XVID'
    # This guarantees the codec initiates cleanly on headless Linux servers without extra setup
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(tmp_path, fourcc, 10.0, (width, height))
    
    if not out.isOpened():
        # Fallback to an entirely raw uncompressed structure if the OS environment is strictly locked down
        fourcc_fallback = 0 
        out = cv2.VideoWriter(tmp_path, fourcc_fallback, 10.0, (width, height))
    
    for i in range(10):
        # Create background matrix canvas
        frame = np.ones((height, width, 3), dtype=np.uint8) * 128
        
        # Stamp visual tracking context directly onto the frame matrix array
        cv2.putText(
            frame, 
            f"Asset-{unique_marker}-{i}", 
            (width // 4, height // 2), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.0, 
            (0, 0, 0), 
            2
        )
        out.write(frame)
    out.release()

    # Read binary back to the test application memory context and clean up disk artifacts
    video_bytes = Path(tmp_path).read_bytes()
    try:
        Path(tmp_path).unlink()
    except Exception:
        pass
        
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
    # Generate unique visual contents for unrelated videos
    v1_bytes = create_mock_video_bytes(1280, 720, unique_marker="MASTER_V1")   # 16:9 Master
    v2_bytes = create_mock_video_bytes(1920, 1080, unique_marker="DIFFERENT_V2") # 16:9 Distinct Video (Same bucket!)
    
    # Crop simulation: Use the exact same visual content marker ("MASTER_V1") for the 9:16 variation!
    v3_bytes = create_mock_video_bytes(1080, 1920, unique_marker="MASTER_V1")   # 9:16 Cross-Format Cut Variant
    
    # Upload everything to tracking arrays
    client.post("/upload", files={"file": ("720p.mp4", v1_bytes, "video/mp4")})
    client.post("/upload", files={"file": ("distinct_1080p.mp4", v2_bytes, "video/mp4")})
    client.post("/upload", files={"file": ("tiktok.mp4", v3_bytes, "video/mp4")})
    
    # Evaluate matched matrices
    match_response = client.get("/match?confidence_threshold=50.0")
    assert match_response.status_code == 200
    matches = match_response.json()
    
    # distinct_1080p.mp4 will be completely ignored because its visual hash is completely unique.
    # tiktok.mp4 will match 720p.mp4 because their contents share the same visual stamp, and they cross buckets!
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
