import httpx


class ComfyUIClient:
    def __init__(self, base_url, http_client=None):
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client or httpx.Client(base_url=self.base_url, timeout=60.0, trust_env=False)

    def submit_workflow(self, workflow):
        response = self.http_client.post("/prompt", json={"prompt": workflow})
        response.raise_for_status()
        return response.json()["prompt_id"]

    def get_history(self, prompt_id):
        response = self.http_client.get("/history/{0}".format(prompt_id))
        response.raise_for_status()
        return response.json()

    def download_image(self, filename, subfolder, folder_type):
        response = self.http_client.get(
            "/view",
            params={
                "filename": filename,
                "subfolder": subfolder,
                "type": folder_type,
            },
        )
        response.raise_for_status()
        return response.content
