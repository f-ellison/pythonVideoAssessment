# Checks video sizes and finds the matching ratio.

# Gets video width and height using OpenCV.
# Divides width by height to find the current ratio.
# Compares the result to target ratios (9:16 = 0.5625, 1:1 = 1.0, 4:5 = 0.8, 16:9 = 1.7778).
# Applies a 1% tolerance range (0.99 to 1.01 multiplier) to match the correct ratio.

# This module extracts video metadata and identifies the aspect ratio within a 1% tolerance window.

import cv2

# Permitted target ratios
TARGET_RATIOS = {
    "9:16": 9 / 16,  # 0.5625
    "4:5": 4 / 5,    # 0.8000
    "1:1": 1.0 / 1.0, # 1.0000
    "16:9": 16 / 9   # 1.7778
}

def get_video_dimensions(video_path: str) -> tuple[int, int]:
    """Extracts width and height of a video file."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not decode video stream.")
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height

def find_matched_ratio(width: int, height: int, tolerance: float = 0.01) -> str:
    if height == 0:
        return "Other"
    actual_ratio = width / height
    for label, target_val in TARGET_RATIOS.items():
        if (target_val * (1.0 - tolerance)) <= actual_ratio <= (target_val * (1.0 + tolerance)):
            return label
    return "Other"
