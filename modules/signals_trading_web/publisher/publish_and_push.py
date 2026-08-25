import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from modules.signals_trading_web.publisher.publication_engine import (
    PublicationEngine
)
from modules.signals_trading_web.publisher.validator import (
    validate_data
)


OUTPUT_DIR = (
    ROOT /
    "modules" /
    "signals_trading_web" /
    "data"
)


PUBLIC_FILES = [
    "modules/signals_trading_web/data/trades.json",
    "modules/signals_trading_web/data/performance.json",
    "modules/signals_trading_web/data/market.json",
    "modules/signals_trading_web/data/analysis_latest.json",
]


def run_git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True
    )

    if result.returncode != 0:
        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr)

        raise RuntimeError(
            f"Git command failed: git {' '.join(args)}"
        )

    return result.stdout.strip()


def verify_repository():
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=ROOT,
        text=True,
        capture_output=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Publishing aborted: repository root could not be verified."
        )

    repository_root = Path(
        result.stdout.strip()
    ).resolve()

    if repository_root != ROOT.resolve():
        raise RuntimeError(
            "Publishing aborted: repository root does not match ROOT."
        )


def verify_no_database_staged():
    staged = run_git(
        "diff",
        "--cached",
        "--name-only"
    )

    if not staged:
        return

    database_files = []

    for filename in staged.splitlines():
        lowered = filename.lower()

        if (
            lowered.endswith(".db")
            or lowered.endswith(".sqlite")
            or lowered.endswith(".sqlite3")
        ):
            database_files.append(filename)

    if database_files:
        run_git("reset", "--", *PUBLIC_FILES)

        raise RuntimeError(
            "Publishing aborted: database files are staged:\n"
            + "\n".join(database_files)
        )


def stage_public_files():
    run_git(
        "add",
        "--",
        *PUBLIC_FILES
    )


def get_public_changes():
    return run_git(
        "status",
        "--short",
        "--",
        *PUBLIC_FILES
    )


def publish():
    print("========================================")
    print("PUBLIC TRADE DATA PUBLISH")
    print("========================================")

    verify_repository()

    print("Generating public JSON from authoritative DB...")

    PublicationEngine(
        OUTPUT_DIR
    ).publish()

    print("Validating generated JSON...")

    validate_data(
        OUTPUT_DIR
    )

    print("Public JSON validated.")

    stage_public_files()

    verify_no_database_staged()

    changes = get_public_changes()

    if not changes:
        print("No public JSON changes detected.")
        print("Nothing to commit or push.")
        return False

    print("Public JSON changes detected:")
    print(changes)

    run_git(
        "commit",
        "-m",
        "Publish current trading data"
    )

    print("Public trading data committed.")

    run_git(
        "push",
        "origin",
        "HEAD"
    )

    print("Public trading data pushed to GitHub.")

    return True


def main():
    try:
        publish()
    except Exception as exc:
        print(
            f"PUBLICATION FAILED: {exc}",
            file=sys.stderr
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
