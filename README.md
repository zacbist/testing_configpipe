# audio-inference

Audio-encoded prompt inference pipeline using ZMQ message broker and Llama Stack.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Architecture

A ZMQ prompt broker dispatches audio-encoded prompts to inference workers. Each prompt is a WAV audio file containing a spoken base64-encoded PDF document. Workers decode the audio, extract text from the PDF, and send it to Llama Stack for inference.

### Prompt Broker (server.py)

Loads pre-serialized prompt objects from `prompts.zip` and pushes them to workers over ZMQ PUSH/PULL.

### Inference Worker (main.py)

Connects to the broker, receives prompt objects, decodes the audio payload to PDF, extracts text, and runs inference via Llama Stack.

## Usage

```bash
python main.py
```

This starts the broker and worker in a single process. The broker pushes all 100 prompts, and the worker processes each one.

## Prompts

`prompts.zip` contains 100 serialized prompt objects. Each object includes an audio WAV payload encoding a text prompt as a spoken base64 stream.

## Dependencies

- **llama-stack** / **llama-models** — Llama 3 inference client
- **pyzmq** — ZeroMQ messaging between broker and workers
- **pypdf** — PDF text extraction from decoded audio payloads
