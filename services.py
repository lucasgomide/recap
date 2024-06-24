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


@dataclass
class VideoTranscriberService:
    url: str
    GCS_BUCKET: str = os.environ["GCS_BUCKET"]

    @cached_property
    def storage_client(self):
        return storage.Client()

    def get_audios_path(self, video_url: str) -> list[str]:
        """
        Download a video from a given URL and convert it to MP3 format. Then, split the original
        audio into 5-minute chunks
        """

        original_path = self._download_audio(video_url=video_url)
        original_audio = AudioSegment.from_mp3(original_path)
        song_duration = len(original_audio)
        start = 0
        files_paths = []
        chunk_size = math.ceil(song_duration / FIVE_MINUTES_IN_MILISECONDS)
        # TODO: split audios parallelly
        for chunk in range(start, chunk_size):
            temp_audio = original_audio[start : start + FIVE_MINUTES_IN_MILISECONDS]
            start += FIVE_MINUTES_IN_MILISECONDS
            temp_path = f"{original_path.split('.')[0]}-part-{chunk}.mp3"
            temp_audio.export(temp_path, format="mp3")
            files_paths.append(temp_path)

        return files_paths

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
            "progress_hooks": [postprocessor_hook],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return saved_file_path[0]

    def _upload_to_gcs(self, audio_paths: list[str]) -> list[str]:
        blobs_path = []
        bucket = self.storage_client.bucket(self.GCS_BUCKET)
        for audio_path in audio_paths:
            destination = f"audio-files/{audio_path.split("/")[-1]}"
            blob = bucket.blob(destination)
            logger.info(f"Uploading audio {blob.name} file to gcs")
            if not blob.exists():
                blob.upload_from_filename(audio_path)
            else:
                logger.info(f"Audio {blob.name} already exists in GCS")

            blobs_path.append(f"gs://{bucket.name}/{blob.name}")
        return blobs_path

    def run(self) -> str:
        audios_path = self.get_audios_path(video_url=self.url)
        uris = self._upload_to_gcs(audio_paths=audios_path)
        transcriptions = []
        for uri in uris:
            transcriptions.extend(transcribe_speech(uri=uri))
        return " ".join(transcriptions)
