import argparse

from _bootstrap import ensure_project_root_on_path


ensure_project_root_on_path()

from app.workers.runner import run_worker


def main():
    parser = argparse.ArgumentParser(description="Run or validate the worker entrypoint.")
    parser.add_argument("--check", action="store_true", help="Validate imports only")
    args = parser.parse_args()
    if args.check:
        print("worker entrypoint ok")
        return
    run_worker()

if __name__ == "__main__":
    main()
