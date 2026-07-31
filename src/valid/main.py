# Takes a folder path from the user.
# Loops through each video file.
# Prints out the file name, exact ratio, matched format, and content match status.

# The orchestration script that indexes videos in a directory, extracts details, and flags duplicate content.

import os
from pathlib import Path
from detector import get_video_dimensions, find_matched_ratio
from hasher import generate_video_hashes, calculate_match_confidence

VALID_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
# Set the minimum confidence threshold to report a valid duplicate group
CONFIDENCE_THRESHOLD = 75.0 

def analyze_directory(directory_path: str):
    dir_path = Path(directory_path)
    if not dir_path.is_dir():
        print(f"Error: {directory_path} is not a valid directory.")
        return

    video_files = [p for p in dir_path.iterdir() if p.suffix.lower() in VALID_EXTENSIONS]
    
    if not video_files:
        print("No supported video files found.")
        return

    processed_videos = []

    print("\n🔍 --- Phase 1: Fingerprinting Videos & Ratios ---")
    for vid in video_files:
        try:
            w, h = get_video_dimensions(str(vid))
            ratio_label = find_matched_ratio(w, h, tolerance=0.01)
            v_hashes = generate_video_hashes(str(vid))
            
            video_data = {
                "name": vid.name,
                "path": str(vid),
                "resolution": f"{w}x{h}",
                "ratio": ratio_label,
                "hashes": v_hashes
            }
            processed_videos.append(video_data)
            print(f"🎬 Processed: {video_data['name']} [{video_data['ratio']}]")
        except Exception as e:
            print(f"❌ Failed to process {vid.name}: {e}")

    print("\n👁️  --- Phase 2: Duplicate Content Matrix ---")
    
    already_grouped = set()
    
    for i, vid1 in enumerate(processed_videos):
        if vid1['path'] in already_grouped:
            continue
            
        matches = []
        
        for j, vid2 in enumerate(processed_videos):
            if i == j:
                continue
                
            confidence = calculate_match_confidence(vid1['hashes'], vid2['hashes'])
            
            if confidence >= CONFIDENCE_THRESHOLD:
                matches.append((vid2['name'], vid2['path'], confidence))
                
        if matches:
            print(f"\n⚠️  Matches detected for master asset: {vid1['name']} ({vid1['ratio']})")
            print(f"   - [Source Master Artifact]")
            for match_name, match_path, score in matches:
                print(f"   - Match: {match_name} | Match Confidence: {score}%")
                already_grouped.add(match_path)
            already_grouped.add(vid1['path'])

    if not already_grouped:
        print("✅ No matching cross-format duplicates found at or above the threshold.")

if __name__ == "__main__":
    target_folder = input("Enter the path to your video folder: ").strip()
    analyze_directory(target_folder)
