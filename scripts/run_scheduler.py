import argparse

from _bootstrap import ensure_project_root_on_path


ensure_project_root_on_path()

from app.workers.scheduler import run_scheduler


def main():
    parser = argparse.ArgumentParser(description="Run or validate the scheduler entrypoint.")
    parser.add_argument("--check", action="store_true", help="Validate imports only")
    args = parser.parse_args()
    if args.check:
        print("scheduler entrypoint ok")
        return
    run_scheduler()


if __name__ == "__main__":
    main()
