import os
import youtube_dl
from speech import transcribe_speech
from mlogging import logger
import click


def download_audio(video_url: str):
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


def upload_audio_to_gcs(audio_path: str):
    from google.cloud import storage

    destination = f"audio-files/{audio_path.split("/")[-1]}"
    storage_client = storage.Client()
    bucket = storage_client.bucket(os.environ["GCS_BUCKET"])
    blob = bucket.blob(destination)
    logger.info("Uploading audio file to gcs")
    if not blob.exists():
        logger.info("Audio file already exists in GCS")
        blob.upload_from_filename(audio_path)

    return f"gs://{bucket.name}/{blob.name}"


def generate_summary(transcription: str):
    from langchain_core.prompts import PromptTemplate
    from langchain_google_genai import GoogleGenerativeAI

    template = """
    Com base na transcrição abaixo você precisa resumir as reuniões.
    Foque nos principais pontos abordados, polêmicas e/ou discussões que foram realmente relevantes.
    Transcrição: {transcription}
    """
    prompt = PromptTemplate.from_template(template)

    llm = GoogleGenerativeAI(model="gemini-pro", temperature=0)
    llm_chain = prompt | llm
    logger.info("Generating summary for transcription")
    return llm_chain.invoke({"transcription": transcription})

@click.command()
@click.argument('video_url')
def run(video_url: str):
    audio_path = download_audio(video_url=video_url)
    gcs_uri = upload_audio_to_gcs(audio_path=audio_path)
    transcriptions = transcribe_speech(gcs_uri=gcs_uri)
    tldr = generate_summary(transcription=" ".join(transcriptions))
    print(tldr)

if __name__ == '__main__':
    run()
