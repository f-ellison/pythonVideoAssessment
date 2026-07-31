# pythonVideoAssessment
Assessment project using python code that will have the following functionality:
# Video Aspect-Ratio Finder 
Processes MP4s into the canonical aspect rations 9:16, 1:1, 4:5, 16:9
With ± 1% tolerance; non-conforming videos are excluded as other
# Same-Content Detector
Detects which videos are the same underlying creative across aspect ratios



Sample videos are served from a private GCS bucket via short-lived server-side V4 signed URLs. The match logic here is a deterministic filename-stem heuristic that reproduces the groupings a correct perceptual matcher would produce on this set.
