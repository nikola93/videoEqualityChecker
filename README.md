# Video Equality Checker

This project is used for comapring local and YouTube uploaded videos using Python OpenCV and ImageHash libraries.

## Installation

`pip3 install opencv-python imagehash yt-dlp`

`brew install ffmpeg`

## Configuration

Unless you want to download all the files locally, preffered way is to download Google Drive app for your OS, adjust the `LOCAL_VIDEO_FOLDER` variable to your local setup and let the script run.

### Google Drive option

For making .xsl and mp4 files visible on your local machine using the Google Drive app, you should first mark them in Web app by rigth-clicking on that file/folder, click `Organize`, then click `Add shortcut`, and after choose `All locations -> My Drive` and click `Add`. This will make file (`uporedna_tabela`) and folder (`Online obuka snimci`) visible on your local machine.

After you make them visible locally, you should download `uporedna_tabela` file as a `.csv` document, and adjust the `INPUT_CSV` variable to the local path.

## Running the script

#### Comparing all videos from the xsl (csv) file. 

`python3 main.py`

#### Comparing single video and url (variables here are set: 1) local path to the video (Google Drive location) 2) URL from the xsl file)

`python3 single_video_check.py`

Results are stored in `comparison_results.csv` and `comparison_results_after_mismatch.csv` (the second one is generated only if the first pass detects some mismatches, and is used as a second (confirming) pass, since fist pass has proven some occasional and minor flakines)
