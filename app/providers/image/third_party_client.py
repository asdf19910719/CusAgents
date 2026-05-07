import httpx


class ThirdPartyImageClient:
    def __init__(
        self,
        base_url,
        api_key,
        model_name,
        api_path="/images/generate",
        http_client=None,
        timeout_seconds=180.0,
        retry_attempts=1,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.api_path = api_path
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = max(0, int(retry_attempts))
        self.http_client = http_client or httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            trust_env=False,
        )

    def create_image(self, payload):
        last_error = None
        for attempt in range(self.retry_attempts + 1):
            try:
                response = self.http_client.post(
                    self.api_path,
                    headers={"Authorization": "Bearer " + self.api_key},
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except httpx.ReadTimeout as exc:
                last_error = exc
                if attempt >= self.retry_attempts:
                    raise
        raise last_error
