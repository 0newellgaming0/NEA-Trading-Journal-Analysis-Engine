import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from publisher.publication_engine import PublicationEngine
from publisher.validator import validate_data


OUTPUT_DIR = ROOT / "data"


if __name__ == "__main__":
    PublicationEngine(OUTPUT_DIR).publish()
    validate_data(OUTPUT_DIR)

    print(
        f"Published public trade data to {OUTPUT_DIR}"
    )
