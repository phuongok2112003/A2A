import json
import subprocess
from typing import Any, Dict, List


def get_tailscale_summary() -> Dict[str, Any]:
    result = subprocess.run(
        ["tailscale", "status", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)

    self_info = data.get("Self", {})
    peers = data.get("Peer", {})

    current_machine = {
        "hostname": self_info.get("HostName"),
        "os": self_info.get("OS"),
        "ip": (self_info.get("TailscaleIPs") or [None])[0],
        "online": self_info.get("Online"),
        "active": self_info.get("Active"),
    }

    important_peers: List[Dict[str, Any]] = []

    for peer in peers.values():
        important_peers.append(
            {
                "hostname": peer.get("HostName"),
                "os": peer.get("OS"),
                "ip": (peer.get("TailscaleIPs") or [None])[0],
                "online": peer.get("Online"),
                "active": peer.get("Active"),
                "connection": "direct" if peer.get("CurAddr") else "relay/offline",
                "current_address": peer.get("CurAddr") or None,
            }
        )

    return {
        "current_machine": current_machine,
        "peers": important_peers,
    }


if __name__ == "__main__":
    status = get_tailscale_summary()
    print(json.dumps(status, indent=2, ensure_ascii=False))