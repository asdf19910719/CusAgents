import argparse
import time

import httpx


def main():
    parser = argparse.ArgumentParser(description="Submit a demo Custom Agents job and poll its status.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--topic", default="冷血剑客复仇", help="Generation topic")
    parser.add_argument("--style", default="cinematic", help="Style preset")
    parser.add_argument("--shots", type=int, default=3, help="Target shot count")
    parser.add_argument(
        "--image-backend",
        default="comfyui_remote",
        choices=["comfyui_remote", "third_party", "codex_cli", "chatgpt_web", "dreamina_cli"],
        help="Image backend to use for this job",
    )
    parser.add_argument("--poll-interval", type=float, default=1.0, help="Polling interval in seconds")
    parser.add_argument("--max-polls", type=int, default=10, help="Maximum polling attempts")
    args = parser.parse_args()

    with httpx.Client(base_url=args.base_url, timeout=10.0, trust_env=False) as client:
        create_response = client.post(
            "/jobs",
            json={
                "topic": args.topic,
                "style_preset": args.style,
                "target_shot_count": args.shots,
                "image_backend": args.image_backend,
            },
        )
        create_response.raise_for_status()
        job = create_response.json()
        job_id = job["id"]
        print("Created job:", job_id)

        for _ in range(args.max_polls):
            status_response = client.get("/jobs/{0}".format(job_id))
            status_response.raise_for_status()
            payload = status_response.json()
            print("Status:", payload["status"], "Current step:", payload["current_step"])
            if payload["status"] in ("completed", "failed", "cancelled", "waiting_review"):
                break
            time.sleep(args.poll_interval)

        assets_response = client.get("/jobs/{0}/assets".format(job_id))
        if assets_response.status_code == 200:
            print("Assets:", assets_response.json())


if __name__ == "__main__":
    main()
