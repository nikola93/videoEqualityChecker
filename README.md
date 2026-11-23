# Video Equality Checker

This project is used for comparing video equality of local and YouTube uploaded videos using Python OpenCV and ImageHash libraries.

## Installation

`pip3 install -r requirements.txt`

`brew install ffmpeg`

## Project structure

```
main.py                  # Entry point: compares all videos from the CSV file
single_video_check.py    # Entry point: compares a single local video with a YouTube URL
video_checker/
├── config.py            # Paths, output files and comparison thresholds
├── batch.py             # CSV batch processing and results report
├── fingerprint.py       # Frame sampling and perceptual hashing
├── comparison.py        # Duration and visual comparison, debug frame saving
└── sources/
    ├── local.py         # Finding the newest local video file
    └── youtube.py       # Fetching duration and stream URL via yt-dlp
```

## Configuration

All variables mentioned below are located in `video_checker/config.py`.

Unless you want to download all the files locally, preferred way is to download Google Drive app for your OS, adjust the `LOCAL_VIDEO_FOLDER` variable to your local setup and let the script run.

### Google Drive option

For making .xsl and mp4 files visible on your local machine using the Google Drive app, you should first mark them in Web app by right-clicking on that file/folder, click `Organize`, then click `Add shortcut`, and after choose `All locations -> My Drive` and click `Add`. This will make file (`uporedna_tabela`) and folder (`Online obuka snimci`) visible on your local machine.

After you make them visible locally, you should download `uporedna_tabela` file as a `.csv` document, and adjust the `INPUT_CSV` variable to the local path.

## Running the script

#### Comparing all videos from the XSL (csv) file. 

`python3 main.py`

#### Comparing single video and url (set `SINGLE_LOCAL_VIDEO` to the local path to the video (Google Drive location) and `SINGLE_YOUTUBE_URL` to the URL from the XSL file)

`python3 single_video_check.py`

Results are stored in `comparison_results.csv` and `comparison_results_after_mismatch.csv` (the second one is generated only if the first pass detects some mismatches, and is used as a second (confirming) pass, since fist pass has proven some occasional and minor flakiness)
