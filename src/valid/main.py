# Takes a folder path from the user.
# Loops through each video file.
# Prints out the file name, exact ratio, matched format, and content match status.

# The orchestration script that indexes videos in a directory, extracts details, and flags duplicate content.

import os
from pathlib import Path
from detector import get_video_dimensions, find_matched_ratio
from hasher import generate_video_hash, check_content_match

VALID_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}

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

    print("\n🔍 --- Phase 1: Analyzing Aspect Ratios ---")
    for vid in video_files:
        try:
            w, h = get_video_dimensions(str(vid))
            ratio_label = find_matched_ratio(w, h, tolerance=0.01)
            v_hash = generate_video_hash(str(vid))
            
            video_data = {
                "name": vid.name,
                "path": str(vid),
                "resolution": f"{w}x{h}",
                "ratio": ratio_label,
                "hash": v_hash
            }
            processed_videos.append(video_data)
            print(f"🎬 {video_data['name']} -> {video_data['resolution']} | Matched: {video_data['ratio']}")
        except Exception as e:
            print(f"❌ Failed to process {vid.name}: {e}")

    print("\n👁️  --- Phase 2: Detecting Same Content ---")
    duplicated_groups = {}
    already_matched = set()

    for i, vid1 in enumerate(processed_videos):
        if vid1['path'] in already_matched or not vid1['hash']:
            continue
            
        group = [vid1['name']]
        
        for j, vid2 in enumerate(processed_videos):
            if i == j or vid2['path'] in already_matched or not vid2['hash']:
                continue
                
            if check_content_match(vid1['hash'], vid2['hash']):
                group.append(vid2['name'])
                already_matched.add(vid2['path'])
                
        if len(group) > 1:
            duplicated_groups[vid1['name']] = group
            already_matched.add(vid1['path'])

    if duplicated_groups:
        for root, matches in duplicated_groups.items():
            print(f"⚠️  Same Content Found across different clips:")
            for match in matches:
                print(f"   - {match}")
    else:
        print("✅ No duplicate video content detected.")

if __name__ == "__main__":
    # Change this to your local video folder path
    target_folder = input("Enter the path to your video folder: ").strip()
    analyze_directory(target_folder)
