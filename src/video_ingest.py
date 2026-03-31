"""
CUE Video Ingest — Upload video, extract frames + audio, transcribe with Whisper.

Uses ffmpeg for frame/audio extraction, Groq Whisper API for transcription.
No new dependencies — Groq package already handles Whisper.
"""
import json
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

_local_env = Path(r"C:\credentials\.env")
if _local_env.exists():
    load_dotenv(_local_env)

import sys
sys.path.insert(0, str(Path(__file__).parent))
from harness import ROOT, WIOM_DIR

FRAMES_DIR = ROOT / "wiom-ads" / "frames"


def next_wiom_id():
    """Generate next wiom_XXX ID."""
    existing = sorted(WIOM_DIR.glob("wiom_*.json"))
    if not existing:
        return "wiom_001"
    nums = []
    for f in existing:
        try:
            nums.append(int(f.stem.replace("wiom_", "")))
        except ValueError:
            pass
    return f"wiom_{max(nums) + 1:03d}" if nums else "wiom_001"


def get_video_duration(video_path):
    """Get video duration in seconds."""
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(video_path)],
        capture_output=True, text=True, timeout=30
    )
    try:
        return float(probe.stdout.strip())
    except (ValueError, AttributeError):
        return None


def extract_frames(video_path, ad_id, num_frames=10):
    """Extract evenly spaced frames from a video using ffmpeg."""
    out_dir = FRAMES_DIR / ad_id
    out_dir.mkdir(parents=True, exist_ok=True)

    duration = get_video_duration(str(video_path)) or 30.0
    interval = duration / (num_frames + 1)
    frame_paths = []

    for i in range(1, num_frames + 1):
        timestamp = interval * i
        out_file = out_dir / f"frame_{i:02d}.jpg"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(timestamp), "-i", str(video_path),
             "-frames:v", "1", "-q:v", "2", str(out_file)],
            capture_output=True, timeout=30
        )
        if out_file.exists():
            frame_paths.append(str(out_file))

    return frame_paths


def extract_audio(video_path, output_path=None):
    """Extract audio track from video as mp3 using ffmpeg.

    Returns path to audio file, or None if extraction fails.
    Groq Whisper accepts: mp3, mp4, mpeg, mpga, m4a, wav, webm (max 25MB).
    """
    if output_path is None:
        # Use a temp file
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        output_path = tmp.name
        tmp.close()

    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path),
         "-vn",               # no video
         "-acodec", "mp3",
         "-ab", "64k",        # 64kbps — good enough for speech, keeps file small
         "-ar", "16000",      # 16kHz sample rate — Whisper's preferred rate
         str(output_path)],
        capture_output=True, timeout=60
    )

    if result.returncode == 0 and Path(output_path).exists():
        return output_path
    return None


def transcribe_audio(audio_path, language="hi"):
    """Transcribe audio using Groq Whisper API.

    Uses whisper-large-v3-turbo — fast, multilingual, free on Groq.
    language: 'hi' for Hindi, 'en' for English, None for auto-detect.
    Returns dict with transcript text and detected language.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return {"error": "No GROQ_API_KEY set", "text": "", "language": None}

    # Check file size — Groq Whisper limit is 25MB
    size_mb = Path(audio_path).stat().st_size / (1024 * 1024)
    if size_mb > 24:
        return {"error": f"Audio file too large ({size_mb:.1f}MB, max 24MB)", "text": "", "language": None}

    try:
        from groq import Groq
        client = Groq(api_key=groq_key)

        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                file=(Path(audio_path).name, f),
                model="whisper-large-v3-turbo",
                language=language,          # None = auto-detect
                response_format="verbose_json",  # includes detected language
                temperature=0.0,
            )

        return {
            "text": response.text,
            "language": getattr(response, "language", language),
            "duration_seconds": getattr(response, "duration", None),
            "error": None,
        }
    except Exception as e:
        return {"error": str(e), "text": "", "language": None}


def transcribe_video(video_path, language="hi"):
    """Full pipeline: extract audio from video, then transcribe.

    Returns transcript dict. Cleans up temp audio file.
    """
    audio_path = None
    try:
        audio_path = extract_audio(str(video_path))
        if not audio_path:
            return {"error": "Audio extraction failed", "text": "", "language": None}

        result = transcribe_audio(audio_path, language=language)
        return result
    finally:
        # Always clean up temp audio file
        if audio_path and Path(audio_path).exists():
            try:
                Path(audio_path).unlink()
            except Exception:
                pass


def create_wiom_ad(video_path, advertiser, campaign, description,
                   language="Hindi", tags=None, platform="Meta"):
    """Create a new Wiom ad entry from an uploaded video.

    Extracts frames + transcribes audio via Groq Whisper.
    Returns (ad_id, metadata_dict, frame_paths, message).
    """
    ad_id = next_wiom_id()
    video_path = Path(video_path)

    if not video_path.exists():
        return None, None, [], f"Video file not found: {video_path}"

    duration = get_video_duration(str(video_path)) or 0
    frame_paths = extract_frames(str(video_path), ad_id, num_frames=10)

    # Transcribe audio — map language name to Whisper language code
    lang_codes = {
        "Hindi": "hi", "English": "en", "Tamil": "ta", "Telugu": "te",
        "Marathi": "mr", "Bengali": "bn", "Multilingual": None,
    }
    whisper_lang = lang_codes.get(language, "hi")
    transcript_result = transcribe_video(str(video_path), language=whisper_lang)

    transcript_text = transcript_result.get("text", "")
    transcript_error = transcript_result.get("error")

    # Build metadata
    metadata = {
        "id": ad_id,
        "advertiser": advertiser or "Wiom",
        "campaign": campaign,
        "platform": platform,
        "format": "video",
        "duration_seconds": round(duration),
        "language": transcript_result.get("language") or language,
        "source": "upload",
        "date_found": datetime.now().strftime("%Y-%m-%d"),
        "date_published": datetime.now().strftime("%Y-%m"),
        "vertical": "ISP/broadband",
        "region": "India",
        "description": description,
        "tags": tags or [],
        "frames_path": f"wiom-ads/frames/{ad_id}/",
        "video_filename": video_path.name,
        "transcript": transcript_text or None,
        "transcript_error": transcript_error or None,
    }

    meta_path = WIOM_DIR / f"{ad_id}.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    words = len(transcript_text.split()) if transcript_text else 0
    transcript_note = f", transcript: {words} words" if words else (f", transcript failed: {transcript_error}" if transcript_error else ", no audio")
    msg = f"Created {ad_id}: {len(frame_paths)} frames extracted{transcript_note}"
    return ad_id, metadata, frame_paths, msg
