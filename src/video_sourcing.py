import os
import yt_dlp

def search_videos(query: str, limit: int = 5):
    """
    Searches YouTube for videos matching the query using yt-dlp.
    """
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            if 'entries' in result:
                return [entry['url'] for entry in result['entries']]
    except Exception as e:
        print(f"Error searching videos: {e}")
    return []

def download_video(video_url: str, output_dir: str = "downloads/videos"):
    """
    Downloads a video from a given URL.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            return ydl.prepare_filename(info_dict)
    except Exception as e:
        print(f"Error downloading video: {e}")
    return None

def download_audio(video_url: str, output_dir: str = "downloads/audio"):
    """
    Downloads only the audio from a given URL.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            base_filename = ydl.prepare_filename(info_dict)
            # The postprocessor changes the extension. The base name is what we need.
            filename_no_ext, _ = os.path.splitext(base_filename)
            return filename_no_ext + ".mp3"
    except Exception as e:
        print(f"Error downloading audio: {e}")
    return None

if __name__ == '__main__':
    search_query = "Goku Super Saiyan 3 transformation"
    print(f"Searching for videos with query: '{search_query}'")
    video_urls = search_videos(search_query, limit=1)

    if video_urls:
        print(f"Found {len(video_urls)} video(s).")
        video_url = video_urls[0]

        print(f"\nDownloading video: {video_url}")
        video_path = download_video(video_url)
        if video_path and os.path.exists(video_path):
            print(f"Video downloaded successfully to: {video_path}")
        else:
            print("Video download failed.")

        print(f"\nDownloading audio from: {video_url}")
        audio_path = download_audio(video_url)
        if audio_path and os.path.exists(audio_path):
            print(f"Audio downloaded successfully to: {audio_path}")
        else:
            print("Audio download failed.")
    else:
        print("No videos found.")
