from video_checker.batch import process_csv_batch
from video_checker.config import INPUT_CSV, LOCAL_VIDEO_FOLDER, MISMATCH_OUTPUT_CSV, OUTPUT_CSV

if __name__ == "__main__":
    has_mismatch = process_csv_batch(INPUT_CSV, LOCAL_VIDEO_FOLDER, OUTPUT_CSV, only_mismatches=False)

    # Run again for mismatches, since the first pass has proven to be occasionally flaky
    if has_mismatch:
        process_csv_batch(OUTPUT_CSV, LOCAL_VIDEO_FOLDER, MISMATCH_OUTPUT_CSV, only_mismatches=True)
