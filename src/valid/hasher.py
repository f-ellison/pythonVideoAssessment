# Creates video signatures to find same content.

# Grabbing sample frames from the video files.
# Uses perceptual hashing to compare visual content.
# Flags files as same content if hash distance is near zero.

# This module extracts a frame from the middle of the video and generates a visual fingerprint (pHash) to track matching content regardless of resolution changes.

import cv2
import imagehash
from PIL import Image

def normalize_and_equalize_frame(cv2_frame, target_size=256) -> Image.Image:
    gray_frame = cv2.cvtColor(cv2_frame, cv2.COLOR_BGR2GRAY)
    equalized_gray = cv2.equalizeHist(gray_frame)
    pil_img = Image.fromarray(equalized_gray)
    
    pil_img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
    background = Image.new('L', (target_size, target_size), 0)
    offset = ((target_size - pil_img.width) // 2, (target_size - pil_img.height) // 2)
    background.paste(pil_img, offset)
    return background

def generate_video_hashes(video_path: str, sample_interval_seconds: float = 2.0, max_samples: int = 5) -> list[str]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0 or total_frames <= 0:
        cap.release()
        return []

    hashes = []
    for i in range(max_samples):
        target_frame = int((i + 1) * sample_interval_seconds * fps)
        if target_frame >= total_frames:
            break
            
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        success, frame = cap.read()
        if success and frame is not None:
            normalized_img = normalize_and_equalize_frame(frame)
            hashes.append(str(imagehash.average_hash(normalized_img)))
            
    cap.release()
    return hashes

def calculate_match_confidence(hashes1: list[str], hashes2: list[str]) -> float:
    compare_limit = min(len(hashes1), len(hashes2))
    if compare_limit == 0:
        return 0.0
        
    total_bits, total_distance = 0, 0
    for idx in range(compare_limit):
        h1 = imagehash.hex_to_hash(hashes1[idx])
        h2 = imagehash.hex_to_hash(hashes2[idx])
        total_bits += len(h1.hash.flatten())
        total_distance += (h1 - h2)
        
    return round((1.0 - (total_distance / total_bits)) * 100, 1) if total_bits > 0 else 0.0
