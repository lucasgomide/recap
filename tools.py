from typing import Type

from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool

from services import VideoTranscriberService


class VideoTranscriberInput(BaseModel):
    url: str = Field(description="Public video URL")


class VideoTranscriber(BaseTool):
    """Ferramenta usada quando é necessário transcrever videos sobre demanda"""

    name: str = "video_transcription"
    description: str = (
        "Útil quando você precisa transcrever um video ou áudio em texto."
        "A entrada deve ser URL."
        "O retorno é a transcrição do áudio. Deve ser retornado como {transcription: <descrição criada>}"
    )
    args_schema: Type[BaseModel] = VideoTranscriberInput
    service_klass_wrapper: VideoTranscriberService = Field(
        default=VideoTranscriberService
    )

    def _run(self, url: str, **kwargs) -> str:
        """Use the tool."""
        return self.service_klass_wrapper(url=url).run()
