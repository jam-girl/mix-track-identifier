from abc import ABC, abstractmethod
from pytube import YouTube
import os

# import subprocess
from pydub import AudioSegment

from mix_track_identifier.config import logger
from mix_track_identifier.config import settings


class Downloader(ABC):
    url: str
    output_dir: str

    @abstractmethod
    def download_audio(self) -> str:
        pass


class YoutubeDownloader(Downloader):
    def __init__(self, url: str, output_dir: str):
        self.url = url
        self.output_dir = output_dir

    def download_audio(self):
        logger.info("download_audio|Starting")
        YouTube(self.url).streams.filter(only_audio=True).get_audio_only().download(
            self.output_dir
        )
        logger.info("download_audio|downloaded")
        # Iterate over files in the directory
        for filename in os.listdir(self.output_dir):
            if filename.endswith(".mp4"):
                input_file = os.path.join(self.output_dir, filename)
                output_file = os.path.join(
                    self.output_dir, os.path.splitext(filename)[0] + ".mp3"
                )
                # Run ffmpeg command to convert MP4 to MP3
                logger.info("download_audio|converting")
                # subprocess.run(
                #     [
                #         "ffmpeg",
                #         "-i",
                #         input_file,
                #         "-vn",
                #         "-acodec",
                #         "libmp3lame",
                #         "-q:a",
                #         "4",
                #         output_file,
                #     ],
                #     check=True,
                #     stdout=subprocess.DEVNULL,
                # )
                audio = AudioSegment.from_file(input_file)
                # Export the audio to MP3 format
                audio.export(output_file, format="mp3", bitrate="192k")
                logger.info("download_audio|converted")
        if not os.path.exists(output_file):
            msg = f"{output_file} does not exist"
            logger.info(msg)
            raise ValueError(msg)

        logger.info("download_audio|Ending")
        return output_file


class DownloaderFactory:
    @staticmethod
    def get_from_url(url: str) -> Downloader:
        if "yout" in url:
            return YoutubeDownloader(url=url, output_dir=settings.temp_output_dir)

        raise NotImplementedError(f"No downloader for {url}")
