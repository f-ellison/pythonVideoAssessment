# Checks video sizes and finds the matching ratio.

# Gets video width and height using OpenCV.
# Divides width by height to find the current ratio.
# Compares the result to target ratios (9:16 = 0.5625, 1:1 = 1.0, 4:5 = 0.8, 16:9 = 1.7778).
# Applies a 1% tolerance range (0.99 to 1.01 multiplier) to match the correct ratio.
