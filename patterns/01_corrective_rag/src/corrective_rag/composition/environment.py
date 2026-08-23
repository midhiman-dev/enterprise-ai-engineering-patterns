"""Developer-Local Environment Variable Bootstrap.

Loads environment variables from a developer-local `.env` file into process environment.
Acts as an outer runtime bootstrap concern, keeping provider configurations decoupled from `.env` logic.
"""

from pathlib import Path
from dotenv import load_dotenv


def load_local_environment(dotenv_path: Path | str | None = None) -> None:
    """Loads local `.env` configuration into standard process environment (`os.environ`).

    Host and deployment environment variables take precedence over `.env` (`override=False`).
    A missing `.env` file is handled gracefully without error.

    Args:
        dotenv_path: Optional explicit path to `.env` file. If None, defaults to the
                     canonical `patterns/01_corrective_rag/.env` file.

    Raises:
        RuntimeError: If an existing `.env` file cannot be parsed or loaded.
    """
    if dotenv_path is None:
        target_path = Path(__file__).resolve().parents[3] / ".env"
    else:
        target_path = Path(dotenv_path)

    if not target_path.exists():
        return

    try:
        load_dotenv(dotenv_path=target_path, override=False)
    except Exception as exc:
        raise RuntimeError(f"Failed to parse local environment file at {target_path}.") from exc
