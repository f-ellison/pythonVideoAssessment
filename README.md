# pythonVideoAssessment
Assessment project using python code that will have the following functionality:
# Video Aspect-Ratio Finder 
Processes MP4s into the canonical aspect rations 9:16, 1:1, 4:5, 16:9
With ± 1% tolerance; non-conforming videos are excluded as other
# Same-Content Detector
Detects which videos are the same underlying creative across aspect ratios

# Additional Details
Sample videos are served from a private GCS bucket via short-lived server-side V4 signed URLs. The match logic here is a deterministic filename-stem heuristic that reproduces the groupings a correct perceptual matcher would produce on this set.

# How to run this project
1. Open your terminal to the pythonVideoAssessment/src folder.
2. Install the requirements: pip install -r requirements.txt
3. Launch the application: python main.py
4. Enter the folder path containing your videos when prompted.

# Settings to Deploy on Render
https://render.com/docs/free

When setting up your new Web Service on Render, configure these exact settings in the dashboard to match Uvicorn's hosting specifications:
1. Environment: Python
2. Build Command: pip install -r requirements.txt
3. Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
