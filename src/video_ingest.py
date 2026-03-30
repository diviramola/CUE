"""
CUE Video Ingest — Upload video, extract frames, create ad metadata.

Uses ffmpeg for frame extraction. Frames saved to wiom-ads/frames/{ad_id}/.
"""
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

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


def extract_frames(video_path, ad_id, num_frames=10):
    """Extract evenly spaced frames from a video using ffmpeg.

    Returns list of frame file paths.
    """
    out_dir = FRAMES_DIR / ad_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Get video duration
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(video_path)],
        capture_output=True, text=True, timeout=30
    )
    duration = float(probe.stdout.strip()) if probe.stdout.strip() else 30.0

    # Extract frames at even intervals
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


def get_video_duration(video_path):
    """Get video duration in seconds."""
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(video_path)],
        capture_output=True, text=True, timeout=30
    )
    return float(probe.stdout.strip()) if probe.stdout.strip() else None


def create_wiom_ad(video_path, advertiser, campaign, description,
                   language="Hindi", tags=None, platform="Meta"):
    """Create a new Wiom ad entry from an uploaded video.

    Returns (ad_id, metadata_dict, frame_paths, message).
    """
    ad_id = next_wiom_id()
    video_path = Path(video_path)

    if not video_path.exists():
        return None, None, [], f"Video file not found: {video_path}"

    # Get duration
    duration = get_video_duration(str(video_path)) or 0

    # Extract frames
    frame_paths = extract_frames(str(video_path), ad_id, num_frames=10)

    # Build metadata
    metadata = {
        "id": ad_id,
        "advertiser": advertiser or "Wiom",
        "campaign": campaign,
        "platform": platform,
        "format": "video",
        "duration_seconds": round(duration),
        "language": language,
        "source": "upload",
        "date_found": datetime.now().strftime("%Y-%m-%d"),
        "date_published": datetime.now().strftime("%Y-%m"),
        "vertical": "ISP/broadband",
        "region": "India",
        "description": description,
        "tags": tags or [],
        "frames_path": f"wiom-ads/frames/{ad_id}/",
        "video_filename": video_path.name,
    }

    # Save metadata
    meta_path = WIOM_DIR / f"{ad_id}.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return ad_id, metadata, frame_paths, f"Created {ad_id}: {len(frame_paths)} frames extracted"
