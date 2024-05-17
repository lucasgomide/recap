from mlogging import logger

from google.cloud import speech

client = speech.SpeechClient()


def transcribe_speech(gcs_uri: str):
    audio = speech.RecognitionAudio(uri=gcs_uri)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=48000,
        language_code="pt-BR",
        model="latest_long",
        audio_channel_count=2,
    )

    operation = client.long_running_recognize(config=config, audio=audio)

    logger.info("Waiting for transcription to be completed...")
    response = operation.result(timeout=90)
    logger.info("Transcription completed")

    transcriptions = []
    for result in response.results:
        transcriptions.append(result.alternatives[0].transcript)
    return transcriptions
