import json
import os
from typing import Any, Dict, List
from pydantic import BaseModel
from pydub import AudioSegment
from shazamio import Shazam
import asyncio

from mix_track_identifier.config import logger
from mix_track_identifier.config import settings
from mix_track_identifier.download import DownloaderFactory


def split_audio(input_file, output_dir):
    logger.info("split_audio|Starting")
    audio = AudioSegment.from_mp3(input_file)
    logger.info("split_audio|Read into memory")
    chunk_length_ms = 20 * 1000  # 20 seconds
    for i, chunk_start in enumerate(range(0, len(audio), chunk_length_ms)):
        logger.info(f"split_audio|{i}|Starting")
        chunk = audio[chunk_start : chunk_start + chunk_length_ms]
        chunk.export(os.path.join(output_dir, f"chunk_{i}.mp3"), format="mp3")
        logger.info(f"split_audio|{i}|Exported")
    logger.info("split_audio|Ending")


class TrackDetails(BaseModel):
    artist: str
    title: str
    timestamp: int


def recognise_audio(chunk_file) -> TrackDetails:
    timestamp = int(chunk_file.split("_")[1].split(".")[0]) * 20
    values: Dict[str, Any] = asyncio.run(Shazam().recognize(chunk_file))
    if "track" in values:
        track = values["track"]
        artist = "n/a"
        if "subtitle" in track:
            artist = track["subtitle"]

        title = "n/a"
        if "title" in track:
            title = track["title"]

        return TrackDetails(artist=artist, title=title, timestamp=timestamp)

    logger.warning("No matches")
    return TrackDetails(artist="n/a", title="n/a", timestamp=timestamp)


def clean_up(directory: str) -> None:
    logger.info(f"Cleaning up {directory} directory")
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    os.rmdir(directory)
    logger.info(f"Done cleaning up {directory}")


def main(url: str):
    logger.info("main|Starting")
    temp_dir = settings.temp_output_dir
    os.makedirs(temp_dir, exist_ok=True)

    downloader = DownloaderFactory.get_from_url(url)
    file_to_process = downloader.download_audio()

    if not file_to_process.endswith(".mp3"):
        raise ValueError(f"{file_to_process} does not end with .mp3")

    split_audio(file_to_process, temp_dir)

    chunks = os.listdir(temp_dir)
    chunks.sort()

    tracks: List[TrackDetails] = []
    for chunk_file in chunks:
        if chunk_file.startswith("chunk_"):
            track = recognise_audio(os.path.join(temp_dir, chunk_file))
            tracks.append(track)

    sorted_tracks = sorted(tracks, key=lambda x: x.timestamp)
    for track in sorted_tracks:
        logger.info(track.dict())

    # File path for the JSON file
    json_file = os.path.join(settings.final_output_dir, "program_output.json")

    # Write the list of TrackDetails objects to a JSON file
    with open(json_file, "w") as f:
        json.dump([track.dict() for track in tracks], f, indent=4)

    # Clean up temp directory
    clean_up(temp_dir)

    logger.info("main|Ending")


if __name__ == "__main__":
    url = input("Enter SoundCloud or YouTube URL: ")
    logger.info("About to start")
    try:
        main(url)
    except Exception as e:
        logger.error("Exception")
        logger.exception(e)
        raise
    logger.info("Done")
