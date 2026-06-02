"""Entry point: ``python -m komorebi`` (or the ``komorebi`` console script).

Boots the FastAPI app with config from the environment. Defaults run a fully
working demo with no external services.
"""

from __future__ import annotations

import uvicorn

from .config import Config
from .server import create_app


def main() -> None:
    config = Config.from_env()
    app = create_app(config)
    print(
        f"🌿 Komorebi up on http://{config.host}:{config.port}  "
        f"(llm={config.llm_backend}, tts={config.tts_backend}, "
        f"persona={config.default_persona})"
    )
    uvicorn.run(app, host=config.host, port=config.port, log_level="info")


if __name__ == "__main__":
    main()
