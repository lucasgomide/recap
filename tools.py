from typing import Type

from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool

from services import VideoTranscriberService


class VideoTranscriberInput(BaseModel):
    url: str = Field(description="Public video URL")


class VideoTranscriber(BaseTool):
    """Tool that transcribe video or audio on demand"""

    name: str = "video_transcription"
    description: str = (
        "Useful for when you need to transcript a video or audio content."
        "Input should be a URL. "
        "This returns only the transcription - not the original source data."
    )
    args_schema: Type[BaseModel] = VideoTranscriberInput
    service_klass_wrapper: VideoTranscriberService = Field(
        default=VideoTranscriberService
    )

    def _run(self, url: str, **kwargs) -> str:
        """Use the tool."""
        return self.service_klass_wrapper(url=url).run()
