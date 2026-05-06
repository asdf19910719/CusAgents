import httpx

from app.providers.image.comfyui_client import ComfyUIClient


def build_transport():
    def handler(request):
        if request.url.path == "/prompt" and request.method == "POST":
            return httpx.Response(200, json={"prompt_id": "prompt-1"})
        if request.url.path == "/history/prompt-1" and request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "prompt-1": {
                        "status": {"completed": True},
                        "outputs": {
                            "9": {
                                "images": [
                                    {"filename": "shot-1.png", "subfolder": "", "type": "output"}
                                ]
                            }
                        },
                    }
                },
            )
        if request.url.path == "/view" and request.method == "GET":
            return httpx.Response(200, content=b"fake-image")
        raise AssertionError("unexpected request: {0} {1}".format(request.method, request.url))

    return httpx.MockTransport(handler)


def test_comfyui_client_submits_workflow_and_returns_prompt_id():
    client = ComfyUIClient(
        base_url="http://127.0.0.1:8188",
        http_client=httpx.Client(transport=build_transport(), base_url="http://127.0.0.1:8188"),
    )

    prompt_id = client.submit_workflow({"nodes": []})

    assert prompt_id == "prompt-1"


def test_comfyui_client_reads_status_and_downloads_image():
    client = ComfyUIClient(
        base_url="http://127.0.0.1:8188",
        http_client=httpx.Client(transport=build_transport(), base_url="http://127.0.0.1:8188"),
    )

    history = client.get_history("prompt-1")
    image_bytes = client.download_image("shot-1.png", "", "output")

    assert history["prompt-1"]["status"]["completed"] is True
    assert image_bytes == b"fake-image"
