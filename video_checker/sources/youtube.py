import subprocess

from ..config import YOUTUBE_FORMAT

YT_DLP_CMD = ['yt-dlp', '--no-check-certificates', '--js-runtimes', 'node']


def get_youtube_duration(url):
    """Fetches the exact duration (in seconds) of a YouTube video using yt-dlp."""
    output = subprocess.check_output([*YT_DLP_CMD, '--print', 'duration', url], text=True).strip()
    return float(output) if output else 0.0


def get_youtube_stream_url(url):
    """Returns a direct stream URL of the YouTube video that OpenCV can read."""
    return subprocess.check_output([*YT_DLP_CMD, '-g', '-f', YOUTUBE_FORMAT, url], text=True).strip()
