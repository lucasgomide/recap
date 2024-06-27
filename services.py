from pathlib import Path
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
        original_audio = AudioSegment.from_file(original_path, format="mp4")
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
        paths = video_url.removeprefix("gs://").split("/")
        bucket_name, blob_file = paths[0], "/".join(paths[1:])
        bucket = self.storage_client.get_bucket(bucket_name)
        saved_file_path = f"audios/{paths[-1]}"
        my_file = Path(saved_file_path)
        if my_file.is_file():
            logger.info("File already aexists")
            return saved_file_path

        blob = bucket.blob(blob_file)
        blob.download_to_filename(saved_file_path)

        return saved_file_path

    def _upload_to_gcs(self, audio: Audio) -> str:
        audio.audio_segment.export(audio.filename)
        blob_destination = audio.filename.split("/")[-1]
        blob = self.bucket.blob(f"audios/{blob_destination}")
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
