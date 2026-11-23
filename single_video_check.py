from video_checker.comparison import compare_videos
from video_checker.config import SINGLE_LOCAL_VIDEO, SINGLE_YOUTUBE_URL
from video_checker.fingerprint import get_video_fingerprint

if __name__ == "__main__":
    # Video name for failed frame naming [e.g. 10.1]
    local_video_name = SINGLE_LOCAL_VIDEO.rsplit("/", maxsplit=1)[1]

    print("Analyzing local video visual fingerprint and duration...")
    local_data = get_video_fingerprint(SINGLE_LOCAL_VIDEO, is_youtube=False)

    print("Analyzing YouTube video visual fingerprint and duration...")
    youtube_data = get_video_fingerprint(SINGLE_YOUTUBE_URL, is_youtube=True)

    if local_data[0] and youtube_data[0]:
        # Tweak DURATION_TOLERANCE in config if YouTube adds a bit of silence/buffer to your specific videos
        is_same, reason = compare_videos(local_data, youtube_data, local_video_name)

        print("\n--- ANALYSIS COMPLETE ---")
        if is_same:
            print(f"✅ MATCH: {reason}")
        else:
            print(f"❌ MISMATCH: {reason}")
    else:
        print("Error: Could not process one or both videos.")
