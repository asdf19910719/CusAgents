from pathlib import Path


def main():
    template_root = Path(__file__).resolve().parents[1] / "app" / "templates"
    templates = sorted(str(path.relative_to(template_root)) for path in template_root.rglob("*.j2"))
    for template in templates:
        print("registered", template)


if __name__ == "__main__":
    main()
