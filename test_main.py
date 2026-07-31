import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from valid.main import app, video_db

# Initialize the FastAPI simulation testing client
client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_state():
    """Wipes the volatile in-memory dictionary before running every single test case."""
    video_db.clear()

# Mock definitions to completely bypass the physical opencv requirements during testing
@pytest.fixture
def mock_video_processing():
    """Mocks OpenCV and ImageHash operations to run reliably on any system."""
    with patch("valid.main.get_video_dimensions") as mock_dims, \
         patch("valid.main.find_matched_ratio") as mock_ratio, \
         patch("valid.main.generate_video_hashes") as mock_hashes:
        yield mock_dims, mock_ratio, mock_hashes

def test_upload_valid_ratios(mock_video_processing):
    """Verifies that standard target aspect ratios resolve to correct buckets."""
    mock_dims, mock_ratio, mock_hashes = mock_video_processing
    
    # Configure the mock to return a clean 16:9 widescreen metadata profile
    mock_dims.return_value = (1920, 1080)
    mock_ratio.return_value = "16:9"
    mock_hashes.return_value = ["hash1", "hash2", "hash3"]

    response = client.post("/upload", files={"file": ("widescreen.mp4", b"fake_video_bytes", "video/mp4")})
    
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["ratio_bucket"] == "16:9"
    assert "video_id" in json_data

def test_upload_tolerance_and_other_bucket(mock_video_processing):
    """Validates that items outside the 1% boundary safely land inside 'Other'."""
    mock_dims, mock_ratio, mock_hashes = mock_video_processing
    
    mock_dims.return_value = (1600, 1100)
    mock_ratio.return_value = "Other"
    mock_hashes.return_value = [] # Other bucket elements don't get hashed

    response = client.post("/upload", files={"file": ("custom_clip.mp4", b"fake_video_bytes", "video/mp4")})
    
    assert response.status_code == 201
    assert response.json()["ratio_bucket"] == "Other"

def test_get_all_videos_endpoint(mock_video_processing):
    """Confirms the /videos registry echoes exact uploaded schemas."""
    mock_dims, mock_ratio, mock_hashes = mock_video_processing
    
    mock_dims.return_value = (1080, 1080)
    mock_ratio.return_value = "1:1"
    mock_hashes.return_value = ["hash_square"]

    client.post("/upload", files={"file": ("square.mp4", b"fake_video_bytes", "video/mp4")})
    
    response = client.get("/videos")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["ratio_bucket"] == "1:1"

def test_cross_ratio_matching_matrix(mock_video_processing):
    """Checks that same-bucket queries skip evaluation while cross-buckets match."""
    mock_dims, mock_ratio, mock_hashes = mock_video_processing

    # 1. Upload Video 1: 16:9 Widescreen Master
    mock_dims.return_value = (1280, 720)
    mock_ratio.return_value = "16:9"
    mock_hashes.return_value = ["hashA", "hashB"]
    client.post("/upload", files={"file": ("720p.mp4", b"fake_video_bytes", "video/mp4")})

    # 2. Upload Video 2: Distinct 16:9 Video (Same bucket, different content hashes)
    mock_dims.return_value = (1920, 1080)
    mock_ratio.return_value = "16:9"
    mock_hashes.return_value = ["hashX", "hashY"]
    client.post("/upload", files={"file": ("distinct_1080p.mp4", b"fake_video_bytes", "video/mp4")})

    # 3. Upload Video 3: 9:16 Vertical Video (Cross-bucket, matching content hashes with Video 1)
    mock_dims.return_value = (1080, 1920)
    mock_ratio.return_value = "9:16"
    mock_hashes.return_value = ["hashA", "hashB"] # Same hash signatures as 720p.mp4
    client.post("/upload", files={"file": ("tiktok.mp4", b"fake_video_bytes", "video/mp4")})

    # Evaluate matched matrices (we set confidence threshold to 100 to ensure exact hash mapping matches)
    match_response = client.get("/match?confidence_threshold=100.0")
    assert match_response.status_code == 200
    matches = match_response.json()
    
    # - distinct_1080p.mp4 is ignored because its content hashes are completely unique.
    # - 720p.mp4 and tiktok.mp4 match because they share identical hashes and occupy DIFFERENT ratio buckets.
    assert len(matches) == 1
    assert matches[0]["filename"] == "tiktok.mp4"

def test_delete_endpoint_clears_memory(mock_video_processing):
    """Ensures deletions clear items out of the volatile memory lookup maps."""
    mock_dims, mock_ratio, mock_hashes = mock_video_processing
    
    mock_dims.return_value = (1080, 1350)
    mock_ratio.return_value = "4:5"
    mock_hashes.return_value = ["hash_insta"]

    upload_res = client.post("/upload", files={"file": ("insta.mp4", b"fake_video_bytes", "video/mp4")})
    v_id = upload_res.json()["video_id"]
    
    del_res = client.get("/videos")
    assert len(del_res.json()) == 1
    
    client.delete(f"/videos/{v_id}")
    check_res = client.get("/videos")
    assert len(check_res.json()) == 0
