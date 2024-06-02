from mlogging import logger

from google.cloud import speech

client = speech.SpeechClient()

AUDIO_CHANNEL_COUNT = 2
SAMPLE_RATE_HERTZ = 48000
TIMEOUT_IN_SECONDS = 30 * 60

def transcribe_speech(gcs_uri: str):
    audio = speech.RecognitionAudio(uri=gcs_uri)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=SAMPLE_RATE_HERTZ,
        language_code="pt-BR",
        model="latest_long",
        audio_channel_count=AUDIO_CHANNEL_COUNT,
    )

    operation = client.long_running_recognize(config=config, audio=audio)
    operation_elapsed_time = 0
    logger.info("Waiting for transcription to be completed...")
    response = operation.result(timeout=TIMEOUT_IN_SECONDS)

    transcriptions = []
    for result in response.results:
        operation_elapsed_time += result.result_end_time.seconds
        transcriptions.append(result.alternatives[0].transcript)
    logger.info(f"Transcription completed in {operation_elapsed_time} seconds")
    return transcriptions
