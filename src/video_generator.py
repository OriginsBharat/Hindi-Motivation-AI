import os
import re
from moviepy.editor import (VideoFileClip, AudioFileClip, CompositeAudioClip,
                            concatenate_videoclips, TextClip, CompositeVideoClip)
import moviepy.audio.fx.all as afx

def create_video_segment(
    video_clip_paths: list[str],
    voiceover_audio_path: str,
    script_text: str,
    output_path: str,
    music_path: str | None = None,
    resolution: tuple[int, int] = (1080, 1920),
    font_path: str = 'assets/1942.ttf'
) -> str | None:
    """
    Creates a single video segment for one character.
    This includes combining clips, voiceover, music, and text.
    Returns the path to the created segment if successful, otherwise None.
    """
    try:
        print(f"--- Creating segment: {os.path.basename(output_path)} ---")

        # --- 1. Load Audio and get duration ---
        voiceover_clip = AudioFileClip(voiceover_audio_path)
        segment_duration = voiceover_clip.duration

        # --- 2. Load and Concatenate Video Clips ---
        clips = [
            VideoFileClip(path).resize(height=resolution[1]).set_position(('center', 'center'))
            for path in video_clip_paths if os.path.exists(path)
        ]
        if not clips:
            print("Error: No valid video clips for segment."); return None

        base_video = concatenate_videoclips(clips, method="compose")
        # Loop or trim the base video to match the audio duration
        if base_video.duration < segment_duration:
            base_video = base_video.fx(afx.loop, duration=segment_duration)
        else:
            base_video = base_video.subclip(0, segment_duration)

        # --- 3. Create Text Overlays ---
        sentences = [s.strip() for s in re.split(r'[.!?]+', script_text) if s.strip()]
        text_overlays = []
        if sentences:
            duration_per_sentence = segment_duration / len(sentences)
            current_time = 0
            for sentence in sentences:
                try:
                    # Attempt to use the custom font
                    text_clip = TextClip(
                        sentence, fontsize=70, color='white', font=font_path,
                        stroke_color='black', stroke_width=2, method='caption',
                        size=(resolution[0] * 0.8, None)
                    )
                except Exception as e:
                    # Fallback to a default font if the custom one fails
                    print(f"Warning: Font '{font_path}' not found or failed to load ({e}). Using default font.")
                    text_clip = TextClip(
                        sentence, fontsize=70, color='white',
                        stroke_color='black', stroke_width=2, method='caption',
                        size=(resolution[0] * 0.8, None)
                    )

                text_clip = text_clip.set_position('center').set_duration(duration_per_sentence)
                text_clip = text_clip.fadein(0.5).fadeout(0.5).set_start(current_time)
                text_overlays.append(text_clip)
                current_time += duration_per_sentence

        # --- 4. Mix Audio ---
        audio_clips = [voiceover_clip]
        if music_path and os.path.exists(music_path):
            music_clip = AudioFileClip(music_path).fx(afx.audio_loop, duration=segment_duration)
            music_clip = music_clip.volumex(0.2)
            audio_clips.append(music_clip)

        final_audio = CompositeAudioClip(audio_clips)

        # --- 5. Final Composition ---
        final_video_layers = [base_video] + text_overlays

        final_segment = CompositeVideoClip(final_video_layers, size=resolution)
        final_segment = final_segment.set_audio(final_audio).set_duration(segment_duration)

        final_segment.write_videofile(
            output_path, codec='libx264', audio_codec='aac',
            temp_audiofile=f'temp-audio-{os.path.basename(output_path)}.m4a', remove_temp=True,
            threads=4, verbose=False
        )
        print(f"--- Segment created successfully: {output_path} ---")
        return output_path

    except Exception as e:
        print(f"An error occurred during segment creation: {e}")
        # Clean up failed segment file if it exists
        if os.path.exists(output_path):
            os.remove(output_path)
        return None
