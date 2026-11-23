# --- PATHS [Adjust locally] ---
# Path to the `uporedna_tabela` file downloaded as CSV
INPUT_CSV = ""

# Path to the local (Google Drive) folder with the videos
LOCAL_VIDEO_FOLDER = ""

# Single video check: local path to the video and the YouTube URL to compare it with
SINGLE_LOCAL_VIDEO = ""
SINGLE_YOUTUBE_URL = "https://www.youtube.com/"

# --- OUTPUT ---
OUTPUT_CSV = "comparison_results.csv"
# Generated only if the first pass detects mismatches (second, confirming pass)
MISMATCH_OUTPUT_CSV = "comparison_results_after_mismatch.csv"
FAILED_FRAMES_DIR = "failed_frames"

# --- FINGERPRINTING ---
# Sample frames at 10%, 30%, 50%, 70%, and 90% marks
SAMPLE_POINTS = [0.1, 0.3, 0.5, 0.7, 0.9]
# Frames are taken this many seconds before and after each sample point
FRAME_OFFSET_SECONDS = 0.4
# Used if OpenCV can't read the FPS
FALLBACK_FPS = 30
YOUTUBE_FORMAT = "best[height<=480]/best"

# --- COMPARISON ---
VISUAL_THRESHOLD = 8
# Allows a tiny fraction of a second difference due to YouTube re-encoding
DURATION_TOLERANCE = 1.5
