import os

import cv2

from .config import DURATION_TOLERANCE, FAILED_FRAMES_DIR, FRAME_OFFSET_SECONDS, VISUAL_THRESHOLD


def compare_videos(data1, data2, video_name, visual_threshold=VISUAL_THRESHOLD,
                   duration_tolerance=DURATION_TOLERANCE):
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

        # If the absolute BEST match in that window still fails...
        if best_distance > visual_threshold:
            idx1, idx2 = best_pair_indices
            save_debug_frames(video_name, i, frames1[i][idx1], frames2[i][idx2])

            window = 2 * FRAME_OFFSET_SECONDS
            return False, f"Visual mismatch (Closest Distance: {best_distance}). Checked a {window}s window. Saved debug frames!"

    return True, "Videos are practically identical."


def save_debug_frames(video_name, point_index, local_frame, youtube_frame):
    """Saves the closest (RGB) frames that failed to match, for manual inspection."""
    os.makedirs(FAILED_FRAMES_DIR, exist_ok=True)

    cv2.imwrite(f"{FAILED_FRAMES_DIR}/{video_name}_fail_point_{point_index}_LOCAL.jpg",
                cv2.cvtColor(local_frame, cv2.COLOR_RGB2BGR))
    cv2.imwrite(f"{FAILED_FRAMES_DIR}/{video_name}_fail_point_{point_index}_YOUTUBE.jpg",
                cv2.cvtColor(youtube_frame, cv2.COLOR_RGB2BGR))
