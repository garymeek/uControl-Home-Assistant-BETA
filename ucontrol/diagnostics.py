"""Diagnostics for uControl IP Bridge.

Accessible via: Settings → Devices & Services → uControl IP → Download Diagnostics.

The download contains:
  - Integration configuration (remote IP, device count, mapped button count)
  - Last 50 received commands (timestamp, remote IP, device, button, result)

Sensitive values (entity IDs, service names) are included because this
data never leaves the local HA instance unless the user explicitly shares it.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_REMOTE_IP, CONF_NUM_DEVICES, CONF_MAPPINGS


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    base: dict[str, Any] = dict(entry.data)
    base.update(entry.options or {})

    mappings: dict = base.get(CONF_MAPPINGS, {})
    mapped_count = sum(len(btns) for btns in mappings.values())

    # Build a concise summary of what's mapped (button label -> action)
    mapped_summary: list[dict[str, str]] = []
    for d_str, btns in sorted(mappings.items(), key=lambda x: int(x[0])):
        for b_str, btn_map in sorted(btns.items(), key=lambda x: int(x[0])):
            mapped_summary.append({
                "device": d_str,
                "button_id": b_str,
                "action": f"{btn_map.get('domain', '?')}.{btn_map.get('service', '?')}",
                "entity_id": btn_map.get("entity_id", ""),
            })

    # Pull the shared command log — filter to only entries for this entry's IP
    remote_ip: str = base.get(CONF_REMOTE_IP, "")
    command_log: deque = hass.data.get(DOMAIN, {}).get("command_log", deque())
    entry_log = [
        record for record in command_log
        if record.get("remote_ip") == remote_ip or record.get("result") == "rejected"
    ]

    return {
        "config": {
            "remote_ip": remote_ip,
            "num_devices": base.get(CONF_NUM_DEVICES, 1),
            "mapped_button_count": mapped_count,
        },
        "mapped_buttons": mapped_summary,
        "command_log": list(entry_log),
    }
