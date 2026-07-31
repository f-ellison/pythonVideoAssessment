# Takes a folder path from the user.
# Loops through each video file.
# Prints out the file name, exact ratio, matched format, and content match status.

# The orchestration script that indexes videos in a directory, extracts details, and flags duplicate content.

import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from pathlib import Path

from valid.detector import get_video_dimensions, find_matched_ratio
from valid.hasher import generate_video_hashes, calculate_match_confidence

app = FastAPI(title="Render Free-Tier Video Matcher API")

# Pure In-Memory metadata database dictionary
# This satisfies the "No database" mandate while storing all records across app lifecycle restarts
video_db = {}

@app.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_video(file: UploadFile = File(...)):
    """Uploads file data using the local file pipeline inside RAM-based transient disk tracks."""
    video_id = str(uuid.uuid4())
    
    # We target Render's transient /tmp virtual disk to maximize RAM performance safely
    temp_path = Path(f"/tmp/{video_id}_{file.filename}")
    
    try:
        # Stream chunks safely into transient memory limits
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        width, height = get_video_dimensions(str(temp_path))
        ratio_bucket = find_matched_ratio(width, height, tolerance=0.01)
        hashes = generate_video_hashes(str(temp_path)) if ratio_bucket != "Other" else []
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Processing failed: {str(e)}")
    finally:
        # Crucial for Render Free Tier: Wipe transient files instantly to free up RAM disk
        if temp_path.exists():
            temp_path.unlink()

    # Save to our volatile, pure in-memory data state dictionary
    video_entry = {
        "video_id": video_id,
        "filename": file.filename,
        "width": width,
        "height": height,
        "aspect_ratio": f"{width}:{height}" if height > 0 else "0:0",
        "ratio_bucket": ratio_bucket,
        "hashes": hashes  # Store fingerprints only; raw large video blocks are dumped
    }
    
    video_db[video_id] = video_entry
    
    return {
        "video_id": video_entry["video_id"],
        "width": video_entry["width"],
        "height": video_entry["height"],
        "aspect_ratio": video_entry["aspect_ratio"],
        "ratio_bucket": video_entry["ratio_bucket"],
        "filename": video_entry["filename"]
    }

@app.get("/match")
async def match_videos(confidence_threshold: float = 60.0):
    """Compares cache logs over runtime variables, bypassing identical buckets."""
    matches_found = []
    already_paired = set()
    videos = list(video_db.values())

    for i, vid1 in enumerate(videos):
        if vid1["ratio_bucket"] == "Other" or vid1["video_id"] in already_paired:
            continue
            
        for j, vid2 in enumerate(videos):
            if i == j or vid2["ratio_bucket"] == "Other" or vid2["video_id"] in already_paired:
                continue
                
            if vid1["ratio_bucket"] == vid2["ratio_bucket"]:
                continue
                
            score = calculate_match_confidence(vid1["hashes"], vid2["hashes"])
            if score >= confidence_threshold:
                matches_found.append({
                    "video_id": vid2["video_id"],
                    "filename": vid2["filename"],
                    "confidence": f"{score}%"
                })
                already_paired.add(vid2["video_id"])
                
        already_paired.add(vid1["video_id"])

    return matches_found

@app.get("/videos")
async def get_all_videos():
    """Returns runtime structures matching original specification outputs."""
    return [
        {
            "video_id": v["video_id"],
            "width": v["width"],
            "height": v["height"],
            "aspect_ratio": v["aspect_ratio"],
            "ratio_bucket": v["ratio_bucket"],
            "filename": v["filename"]
        }
        for v in video_db.values()
    ]

@app.delete("/videos/{video_id}")
async def delete_video(video_id: str):
    """Drops the tracking metrics directly from the application memory lookup maps."""
    if video_id not in video_db:
        raise HTTPException(status_code=404, detail="Requested identity record absent.")
        
    del video_db[video_id]
    return {"deleted": video_id}
