import os
import subprocess
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, jsonify
import yt_dlp
import ffmpeg
import logging

"""
I didn't clean up the code yet, so everything is in this file:
1) Download youtube videos with yt_dlp
2) Seperate the media into sound components, i.e. vocals and non_vocals (music, etc.)
3) Merge the media back with vocals and video components. 

Using flask to manage the video processing requests.
"""

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def download_youtube_video(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(app.config['UPLOAD_FOLDER'], '%(title)s.%(ext)s'),
        'noplaylist': True,
        'keepvideo': True,  # Don't delete source files, which helps with merge faults
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4'
        }]
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info_dict)
        return video_file
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return None

def separate_music_demucs(filepath):
    try:
        output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'demucs_output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # syscall to demucs
        subprocess.run([
            "demucs", filepath, "-o", output_dir, "--two-stems", "vocals"
        ], check=True)

        vocals_path = os.path.join(output_dir, "htdemucs", os.path.basename(filepath).replace('.webm', ''), 'vocals.wav')
        return vocals_path

    except Exception as e:
        logging.error(f"Error separating music with Demucs: {e}")
        return None


def merge_audio_video(video_path, vocals_path):
    output_video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + os.path.splitext(os.path.basename(video_path))[0] + '.mp4')

    try:
        if not os.path.exists(video_path):
            logging.error(f"Video file does not exist: {video_path}")
            return None

        if not os.path.exists(vocals_path):
            logging.error(f"Vocals file does not exist: {vocals_path}")
            return None

        # ensure format
        input_video = ffmpeg.input(video_path)
        input_audio = ffmpeg.input(vocals_path)

        (
            ffmpeg
            .concat(input_video, input_audio, v=1, a=1)
            .output(output_video_path, vcodec='libx264', acodec='aac', audio_bitrate='320k', ar='44100')
            .run(overwrite_output=True)
        )

        return output_video_path
    except ffmpeg.Error as e:
        logging.error(f"FFmpeg error: {e.stderr}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during merging video and audio: {e}")
        return None



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        if url:
            video_path = download_youtube_video(url)
            
            vocals_path = separate_music_demucs(video_path)
            
            final_video_path = merge_audio_video(video_path, vocals_path)
            
            if final_video_path:
                return jsonify({
                    "status": "completed",
                    "video_url": url_for('serve_video', filename=os.path.basename(final_video_path))
                })
            else:
                return jsonify({"status": "error"})
    return render_template('index.html')


@app.route('/video/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)