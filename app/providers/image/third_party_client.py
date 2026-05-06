import httpx


class ThirdPartyImageClient:
    def __init__(self, base_url, api_key, model_name, api_path="/images/generate", http_client=None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.api_path = api_path
        self.http_client = http_client or httpx.Client(base_url=self.base_url, timeout=60.0, trust_env=False)

    def create_image(self, payload):
        response = self.http_client.post(
            self.api_path,
            headers={"Authorization": "Bearer " + self.api_key},
            json=payload,
        )
        response.raise_for_status()
        return response.json()
