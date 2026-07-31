# Takes a folder path from the user.
# Loops through each video file.
# Prints out the file name, exact ratio, matched format, and content match status.

# The orchestration script that indexes videos in a directory, extracts details, and flags duplicate content.

import os
import shutil
from pathlib import Path
from detector import get_video_dimensions, find_matched_ratio
from hasher import generate_video_hashes, calculate_match_confidence

VALID_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
CONFIDENCE_THRESHOLD = 60.0 

def analyze_and_sort_directory(directory_path: str):
    dir_path = Path(directory_path)
    if not dir_path.is_dir():
        print(f"Error: {directory_path} is not a valid directory.")
        return

    # Create target folders for sorting execution
    allowed_buckets = ["9-16", "4-5", "1-1", "16-9", "Other"]
    bucket_dirs = {}
    for b in allowed_buckets:
        folder = dir_path / b
        folder.mkdir(exist_ok=True)
        bucket_dirs[b.replace("-", ":")] = folder

    video_files = [p for p in dir_path.iterdir() if p.suffix.lower() in VALID_EXTENSIONS]
    if not video_files:
        print("No supported video files found.")
        return

    processed_videos = []

    print("\n🔍 --- Phase 1: Categorizing and Fingerprinting ---")
    for vid in video_files:
        try:
            w, h = get_video_dimensions(str(vid))
            ratio_bucket = find_matched_ratio(w, h, tolerance=0.01)
            
            # Skip visual hashing for 'Other' items to optimize speed
            v_hashes = generate_video_hashes(str(vid)) if ratio_bucket != "Other" else []
            
            video_data = {
                "original_name": vid.name,
                "current_path": vid,
                "ratio_bucket": ratio_bucket,
                "hashes": v_hashes
            }
            processed_videos.append(video_data)
            print(f"🎬 Read: {vid.name} -> Bucket Assigned: [{ratio_bucket}]")
        except Exception as e:
            print(f"❌ Failed to parse {vid.name}: {e}")

    print("\n👁️  --- Phase 2: Cross-Ratio Duplicate Detection ---")
    already_matched = set()
    
    for i, vid1 in enumerate(processed_videos):
        # Rule: Completely ignore "Other" videos during layout evaluation matching loops
        if vid1['ratio_bucket'] == "Other" or vid1['original_name'] in already_matched:
            continue
            
        matches = []
        for j, vid2 in enumerate(processed_videos):
            if i == j or vid2['ratio_bucket'] == "Other" or vid2['original_name'] in already_matched:
                continue
                
            # Rule: Skip matching calculations if videos belong to the exact same aspect ratio bucket
            if vid1['ratio_bucket'] == vid2['ratio_bucket']:
                continue
                
            confidence = calculate_match_confidence(vid1['hashes'], vid2['hashes'])
            if confidence >= CONFIDENCE_THRESHOLD:
                matches.append((vid2['original_name'], vid2['ratio_bucket'], confidence))
                already_matched.add(vid2['original_name'])
                
        if matches:
            print(f"\n⚠️  Cross-Format Content Identified for: {vid1['original_name']} ({vid1['ratio_bucket']})")
            for name, ratio, score in matches:
                print(f"   -> Found Variant: {name} ({ratio}) | Match Score: {score}%")
            already_matched.add(vid1['original_name'])

    print("\n📦 --- Phase 3: Moving Files to Target Subdirectories ---")
    for vid in processed_videos:
        target_dir = bucket_dirs[vid['ratio_bucket']]
        destination = target_dir / vid['original_name']
        
        try:
            shutil.move(str(vid['current_path']), str(destination))
            print(f"🚚 Moved {vid['original_name']} ➡️  {vid['ratio_bucket']}/")
        except Exception as e:
            print(f"❌ Failed to move {vid['original_name']}: {e}")

    print("\n✅ Processing, indexing, cross-matching, and file sorting tasks complete.")

if __name__ == "__main__":
    target_folder = input("Enter the path to your video folder: ").strip()
    analyze_and_sort_directory(target_folder)
