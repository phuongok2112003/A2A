from __future__ import annotations

import subprocess
import time
import requests
from dataclasses import dataclass
from typing import Optional
from config.settings import settings


NGROK_API = "http://127.0.0.1:4040/api/tunnels"


@dataclass
class NgrokTunnel:
    pid: int
    public_url: str
    proto: str
    local_port: int


def start_ngrok_and_get_url(
    port: int,
    timeout: int = 15,
) -> NgrokTunnel:
    """
    Start ngrok tunnel and wait until public URL is available.

    Requires:
    - ngrok installed
    - auth token configured
    """

    proc = subprocess.Popen(
        ["ngrok", "http", f"127.0.0.1:{port}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    start = time.monotonic()

    while time.monotonic() - start < timeout:
        try:
            resp = requests.get(NGROK_API, timeout=2)
            resp.raise_for_status()

            data = resp.json()

            tunnels = data.get("tunnels", [])

            if tunnels:
                t = tunnels[0]
                print(f"Public url ngrok {t["public_url"]}")

                return NgrokTunnel(
                    pid=proc.pid,
                    public_url=t["public_url"],
                    proto=t.get("proto", ""),
                    local_port=port,
                )

        except Exception:
            time.sleep(0.5)

    proc.terminate()
    raise RuntimeError("Ngrok did not expose a tunnel in time")


ngrok_tunel_zalo_bot_webhook: NgrokTunnel | None = None

async def init_ngrok(port: int) -> str:
    global ngrok_tunel_zalo_bot_webhook

    if ngrok_tunel_zalo_bot_webhook:
        return ngrok_tunel_zalo_bot_webhook

    ngrok_tunel_zalo_bot_webhook = start_ngrok_and_get_url(port)
    return ngrok_tunel_zalo_bot_webhook.public_url

