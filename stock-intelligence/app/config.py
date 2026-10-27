"""App config: reads .env, validates provider mode. No secrets in logs."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

VALID_PROVIDERS = ("MOCK", "UPSTOX")


class ConfigError(RuntimeError):
    pass


def get_config():
    provider = os.environ.get("PROVIDER", "MOCK").upper()
    if provider not in VALID_PROVIDERS:
        raise ConfigError(f"PROVIDER must be one of {VALID_PROVIDERS}, got {provider!r}")

    upstox = {
        "api_key": os.environ.get("UPSTOX_API_KEY", "").strip(),
        "api_secret": os.environ.get("UPSTOX_API_SECRET", "").strip(),
        "access_token": os.environ.get("UPSTOX_ACCESS_TOKEN", "").strip(),
        "redirect_uri": os.environ.get("UPSTOX_REDIRECT_URI", "http://127.0.0.1:9090").strip(),
    }

    if provider == "UPSTOX" and not upstox["access_token"]:
        raise ConfigError(
            "UPSTOX mode needs UPSTOX_ACCESS_TOKEN. "
            "Generate one on the Upstox developer dashboard or switch to MOCK."
        )

    return {"provider": provider, "upstox": upstox, "root": ROOT}


def public_config(cfg):
    """Safe subset: no secrets, no tokens."""
    upstox = cfg["upstox"]
    return {
        "provider": cfg["provider"],
        "upstox": {
            "api_key_configured": bool(upstox["api_key"]),
            "access_token_configured": bool(upstox["access_token"]),
        },
    }
