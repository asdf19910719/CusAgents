from pathlib import Path


class BrowserProfileManager:
    def __init__(self, profile_dir):
        self.profile_dir = Path(profile_dir)

    def ensure_profile_dir(self):
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        return self.profile_dir

    def get_download_dir(self):
        download_dir = self.profile_dir.parent / "downloads" / self.profile_dir.name
        download_dir.mkdir(parents=True, exist_ok=True)
        return download_dir
