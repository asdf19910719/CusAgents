class DreaminaTaskRecoveryService:
    def __init__(self, client):
        self.client = client

    def query_submit_id(self, submit_id, download_dir=None):
        return self.client.query_result(submit_id=submit_id, download_dir=download_dir)
