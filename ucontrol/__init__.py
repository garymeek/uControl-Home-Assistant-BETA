from __future__ import annotations

import ipaddress
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

import os

from .const import (
    DOMAIN, STORAGE_DIR, CONF_MAPPINGS, CONF_REMOTE_IP,
    CONF_ACTION, CONF_DOMAIN, CONF_SERVICE, CONF_ENTITY_ID,
    BUTTON_LABELS, DEVICE_SPECIFIC_BUTTONS, SEQUENCE_DEVICE_IDS, SEQUENCE_BUTTON_LABELS,
    COMMAND_LOG_MAX,
)

_LOGGER = logging.getLogger(__name__)


def _extract_remote_ip(request: web.Request) -> str | None:
    """Return the best-guess IPv4 address for the caller.

    Checks X-Forwarded-For first (trusting the leftmost address, which is
    the original client when a reverse proxy appends to the header), then
    falls back to the direct connection peer address.  Returns None if no
    valid IPv4 address can be determined.
    """
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        candidate = xff.split(",")[0].strip()
        try:
            addr = ipaddress.IPv4Address(candidate)
            return str(addr)
        except ValueError:
            pass  # not a valid IPv4 — fall through to peer address

    peer = request.transport and request.transport.get_extra_info("peername")
    if peer:
        try:
            addr = ipaddress.IPv4Address(peer[0])
            return str(addr)
        except ValueError:
            pass

    return None


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    # Per-entry rolling command log for diagnostics
    hass.data[DOMAIN].setdefault("command_log", deque(maxlen=COMMAND_LOG_MAX))

    storage_dir = os.path.join(hass.config.config_dir, STORAGE_DIR)
    await hass.async_add_executor_job(lambda: os.makedirs(storage_dir, exist_ok=True))

    if not hass.data[DOMAIN].get("view_registered"):
        hass.http.register_view(UControlIPCommandView)
        hass.data[DOMAIN]["view_registered"] = True
        _LOGGER.debug("Registered uControl IP HTTP view")

    return True


def _log_command(hass: HomeAssistant, record: dict[str, Any]) -> None:
    """Append a command record to the in-memory diagnostic log."""
    log: deque = hass.data[DOMAIN]["command_log"]
    log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **record,
    })


class UControlIPCommandView(HomeAssistantView):
    """HTTP endpoint for uControl IP button presses.

    URL pattern:
        GET /api/command/ip/{device}/{button}

    Each config entry represents one physical remote, identified by its IP
    address.  Incoming requests are matched against registered remote IPs —
    requests from unknown IPs are rejected with 403.  X-Forwarded-For is
    trusted so installations behind a reverse proxy work correctly.

    Devices are numbered from 1.  Standard buttons use the IDs defined in
    BUTTON_LABELS (const.py).  The power buttons are:

        Power On   ->  GET /api/command/ip/{device}/49
        Power Off  ->  GET /api/command/ip/{device}/50

    Sequence devices (IDs 10-13) only expose button 1 (Short Press) and
    button 2 (Long Press).
    """

    url = "/api/command/ip/{device}/{button}"
    name = "api:ucontrol_ip_command"
    requires_auth = False

    async def get(self, request: web.Request, device: str, button: str) -> web.Response:
        hass: HomeAssistant = request.app["hass"]

        # ----------------------------------------------------------------
        # 1. Validate device / button parameters
        # ----------------------------------------------------------------
        try:
            dev_int = int(device)
            btn_int = int(button)
        except ValueError:
            return web.json_response(
                {"header": {"status": 400, "message": "Bad device or button"}},
                status=400,
            )

        if dev_int < 1:
            return web.json_response(
                {"header": {"status": 400, "message": "Device ID must be 1 or greater"}},
                status=400,
            )

        # ----------------------------------------------------------------
        # 2. Identify the calling remote by IP
        # ----------------------------------------------------------------
        caller_ip = _extract_remote_ip(request)
        _LOGGER.debug(
            "uControl IP: request from %s -- device %s, button %s",
            caller_ip, dev_int, btn_int,
        )

        if not caller_ip:
            _LOGGER.warning("uControl IP: could not determine caller IP, rejecting request")
            return web.json_response(
                {"header": {"status": 403, "message": "Could not determine remote IP"}},
                status=403,
            )

        # Find the config entry whose registered IP matches the caller
        matched_entry = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            entry_data: dict[str, Any] = {}
            entry_data.update(entry.data)
            entry_data.update(entry.options or {})
            if entry_data.get(CONF_REMOTE_IP, "") == caller_ip:
                matched_entry = entry
                break

        if matched_entry is None:
            _LOGGER.warning(
                "uControl IP: request from unregistered IP %s rejected", caller_ip
            )
            _log_command(hass, {
                "remote_ip": caller_ip,
                "device_id": dev_int,
                "button_id": btn_int,
                "result": "rejected",
                "reason": "IP not registered",
            })
            return web.json_response(
                {"header": {"status": 403, "message": "Remote IP not registered"}},
                status=403,
            )

        # ----------------------------------------------------------------
        # 3. Look up the button mapping for this entry
        # ----------------------------------------------------------------
        data: dict[str, Any] = {}
        data.update(matched_entry.data)
        data.update(matched_entry.options or {})

        btn_label = (
            SEQUENCE_BUTTON_LABELS.get(btn_int, str(btn_int))
            if dev_int in SEQUENCE_DEVICE_IDS
            else DEVICE_SPECIFIC_BUTTONS.get(dev_int, {}).get(btn_int)
            or BUTTON_LABELS.get(btn_int, str(btn_int))
        )

        mappings: dict[str, dict[str, dict[str, Any]]] = data.get(CONF_MAPPINGS, {})
        dev_map = mappings.get(str(dev_int))
        btn_map = dev_map.get(str(btn_int)) if dev_map else None

        if not btn_map:
            hass.bus.async_fire(
                f"{DOMAIN}_button_press",
                {
                    "remote_ip": caller_ip,
                    "device_id": dev_int,
                    "button_id": btn_int,
                    "button_label": btn_label,
                    "mapped": False,
                },
            )
            _log_command(hass, {
                "remote_ip": caller_ip,
                "device_id": dev_int,
                "button_id": btn_int,
                "button_label": btn_label,
                "result": "unmapped",
            })
            _LOGGER.debug(
                "uControl IP: unmapped press -- remote %s, device %s, button %s (%s)",
                caller_ip, dev_int, btn_int, btn_label,
            )
            return web.json_response(
                {"header": {"status": 404, "message": "Unknown device/button"}},
                status=404,
            )

        domain = btn_map.get(CONF_DOMAIN)
        service = btn_map.get(CONF_SERVICE)
        entity_id = btn_map.get(CONF_ENTITY_ID)

        if not domain or not service or not entity_id:
            return web.json_response(
                {"header": {"status": 404, "message": "Incomplete mapping"}},
                status=404,
            )

        # ----------------------------------------------------------------
        # 4. Fire event and call the mapped service
        # ----------------------------------------------------------------
        raw_action: dict = btn_map.get(CONF_ACTION, {})
        extra_data: dict = raw_action.get("data", {}) if isinstance(raw_action, dict) else {}

        hass.bus.async_fire(
            f"{DOMAIN}_button_press",
            {
                "remote_ip": caller_ip,
                "device_id": dev_int,
                "button_id": btn_int,
                "button_label": btn_label,
                "mapped": True,
                "action": f"{domain}.{service}",
                "entity_id": entity_id,
            },
        )

        try:
            call_data = {"entity_id": entity_id, **extra_data}
            await hass.services.async_call(
                domain,
                service,
                call_data,
                blocking=False,
            )
        except Exception as e:  # noqa: BLE001
            _LOGGER.exception("Service call failed")
            _log_command(hass, {
                "remote_ip": caller_ip,
                "device_id": dev_int,
                "button_id": btn_int,
                "button_label": btn_label,
                "action": f"{domain}.{service}",
                "entity_id": entity_id,
                "result": "error",
                "reason": str(e),
            })
            return web.json_response(
                {"header": {"status": 500, "message": "Service call failed"}, "data": {"error": str(e)}},
                status=500,
            )

        _log_command(hass, {
            "remote_ip": caller_ip,
            "device_id": dev_int,
            "button_id": btn_int,
            "button_label": btn_label,
            "action": f"{domain}.{service}",
            "entity_id": entity_id,
            "result": "ok",
        })
        return web.json_response({"header": {"status": 200, "message": "OK"}})
