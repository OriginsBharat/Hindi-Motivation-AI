from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import re
from src.video_sourcing import search_videos, download_video, download_audio
from src.voice_cloning import clone_voice
from src.video_generator import create_video_segment
from src import youtube_uploader
from moviepy.editor import VideoFileClip, concatenate_videoclips

app = Flask(__name__)
app.secret_key = 'a_very_secret_key_for_a_cool_project'

# --- Configuration ---
OUTPUT_DIR = "outputs"
DOWNLOAD_DIR_VIDEO = "downloads/videos"
DOWNLOAD_DIR_AUDIO = "downloads/audio"
ASSETS_DIR = "assets"
for d in [OUTPUT_DIR, DOWNLOAD_DIR_VIDEO, DOWNLOAD_DIR_AUDIO, ASSETS_DIR]:
    os.makedirs(d, exist_ok=True)
# --- End Configuration ---

@app.route('/')
def index():
    return render_template('index.html')

def parse_script(script_data):
    """Parses the user's script input into a list of tasks."""
    parts = script_data.strip().lower().split('new character')
    tasks = []
    for part in parts:
        if ',' in part:
            character, script = part.strip().split(',', 1)
            tasks.append({"character": character.strip(), "script": script.strip()})
    return tasks

@app.route('/generate', methods=['POST'])
def generate():
    script_data = request.form.get('script_data')
    tasks = parse_script(script_data)
    if not tasks:
        flash("Could not parse script. Use format: 'Character, Script'. Separate with 'new character'.")
        return redirect(url_for('index'))

    segment_paths = []
    # For now, we'll use a single dummy music track for all segments
    dummy_music_path = os.path.join(DOWNLOAD_DIR_AUDIO, "placeholder_music.mp3")
    if not os.path.exists(dummy_music_path):
        import numpy as np; import soundfile as sf
        sr, dur, freq = 44100, 5, 220
        t = np.linspace(0, dur, int(sr*dur), False)
        data = (np.iinfo(np.int16).max * 0.05 * np.sin(2*np.pi*freq*t)).astype(np.int16)
        sf.write(dummy_music_path, data, sr)

    for i, task in enumerate(tasks):
        char, script = task['character'], task['script']
        print(f"\n--- Generating segment {i+1}/{len(tasks)} for {char} ---")

        # --- 1. Sourcing Video Clips ---
        # NOTE: This will fail in the sandbox environment due to YouTube blocking.
        print(f"Sourcing videos for {char}...")
        video_urls = search_videos(f"{char} anime amv", limit=2)
        if not video_urls:
            flash(f"Could not find any video clips for '{char}'. Skipping this character.")
            continue

        video_clips = []
        for url in video_urls:
            path = download_video(url, DOWNLOAD_DIR_VIDEO)
            if path:
                video_clips.append(path)

        if not video_clips:
            flash(f"Failed to download any video clips for '{char}'. Skipping.")
            continue

        # --- 2. Voice Cloning ---
        # NOTE: This will fail in the sandbox due to YouTube blocking and heavy processing.
        print(f"Sourcing reference audio for {char}...")
        audio_urls = search_videos(f"{char} japanese voice", limit=1)
        if not audio_urls:
            flash(f"Could not find reference audio for '{char}'. Skipping.")
            continue

        ref_audio_path = download_audio(audio_urls[0], DOWNLOAD_DIR_AUDIO)
        if not ref_audio_path:
            flash(f"Failed to download reference audio for '{char}'. Skipping.")
            continue

        print(f"Cloning voice for {char}...")
        voiceover_path = clone_voice(
            text=script,
            reference_audio_path=ref_audio_path,
            output_filename=f"voice_{i}.wav"
        )
        if not voiceover_path:
            flash(f"Failed to clone voice for '{char}'. Skipping.")
            continue

        # --- 3. Create the segment ---
        segment_output_path = os.path.join(OUTPUT_DIR, f"segment_{i}.mp4")
        segment_path = create_video_segment(
            video_clip_paths=video_clips,
            voiceover_audio_path=voiceover_path,
            script_text=script,
            output_path=segment_output_path,
            music_path=dummy_music_path
        )
        if segment_path:
            segment_paths.append(segment_path)
        else:
            flash(f"Failed to create video segment for {char}.")
            # Clean up successful segments if one fails
            for p in segment_paths: os.remove(p)
            return redirect(url_for('index'))

    # --- 4. Concatenate all segments ---
    if not segment_paths:
        flash("Video generation failed, no segments were created.")
        return redirect(url_for('index'))

    print("\n--- Concatenating all segments ---")
    try:
        final_clips = [VideoFileClip(p) for p in segment_paths]
        final_video = concatenate_videoclips(final_clips, method="compose")
        final_filename = "final_tribute_video.mp4"
        final_path = os.path.join(OUTPUT_DIR, final_filename)
        final_video.write_videofile(final_path, codec="libx264", audio_codec="aac", temp_audiofile='temp-audio.m4a', remove_temp=True, threads=4, verbose=False, logger=None)
        print("--- Final video created successfully! ---")

        for clip in final_clips: clip.close()
        for p in segment_paths: os.remove(p)

        return redirect(url_for('result', filename=final_filename))
    except Exception as e:
        flash(f"Failed to concatenate final video: {e}")
        return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload():
    filename = request.form.get('filename')
    if not filename:
        flash("No filename provided for upload.")
        return redirect(request.referrer or url_for('index'))

    video_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(video_path):
        flash(f"Video file not found: {filename}")
        return redirect(request.referrer)

    try:
        print("Authenticating with YouTube...")
        youtube = youtube_uploader.get_authenticated_service()
        if not youtube:
            flash("YouTube authentication failed. Please see terminal for instructions.")
            return redirect(request.referrer)
    except Exception as e:
        flash(f"An authentication error occurred: {e}")
        return redirect(request.referrer)

    main_title = f"AI Generated Anime Tribute: {filename}"
    main_desc = "This video was generated by an AI. #AI #Anime #Tribute"
    video_id = youtube_uploader.upload_video(youtube, video_path, main_title, main_desc, ["ai", "anime"])
    if not video_id:
        flash("Failed to upload the main video.")
        return redirect(request.referrer)

    flash(f"Main video uploaded! Video ID: {video_id}")
    main_url = f"https://www.youtube.com/watch?v={video_id}"

    # --- Create and Upload Shorts ---
    try:
        with VideoFileClip(video_path) as video:
            for i in range(0, int(video.duration), 50):
                short_path = os.path.join(OUTPUT_DIR, f"short_{i}.mp4")
                video.subclip(i, min(i + 50, video.duration)).write_videofile(short_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
                short_desc = f"Clip from the full video: {main_url}"
                youtube_uploader.upload_video(youtube, short_path, f"AI Tribute Clip #{i//50 + 1}", short_desc, ["short", "anime"])
                os.remove(short_path)
    except Exception as e:
        flash(f"Error creating shorts: {e}")

    return redirect(request.referrer)

@app.route('/result')
def result():
    filename = request.args.get('filename')
    if not filename: return redirect(url_for('index'))
    return render_template('result.html', filename=filename)

@app.route('/outputs/<path:filename>')
def serve_video(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
