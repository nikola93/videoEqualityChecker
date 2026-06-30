import csv
import glob
import os
import subprocess

import cv2
import imagehash
from PIL import Image


def find_latest_video(folder_path, video_base_name):
    """
    Searches the folder AND ALL SUBFOLDERS for files starting with the video_base_name
    (e.g. '0.1') and returns the exact path of the most recently modified version.
    """
    # Remove .mp4 if it's there so we can search broadly
    base_name = video_base_name.replace('.mp4', '').strip()

    # 🌟 NEW: Added "**" to look inside all subfolders
    search_pattern = os.path.join(folder_path, "**", f"{base_name}*.mp4")

    # 🌟 NEW: Added recursive=True so it actually dives into those folders
    matching_files = glob.glob(search_pattern, recursive=True)

    if not matching_files:
        return None  # No file found

    # If there are multiple files across different folders, sort them by newest!
    latest_file = max(matching_files, key=os.path.getmtime)

    return latest_file

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


def process_csv_batch(csv_filepath, local_folder, output_filepath, hasMismatch):
    """Reads the CSV, loops through files, and writes results to a new CSV."""

    with open(output_filepath, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        # Added the "Area" column to your output so you know which section it belongs to!
        writer.writerow(["Area", "Video Name", "YouTube URL", "Match Status", "Details"])

        with open(csv_filepath, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            header = next(reader, None)  # Skip the header row
            mismatch = False

            for row in reader:
                # Make sure the row has at least 3 columns (Area, Video, URL)
                if len(row) < 3 or not row[1].strip() or not row[2].strip():
                    continue

                # --- THIS IS THE FIX ---
                # row[0] is "## Увод", row[1] is "0.1", row[2] is the URL
                area_name = row[0].strip()
                video_name = row[1].strip()
                youtube_url = row[2].strip()

                if hasMismatch:
                    status_col = row[3].strip()
                    if status_col == "✅ MATCH":
                        continue

                print(f"\n--- Checking: {area_name} | {video_name} ---")

                # Find the most recently edited local file
                local_video_path = find_latest_video(local_folder, video_name)

                # Check if we actually found a file
                if not local_video_path:
                    print(f"  [!] No files found starting with '{video_name}' in folder.")
                    writer.writerow([area_name, video_name, youtube_url, "MISSING LOCALLY", "No matching file found"])
                    continue

                print(f"  -> Found newest version: {os.path.basename(local_video_path)}")

                print("  -> Fetching Local Data...")
                local_data = get_video_fingerprint(local_video_path, is_youtube=False)

                print("  -> Fetching YouTube Data...")
                youtube_data = get_video_fingerprint(youtube_url, is_youtube=True)

                # Compare
                is_same, reason = compare_videos(local_data, youtube_data, video_name)

                status = "✅ MATCH" if is_same else "❌ MISMATCH"
                if not is_same:
                    mismatch = True
                print(f"  Result: {status} | {reason}")

                # Write to the results CSV
                writer.writerow([area_name, video_name, youtube_url, status, reason])

    print(f"\n🎉 BATCH COMPLETE! Check your results in: {output_filepath}")
    return mismatch


# --- EXECUTION ---
if __name__ == "__main__":
    # # 1. Path to your uploaded CSV file [Adjust locally]
    INPUT_CSV = ""
    #
    # # 2. Path to your local setup [Adjust locally]
    LOCAL_VIDEO_FOLDER = ""
    #
    # # 3. Where you want the final report saved
    OUTPUT_CSV = "comparison_results.csv"
    #
    # # Run the batch process
    hasMismatch = process_csv_batch(INPUT_CSV, LOCAL_VIDEO_FOLDER, OUTPUT_CSV, False)
    # # Run again for mismatches
    if hasMismatch:
        INPUT_CSV = OUTPUT_CSV
        OUTPUT_CSV = "comparison_results_after_mismatch.csv"
        process_csv_batch(INPUT_CSV, LOCAL_VIDEO_FOLDER, OUTPUT_CSV, True)


