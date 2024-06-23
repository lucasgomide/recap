from dataclasses import dataclass
from functools import cached_property
import youtube_dl
import os
from speech import transcribe_speech
from mlogging import logger
from google.cloud import storage


@dataclass
class VideoTranscriberService:
    url: str
    GCS_BUCKET: str = os.environ["GCS_BUCKET"]

    @cached_property
    def storage_client(self):
        return storage.Client()

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

    def _upload_audio_to_gcs(self, audio_path: str) -> str:
        destination = f"audio-files/{audio_path.split("/")[-1]}"

        bucket = self.storage_client.bucket(self.GCS_BUCKET)
        blob = bucket.blob(destination)
        logger.info("Uploading audio file to gcs")
        if not blob.exists():
            logger.info("Audio file already exists in GCS")
            blob.upload_from_filename(audio_path)

        return f"gs://{bucket.name}/{blob.name}"

    def run(self) -> str:
        audio_path = self._download_audio(video_url=self.url)
        gcs_uri = self._upload_audio_to_gcs(audio_path=audio_path)
        transcriptions = transcribe_speech(gcs_uri=gcs_uri)
        return " ".join(transcriptions)
