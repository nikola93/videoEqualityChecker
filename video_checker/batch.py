import csv
import os

from .comparison import compare_videos
from .fingerprint import get_video_fingerprint
from .sources.local import find_latest_video

STATUS_MATCH = "✅ MATCH"
STATUS_MISMATCH = "❌ MISMATCH"
STATUS_MISSING = "MISSING LOCALLY"


def process_csv_batch(csv_filepath, local_folder, output_filepath, only_mismatches):
    """
    Reads the CSV, loops through files, and writes results to a new CSV.
    With 'only_mismatches', the input is a previous results CSV and matched rows are skipped.
    Returns True if any mismatch was found.
    """
    mismatch = False

    with open(output_filepath, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["Area", "Video Name", "YouTube URL", "Match Status", "Details"])

        with open(csv_filepath, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            next(reader, None)  # Skip the header row

            for row in reader:
                # Make sure the row has at least 3 columns (Area, Video, URL)
                if len(row) < 3 or not row[1].strip() or not row[2].strip():
                    continue

                # row[0] is "## Увод", row[1] is "0.1", row[2] is the URL
                area_name = row[0].strip()
                video_name = row[1].strip()
                youtube_url = row[2].strip()

                if only_mismatches and row[3].strip() == STATUS_MATCH:
                    continue

                print(f"\n--- Checking: {area_name} | {video_name} ---")

                # Find the most recently edited local file
                local_video_path = find_latest_video(local_folder, video_name)

                if not local_video_path:
                    print(f"  [!] No files found starting with '{video_name}' in folder.")
                    writer.writerow([area_name, video_name, youtube_url, STATUS_MISSING, "No matching file found"])
                    continue

                print(f"  -> Found newest version: {os.path.basename(local_video_path)}")

                print("  -> Fetching Local Data...")
                local_data = get_video_fingerprint(local_video_path, is_youtube=False)

                print("  -> Fetching YouTube Data...")
                youtube_data = get_video_fingerprint(youtube_url, is_youtube=True)

                is_same, reason = compare_videos(local_data, youtube_data, video_name)

                status = STATUS_MATCH if is_same else STATUS_MISMATCH
                if not is_same:
                    mismatch = True
                print(f"  Result: {status} | {reason}")

                writer.writerow([area_name, video_name, youtube_url, status, reason])

    print(f"\n🎉 BATCH COMPLETE! Check your results in: {output_filepath}")
    return mismatch
