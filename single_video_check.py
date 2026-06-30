import cv2
import imagehash
from PIL import Image
import subprocess
import os


def get_video_fingerprint(video_path_or_url, is_youtube=False):
    """
    Returns a tuple: (fingerprint_list, duration_in_seconds)
    """
    duration = 0.0

    if is_youtube:
        try:
            # 1. Fetch exact duration from YouTube using yt-dlp first
            dur_cmd = ['yt-dlp', '--no-check-certificates', '--js-runtimes', 'node', '--print', 'duration', video_path_or_url]
            dur_output = subprocess.check_output(dur_cmd, text=True).strip()
            duration = float(dur_output) if dur_output else 0.0

            # 2. Get the stream URL
            ydl_cmd = ['yt-dlp', '--no-check-certificates', '--js-runtimes', 'node', '-g', '-f', 'best[height<=480]/best',
                       video_path_or_url]
            stream_url = subprocess.check_output(ydl_cmd, text=True).strip()
            cap = cv2.VideoCapture(stream_url)
        except Exception as e:
            print(f"Error fetching YouTube stream/duration: {e}")
            return None, 0.0
    else:
        cap = cv2.VideoCapture(video_path_or_url)
        # Calculate duration for local file based on frames and FPS
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames_local = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if fps > 0:
            duration = total_frames_local / fps

    if not cap.isOpened():
        return None, 0.0

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 30  # Fallback if OpenCV can't read the FPS
    # Get total frames for frame extraction
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        return None, duration

    frame_offset = int(fps * 0.4)

    # Sample frames at 10%, 30%, 50%, 70%, and 90% marks
    sample_points = [0.1, 0.3, 0.5, 0.7, 0.9]

    fingerprint_clusters = []
    frames_clusters = []

    for point in sample_points:
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


def compare_videos(data1, data2, video_name, visual_threshold=8, duration_tolerance=1.5):
    """
    Compares two videos based on their duration and visual fingerprints.
    'duration_tolerance' allows a tiny fraction of a second difference due to YouTube re-encoding.
    """
    fp1, dur1, frames1 = data1
    fp2, dur2, frames2 = data2

    if not fp1 or not fp2 or len(fp1) != len(fp2):
        return False, "Failed to extract fingerprints properly."

    # --- STEP 1: DURATION CHECK ---
    duration_diff = abs(dur1 - dur2)
    if duration_diff > duration_tolerance:
        return False, f"Duration mismatch: {dur1:.2f}s vs {dur2:.2f}s (Diff: {duration_diff:.2f}s)"

    # --- STEP 2: VISUAL FINGERPRINT CHECK ---
    for i, (cluster1, cluster2) in enumerate(zip(fp1, fp2)):

        best_distance = 100  # Start with a huge failing distance
        best_pair_indices = (0, 0)

        # Check every frame in Local's burst against every frame in YouTube's burst
        for j, hash1 in enumerate(cluster1):
            for k, hash2 in enumerate(cluster2):
                distance = hash1 - hash2

                # If we find a closer match, remember it!
                if distance < best_distance:
                    best_distance = distance
                    best_pair_indices = (j, k)

        # If the absolute BEST match in that 0.8-second window still fails...
        if best_distance > visual_threshold:
            fail_dir = "failed_frames"
            os.makedirs(fail_dir, exist_ok=True)

            idx1, idx2 = best_pair_indices

            # Save the closest frames it could find
            cv2.imwrite(f"{fail_dir}/{video_name}_fail_point_{i}_LOCAL.jpg",
                        cv2.cvtColor(frames1[i][idx1], cv2.COLOR_RGB2BGR))
            cv2.imwrite(f"{fail_dir}/{video_name}_fail_point_{i}_YOUTUBE.jpg",
                        cv2.cvtColor(frames2[i][idx2], cv2.COLOR_RGB2BGR))

            return False, f"Visual mismatch (Closest Distance: {best_distance}). Checked a 0.8s window. Saved debug frames!"

    return True, "Videos are practically identical."


# --- EXECUTION EXAMPLE ---
if __name__ == "__main__":
    # # 1. Path to your local video [Adjust locally]
    local_video = ""

    # # 2. YT URL for comparison
    youtube_url = "https://www.youtube.com/"

    # # Video name for failed frame naming [e.g. 10.1]
    local_video_name = local_video.rsplit("/", maxsplit=1)[1]

    print("Analyzing local video visual fingerprint and duration...")
    local_data = get_video_fingerprint(local_video, is_youtube=False)

    print("Analyzing YouTube video visual fingerprint and duration...")
    youtube_data = get_video_fingerprint(youtube_url, is_youtube=True)

    if local_data[0] and youtube_data[0]:
        # Tweak duration_tolerance if YouTube adds a bit of silence/buffer to your specific videos
        is_same, reason = compare_videos(local_data, youtube_data, local_video_name, visual_threshold=8, duration_tolerance=1.5)

        print("\n--- ANALYSIS COMPLETE ---")
        if is_same:
            print(f"✅ MATCH: {reason}")
        else:
            print(f"❌ MISMATCH: {reason}")
    else:
        print("Error: Could not process one or both videos.")