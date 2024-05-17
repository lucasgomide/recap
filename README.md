# Recap

Recap is an app built to transcribe and summarize video content.

It uses Speech-to-Text to convert audio into text and Gemini as the LLM (Language Model) to summarize the audio content. Additionally, Google Cloud Storage is used to store the processed audio files.

The summarization process is quite simple. First, we extract the audio from the requested video using `youtube-dl`, which supports a large number of video providers. After that, we call Speech-to-Text to transcribe the audio into text. Finally, we use Gemini to summarize the transcription for us.


# What's next

- Make Cloud Storage optional by enabling processing files locally
- Support others LLM's
- Support others models to transcribe audio into text
- Use proper models (faster & more efficient) for audio files less than 60 seconds
- Add tests

# Pre-requisits
The following environment variables are required:

```shell
GOOGLE_APPLICATION_CREDENTIALS # required to access Cloud Storage & Cloud Speech
GOOGLE_API_KEY # required for Gemini
GCS_BUCKET # required to store audio extracted from video
```

You will also need to grant the following roles in your IAM:
- Cloud Speech Administrator
- Storage Object Viewer

# Usage

To run the application, use the following command:


```shell
$ poetry run python -m recap <VIDEO_URL>
```

# Estimated Costs
Check out the pricing for the tools used:
[Speech-to-Text](https://cloud.google.com/speech-to-text/pricing) & [Gemini Pro](https://ai.google.dev/pricing?hl=pt-br)

