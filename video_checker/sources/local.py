import glob
import os


def find_latest_video(folder_path, video_base_name):
    """
    Searches the folder AND ALL SUBFOLDERS for files starting with the video_base_name
    (e.g. '0.1') and returns the exact path of the most recently modified version.
    """
    # Remove .mp4 if it's there so we can search broadly
    base_name = video_base_name.replace('.mp4', '').strip()

    search_pattern = os.path.join(folder_path, "**", f"{base_name}*.mp4")
    matching_files = glob.glob(search_pattern, recursive=True)

    if not matching_files:
        return None  # No file found

    # If there are multiple files across different folders, sort them by newest!
    return max(matching_files, key=os.path.getmtime)
