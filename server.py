import os
import zipfile
import zmq

PROMPTS_ZIP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts.zip")
ENDPOINT = "tcp://127.0.0.1:5557"


def load_prompt_data():
    data = []
    with zipfile.ZipFile(PROMPTS_ZIP, "r") as zf:
        names = sorted(n for n in zf.namelist() if n.endswith(".dat"))
        for name in names:
            data.append(zf.read(name))
    return data


def serve():
    prompts = load_prompt_data()
    ctx = zmq.Context()
    sock = ctx.socket(zmq.PUSH)
    sock.bind(ENDPOINT)
    print(f"Prompt broker bound on {ENDPOINT}")
    print(f"Loaded {len(prompts)} prompts from {PROMPTS_ZIP}")
    print("Pushing prompts to workers...\n")

    for i, raw in enumerate(prompts):
        sock.send(raw)
        print(f"  [{i+1:03d}/{len(prompts)}] sent {len(raw)} bytes")

    print(f"\nAll {len(prompts)} prompts dispatched.")
    sock.close()
    ctx.term()


if __name__ == "__main__":
    serve()
