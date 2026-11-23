import cv2
import imagehash
from PIL import Image

from .config import FALLBACK_FPS, FRAME_OFFSET_SECONDS, SAMPLE_POINTS
from .sources.youtube import get_youtube_duration, get_youtube_stream_url


def get_video_fingerprint(video_path_or_url, is_youtube=False):
    """
    Returns a tuple: (fingerprint_clusters, duration_in_seconds, frames_clusters)
    """
    duration = 0.0

    if is_youtube:
        try:
            duration = get_youtube_duration(video_path_or_url)
            cap = cv2.VideoCapture(get_youtube_stream_url(video_path_or_url))
        except Exception as e:
            print(f"Error fetching YouTube stream/duration: {e}")
            return None, 0.0, None
    else:
        cap = cv2.VideoCapture(video_path_or_url)
        # Calculate duration for local file based on frames and FPS
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames_local = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if fps > 0:
            duration = total_frames_local / fps

    if not cap.isOpened():
        return None, 0.0, None

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = FALLBACK_FPS
    # Get total frames for frame extraction
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        cap.release()
        return None, duration, None

    frame_offset = int(fps * FRAME_OFFSET_SECONDS)

    fingerprint_clusters = []
    frames_clusters = []

    for point in SAMPLE_POINTS:
        base_frame_idx = int(total_frames * point)

        point_hashes = []
        point_frames = []

        for offset in [-frame_offset, 0, frame_offset]:
            # Make sure we don't accidentally ask for a negative frame or go past the end
            idx = max(0, min(total_frames - 1, base_frame_idx + offset))
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()

            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                phash = imagehash.phash(pil_img)

                point_hashes.append(phash)
                point_frames.append(rgb_frame)

        # Save the cluster of 3 to our main lists
        fingerprint_clusters.append(point_hashes)
        frames_clusters.append(point_frames)

    cap.release()
    return fingerprint_clusters, duration, frames_clusters
