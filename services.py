from collections import namedtuple
from typing import Generator
from dataclasses import dataclass
from functools import cached_property
import youtube_dl
import math

import os
from speech import transcribe_speech
from mlogging import logger
from google.cloud import storage
from pydub import AudioSegment

FIVE_MINUTES_IN_MILISECONDS = 1000 * 60 * 5

Audio = namedtuple("Audio", ["audio_segment", "filename"])


@dataclass
class VideoTranscriberService:
    url: str

    @cached_property
    def storage_client(self):
        return storage.Client()

    @cached_property
    def bucket(self):
        return self.storage_client.bucket(os.environ["GCS_BUCKET"])

    def get_audios(self, video_url: str) -> Generator[Audio, None, None]:
        """
        Download a video from a given URL and convert it to MP3 format. Then, split the original
        audio into 5-minute chunks
        """

        original_path = self._download_audio(video_url=video_url)
        original_audio = AudioSegment.from_mp3(original_path)
        song_duration = len(original_audio)
        start = 0
        chunk_size = math.ceil(song_duration / FIVE_MINUTES_IN_MILISECONDS)

        for index in range(start, chunk_size):
            audio = original_audio[start : start + FIVE_MINUTES_IN_MILISECONDS]
            start += FIVE_MINUTES_IN_MILISECONDS
            folder, filename = original_path.split("/")[-2:]
            yield Audio(
                audio_segment=audio, filename=f"{folder}/index-{index}-{filename}"
            )

    def _download_audio(self, video_url: str) -> str:
        saved_file_path = []

        def postprocessor_hook(item):
            if item["status"] == "finished":
                saved_file_path.append(f"{item['filename'].split('.')[0]}.mp3")

        ydl_opts = {
            "outtmpl": "audios/%(id)s.%(ext)s",
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }
            ],
            "nooverwrites": True,
            "progress_hooks": [postprocessor_hook],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return saved_file_path[0]

    def _upload_to_gcs(self, audio: Audio) -> str:
        audio.audio_segment.export(audio.filename)
        blob_destination = audio.filename.split("/")[-1]
        blob = self.bucket.blob(f"audio-files/{blob_destination}")
        logger.info(f"Uploading audio {blob.name} file to gcs")
        if not blob.exists():
            blob.upload_from_filename(audio.filename)
        else:
            logger.info(f"Audio {blob.name} already exists in GCS")

        return f"gs://{self.bucket.name}/{blob.name}"

    def run(self) -> str:
        audios = self.get_audios(video_url=self.url)
        transcriptions = []
        for audio in audios:
            uri = self._upload_to_gcs(audio=audio)
            transcriptions.extend(transcribe_speech(uri=uri))
        return " ".join(transcriptions)
