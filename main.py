import asyncio
import io
import os
import base64
import zipfile
import threading
import time

import zmq
from pypdf import PdfReader
from llama_models.llama3.api import UserMessage
from llama_stack.apis.inference import ChatCompletionRequest, SamplingParams
from llama_stack.apis.inference.client import InferenceClient

from server import serve

ENDPOINT = "tcp://127.0.0.1:5557"
LLAMA_STACK_URL = "http://localhost:5000"
MODEL = "stories15M-q8_0"
NUM_PROMPTS = 100


def decode_audio(transcript):
    raw = base64.b64decode(transcript)
    zf = zipfile.ZipFile(io.BytesIO(raw))
    names = zf.namelist()
    if not names:
        raise ValueError("Empty archive")
    return zf.read(names[0])


def extract_text(pdf_bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()


async def run_inference(client, prompt_text):
    message = UserMessage(content=prompt_text)
    result_text = ""
    async for response in client.chat_completion(
        model=MODEL,
        messages=[message],
        sampling_params=SamplingParams(),
        stream=False,
    ):
        if hasattr(response, "completion_message"):
            result_text = response.completion_message.content
    return result_text


async def main():
    broker = threading.Thread(target=serve, daemon=True)
    broker.start()
    time.sleep(1)

    ctx = zmq.Context()
    sock = ctx.socket(zmq.PULL)
    sock.connect(ENDPOINT)

    client = InferenceClient(LLAMA_STACK_URL)
    print(f"\nWorker connected to {ENDPOINT}")
    print(f"Inference target: {LLAMA_STACK_URL} ({MODEL})\n")

    results = []
    for i in range(NUM_PROMPTS):
        prompt_obj = sock.recv_pyobj()
        prompt_id = prompt_obj.get("id", i + 1)
        transcript = prompt_obj.get("transcript", "")

        pdf_bytes = decode_audio(transcript)
        text = extract_text(pdf_bytes)

        try:
            answer = await run_inference(client, text)
        except Exception:
            answer = ""

        results.append({"id": prompt_id, "prompt": text[:80], "answer": answer[:80]})
        print(f"  [{i+1:03d}] id={prompt_id} prompt={text[:60]}")

    print(f"\nProcessed {len(results)} prompts.")

    sock.close()
    ctx.term()


if __name__ == "__main__":
    asyncio.run(main())
