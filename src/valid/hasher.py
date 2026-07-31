# Creates video signatures to find same content.

# Grabbing sample frames from the video files.
# Uses perceptual hashing to compare visual content.
# Flags files as same content if hash distance is near zero.

# This module extracts a frame from the middle of the video and generates a visual fingerprint (pHash) to track matching content regardless of resolution changes.

import cv2
import imagehash
from PIL import Image, ImageOps

def square_normalize_frame(cv2_frame, target_size=256) -> Image.Image:
    """Converts a frame to a padded square to eliminate aspect ratio bias."""
    rgb_frame = cv2.cvtColor(cv2_frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_frame)
    
    # Resize and pad with black bars so layout changes don't destroy the hash
    pil_img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
    
    # Create background square canvas
    background = Image.new('RGB', (target_size, target_size), (0, 0, 0))
    offset = ((target_size - pil_img.width) // 2, (target_size - pil_img.height) // 2)
    background.paste(pil_img, offset)
    
    return background

def generate_video_hashes(video_path: str, num_samples: int = 3) -> list[str]:
    """Extracts padded frames across the timeline to create a robust fingerprint."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        cap.release()
        return []

    hashes = []
    # Sample evenly across the video (e.g., 25%, 50%, 75% marks)
    intervals = [int(total_frames * (i / (num_samples + 1))) for i in range(1, num_samples + 1)]

    for frame_idx in intervals:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = cap.read()
        if success and frame is not None:
            normalized_img = square_normalize_frame(frame)
            # Use dHash (Difference Hash) which tracks gradients better over resolution changes
            v_hash = str(imagehash.dhash(normalized_img))
            hashes.append(v_hash)
            
    cap.release()
    return hashes

def calculate_match_confidence(hashes1: list[str], hashes2: list[str]) -> float:
    """Computes similarity percentage based on overall bit distance."""
    if not hashes1 or not hashes2:
        return 0.0
        
    total_bits = 0
    total_distance = 0
    
    # Compare each corresponding sampled section
    for h1_str, h2_str in zip(hashes1, hashes2):
        h1 = imagehash.hex_to_hash(h1_str)
        h2 = imagehash.hex_to_hash(h2_str)
        
        # Max bit length for standard imagehash hashes is usually 64 bits
        bit_length = len(h1.hash.flatten()) 
        distance = h1 - h2
        
        total_bits += bit_length
        total_distance += distance
        
    if total_bits == 0:
        return 0.0
        
    # Translate bit variation into a readable confidence metric
    confidence = (1.0 - (total_distance / total_bits)) * 100
    return round(confidence, 1)
