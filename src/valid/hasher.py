# Creates video signatures to find same content.

# Grabbing sample frames from the video files.
# Uses perceptual hashing to compare visual content.
# Flags files as same content if hash distance is near zero.

# This module extracts a frame from the middle of the video and generates a visual fingerprint (pHash) to track matching content regardless of resolution changes.

import cv2
import imagehash
from PIL import Image

def generate_video_hash(video_path: str) -> str | None:
    """Generates a perceptual hash from the middle frame of a video."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    middle_frame_idx = total_frames // 2
    
    # Jump directly to the middle frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame_idx)
    success, frame = cap.read()
    cap.release()
    
    if not success or frame is None:
        return None
        
    # Convert OpenCV BGR frame to PIL RGB Image
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_frame)
    
    # Generate perceptual hash (resilient to scale/compression changes)
    return str(imagehash.phash(pil_img))

def check_content_match(hash1: str, hash2: str, max_distance: int = 4) -> bool:
    """Compares two hashes. If Hamming distance is low, content is identical."""
    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)
    return (h1 - h2) <= max_distance
