from __future__ import annotations

import ipaddress
import os
from typing import Any

import voluptuous as vol
import yaml

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    ActionSelector,
    ActionSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    DOMAIN,
    STORAGE_DIR,
    IMPORT_MODE_REPLACE,
    IMPORT_MODE_MERGE,
    CONF_REMOTE_IP,
    CONF_NUM_DEVICES,
    CONF_MAPPINGS,
    CONF_ACTION,
    CONF_DOMAIN,
    CONF_SERVICE,
    CONF_ENTITY_ID,
    BUTTON_IDS,
    BUTTON_LABELS,
    DEVICE_SPECIFIC_BUTTONS,
    SEQUENCE_DEVICE_IDS,
    SEQUENCE_BUTTON_IDS,
    SEQUENCE_BUTTON_LABELS,
)


def _resolve_label(d_str: str, b_str: str) -> str:
    """Return a consistent human-readable label for a device/button pair."""
    d_int = int(d_str)
    b_int = int(b_str)
    if d_int in SEQUENCE_DEVICE_IDS:
        btn_label = "Long" if b_int == 2 else "Short"
        return f"Sequence {d_int - 9} {btn_label}"
    btn_label = DEVICE_SPECIFIC_BUTTONS.get(d_int, {}).get(b_int) or BUTTON_LABELS.get(b_int, b_str)
    return f"Device {d_str} – {btn_label} (ID {b_str})"


def _storage_path(hass_config_path: str) -> str:
    """Return absolute path to the storage directory."""
    return os.path.join(hass_config_path, STORAGE_DIR)


def _ensure_storage_dir(hass_config_path: str) -> str:
    """Create storage directory if it doesn't exist. Returns the path."""
    path = _storage_path(hass_config_path)
    os.makedirs(path, exist_ok=True)
    return path


def _build_export_yaml(mappings: dict) -> str:
    """
    Serialise mappings to a YAML string with human-readable comments.

    Example output:
        # Device 1 – Vol+ (ID 26)
        "1":
          "26":
            domain: media_player
            service: volume_up
            entity_id: media_player.living_room_tv
    """
    lines: list[str] = [
        "# uControl IP – button mappings export",
        "# Edit freely; import this file back via the integration options.",
        "",
        "mappings:",
    ]

    for d_str, btns in sorted(mappings.items(), key=lambda x: int(x[0])):
        # Emit device key once, then all buttons nested beneath it
        lines.append(f'  "{d_str}":')
        for b_str, mapping in sorted(btns.items(), key=lambda x: int(x[0])):
            label = _resolve_label(d_str, b_str)
            lines.append(f"    # {label}")
            lines.append(f'    "{b_str}":')
            lines.append(f"      domain: {mapping.get(CONF_DOMAIN, '')}")
            lines.append(f"      service: {mapping.get(CONF_SERVICE, '')}")
            lines.append(f"      entity_id: {mapping.get(CONF_ENTITY_ID, '')}")
            # Preserve the raw action blob so a re-imported file round-trips cleanly
            raw_action = mapping.get(CONF_ACTION)
            if raw_action:
                action_yaml = yaml.dump(
                    {"action": raw_action},
                    default_flow_style=False,
                    allow_unicode=True,
                ).strip()
                for action_line in action_yaml.splitlines():
                    lines.append(f"      {action_line}")
            lines.append("")

    return "\n".join(lines)


def _load_yaml_mappings(filepath: str) -> dict:
    """Load and return the mappings dict from a YAML export file."""
    with open(filepath, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict) or "mappings" not in data:
        raise ValueError("YAML file does not contain a 'mappings' key")

    raw: dict = data["mappings"]
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for d_key, btns in raw.items():
        d_str = str(d_key)
        if not isinstance(btns, dict):
            continue
        for b_key, mapping in btns.items():
            b_str = str(b_key)
            if not isinstance(mapping, dict):
                continue
            result.setdefault(d_str, {})[b_str] = {
                CONF_DOMAIN: mapping.get("domain", ""),
                CONF_SERVICE: mapping.get("service", ""),
                CONF_ENTITY_ID: mapping.get("entity_id", ""),
                CONF_ACTION: mapping.get("action", {}),
            }

    return result


# ---------------------------------------------------------------------------
# Config flow (initial setup — unchanged)
# ---------------------------------------------------------------------------

class UControlIPConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            raw_ip = user_input.get(CONF_REMOTE_IP, "").strip()

            # Validate IPv4 format
            try:
                ipaddress.IPv4Address(raw_ip)
            except ValueError:
                errors[CONF_REMOTE_IP] = "invalid_ip"

            # Reject duplicate IPs across existing entries
            if not errors:
                for entry in self._async_current_entries():
                    existing_ip = entry.data.get(CONF_REMOTE_IP, "")
                    if existing_ip == raw_ip:
                        errors[CONF_REMOTE_IP] = "ip_already_configured"
                        break

            if not errors:
                return self.async_create_entry(
                    title=f"uControl IP – {raw_ip}",
                    data={
                        CONF_REMOTE_IP: raw_ip,
                        CONF_NUM_DEVICES: int(user_input[CONF_NUM_DEVICES]),
                        CONF_MAPPINGS: {},
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_REMOTE_IP): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Required(CONF_NUM_DEVICES, default=1): vol.All(
                    int, vol.Range(min=1, max=16)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return UControlIPOptionsFlowHandler()


# ---------------------------------------------------------------------------
# Options flow
# ---------------------------------------------------------------------------

class UControlIPOptionsFlowHandler(config_entries.OptionsFlow):
    """
    Options flow steps:
      init           – menu: configure buttons / export / import
      map            – map chosen buttons to actions
      export         – enter filename, write YAML
      import         – pick a YAML file
      import_confirm – choose replace or merge, then apply
    """

    def __init__(self) -> None:
        self._selected: list[str] = []
        self._num_devices: int = 1  # overwritten in async_step_init from entry data
        self._remote_ip: str = ""   # overwritten in async_step_init from entry data
        self._import_filename: str = ""
        self._edit_button: str = ""

    @property
    def _entry(self) -> config_entries.ConfigEntry:
        return self.config_entry

    def _current_num_devices(self) -> int:
        """Return num_devices from the live entry, falling back to the cached value."""
        base = dict(self._entry.data)
        base.update(self._entry.options or {})
        return int(base.get(CONF_NUM_DEVICES, self._num_devices))

    def _current_remote_ip(self) -> str:
        """Return remote_ip from the live entry, falling back to the cached value."""
        base = dict(self._entry.data)
        base.update(self._entry.options or {})
        return base.get(CONF_REMOTE_IP, self._remote_ip)

    # ------------------------------------------------------------------
    # Step: init — top-level menu
    # ------------------------------------------------------------------

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        entry = self._entry
        base = dict(entry.data)
        base.update(entry.options or {})

        current_num_devices: int = int(base.get(CONF_NUM_DEVICES, 1))
        current_mappings: dict = base.get(CONF_MAPPINGS, {})
        current_remote_ip: str = base.get(CONF_REMOTE_IP, "")

        default_selected: list[str] = [
            f"{d_str}:{b_str}"
            for d_str, btns in (current_mappings or {}).items()
            for b_str in btns.keys()
        ]

        options: list[str] = []
        option_labels: dict[str, str] = {}
        for d in range(1, current_num_devices + 1):
            for b in BUTTON_IDS:
                key = f"{d}:{b}"
                options.append(key)
                option_labels[key] = f"Device {d} – {BUTTON_LABELS.get(b, str(b))} (ID {b})"
            for b, label in DEVICE_SPECIFIC_BUTTONS.get(d, {}).items():
                key = f"{d}:{b}"
                options.append(key)
                option_labels[key] = f"Device {d} – {label} (ID {b})"
        for d in SEQUENCE_DEVICE_IDS:
            for b in SEQUENCE_BUTTON_IDS:
                key = f"{d}:{b}"
                options.append(key)
                option_labels[key] = f"Sequence {d - 9} {'Long' if b == 2 else 'Short'}"

        buttons_selector = SelectSelector(
            SelectSelectorConfig(
                options=[{"value": k, "label": option_labels[k]} for k in options],
                multiple=True,
                mode="dropdown",
            )
        )

        action_selector_menu = SelectSelector(
            SelectSelectorConfig(
                options=[
                    {"value": "map", "label": "Configure button mappings"},
                    {"value": "edit", "label": "Edit a single button mapping"},
                    {"value": "export", "label": "Export mappings to YAML"},
                    {"value": "import", "label": "Import mappings from YAML"},
                ],
                multiple=False,
                mode="list",
            )
        )

        if user_input is not None:
            action = user_input.get("action_choice", "map")
            self._num_devices = int(user_input[CONF_NUM_DEVICES])

            # Validate the IP field
            new_ip = user_input.get(CONF_REMOTE_IP, "").strip()
            errors: dict[str, str] = {}
            try:
                ipaddress.IPv4Address(new_ip)
            except ValueError:
                errors[CONF_REMOTE_IP] = "invalid_ip"

            if not errors and new_ip != current_remote_ip:
                for other in self.hass.config_entries.async_entries(DOMAIN):
                    if other.entry_id == entry.entry_id:
                        continue
                    other_base = dict(other.data)
                    other_base.update(other.options or {})
                    if other_base.get(CONF_REMOTE_IP, "") == new_ip:
                        errors[CONF_REMOTE_IP] = "ip_already_configured"
                        break

            if errors:
                # Re-render the form with the error
                pass
            else:
                # Persist the (possibly updated) IP back into options
                self._remote_ip = new_ip

                selected = user_input.get("buttons")
                if isinstance(selected, list):
                    self._selected = selected
                elif isinstance(selected, str):
                    parts = [p.strip() for p in selected.replace("\n", ",").split(",")]
                    self._selected = [p for p in parts if p]
                else:
                    self._selected = []

                if action == "export":
                    return await self.async_step_export()
                if action == "import":
                    return await self.async_step_import()
                if action == "edit":
                    return await self.async_step_edit_select()
                return await self.async_step_map()

        errors: dict[str, str] = {}

        schema = vol.Schema(
            {
                vol.Required(CONF_REMOTE_IP, default=current_remote_ip): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Required(CONF_NUM_DEVICES, default=current_num_devices): vol.All(
                    int, vol.Range(min=1, max=16)
                ),
                vol.Optional("buttons", default=default_selected): buttons_selector,
                vol.Required("action_choice", default="map"): action_selector_menu,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)

    # ------------------------------------------------------------------
    # Step: map — unchanged from original
    # ------------------------------------------------------------------

    async def async_step_map(self, user_input: dict[str, Any] | None = None):
        entry = self._entry
        base = dict(entry.data)
        base.update(entry.options or {})

        current_mappings: dict = base.get(CONF_MAPPINGS, {})
        action_selector = ActionSelector(ActionSelectorConfig())
        errors: dict[str, str] = {}

        if user_input is not None:
            # Start with a deep copy of all existing mappings so unselected
            # buttons are preserved rather than silently dropped.
            new_mappings: dict[str, dict[str, dict[str, Any]]] = {
                d: dict(btns) for d, btns in current_mappings.items()
            }

            for key in self._selected:
                if ":" not in key:
                    continue
                d_str, b_str = key.split(":", 1)
                existing = (current_mappings.get(d_str, {}) or {}).get(b_str, {})
                base_label = _resolve_label(d_str, b_str)

                if existing.get(CONF_DOMAIN) and existing.get(CONF_SERVICE):
                    current = f"{existing[CONF_DOMAIN]}.{existing[CONF_SERVICE]}"
                    if existing.get(CONF_ENTITY_ID):
                        current = f"{current} → {existing[CONF_ENTITY_ID]}"
                    field = f"{base_label} (current: {current})"
                else:
                    field = base_label

                action: Any = user_input.get(field)
                if isinstance(action, list):
                    action = action[0] if action else None

                if not action or not isinstance(action, dict):
                    if existing:
                        new_mappings.setdefault(d_str, {})[b_str] = existing
                    continue

                action_str: str = action.get("action", "")
                if not action_str or "." not in action_str:
                    errors["base"] = "invalid_action"
                    break

                svc_domain, svc_name = action_str.split(".", 1)
                target: dict[str, Any] = action.get("target", {})
                entity_id: str = ""
                if isinstance(target.get("entity_id"), list):
                    entity_id = target["entity_id"][0]
                elif isinstance(target.get("entity_id"), str):
                    entity_id = target["entity_id"]

                new_mappings.setdefault(d_str, {})[b_str] = {
                    CONF_ACTION: action,
                    CONF_DOMAIN: svc_domain.strip(),
                    CONF_SERVICE: svc_name.strip(),
                    CONF_ENTITY_ID: entity_id,
                }

            if not errors:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_REMOTE_IP: self._current_remote_ip(),
                        CONF_NUM_DEVICES: self._num_devices,
                        CONF_MAPPINGS: new_mappings,
                    },
                )

        schema_fields: dict[Any, Any] = {}
        for key in self._selected:
            if ":" not in key:
                continue
            d_str, b_str = key.split(":", 1)
            existing = (current_mappings.get(d_str, {}) or {}).get(b_str, {})
            base_label = _resolve_label(d_str, b_str)

            if existing.get(CONF_DOMAIN) and existing.get(CONF_SERVICE):
                current = f"{existing[CONF_DOMAIN]}.{existing[CONF_SERVICE]}"
                if existing.get(CONF_ENTITY_ID):
                    current = f"{current} → {existing[CONF_ENTITY_ID]}"
                field = f"{base_label} (current: {current})"
            else:
                field = base_label

            existing_action = existing.get(CONF_ACTION)
            default_action = [existing_action] if existing_action else []
            schema_fields[vol.Optional(field, default=default_action)] = action_selector

        return self.async_show_form(
            step_id="map", data_schema=vol.Schema(schema_fields), errors=errors
        )

    # ------------------------------------------------------------------
    # Step: export
    # ------------------------------------------------------------------

    async def async_step_export(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        entry = self._entry
        base = dict(entry.data)
        base.update(entry.options or {})
        current_mappings: dict = base.get(CONF_MAPPINGS, {})

        if user_input is not None:
            filename: str = user_input.get("export_filename", "").strip()
            if not filename:
                errors["export_filename"] = "empty_filename"
            else:
                # Sanitise — strip any path separators and ensure .yaml extension
                filename = os.path.basename(filename)
                if not filename.endswith(".yaml"):
                    filename = filename + ".yaml"

                try:
                    storage_dir = _ensure_storage_dir(self.hass.config.config_dir)
                    filepath = os.path.join(storage_dir, filename)
                    yaml_content = _build_export_yaml(current_mappings)

                    def _write() -> None:
                        with open(filepath, "w", encoding="utf-8") as fh:
                            fh.write(yaml_content)

                    await self.hass.async_add_executor_job(_write)

                    # Success — persist options unchanged and close the flow
                    return self.async_create_entry(
                        title="",
                        data={
                            CONF_REMOTE_IP: self._current_remote_ip(),
                            CONF_NUM_DEVICES: self._current_num_devices(),
                            CONF_MAPPINGS: current_mappings,
                        },
                    )
                except Exception:  # noqa: BLE001
                    errors["base"] = "export_failed"

        storage_dir = os.path.join(self.hass.config.config_dir, STORAGE_DIR)
        schema = vol.Schema(
            {
                vol.Required("export_filename", default="my_mappings"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
            }
        )
        return self.async_show_form(
            step_id="export",
            data_schema=schema,
            errors=errors,
            description_placeholders={"storage_dir": storage_dir},
        )

    # ------------------------------------------------------------------
    # Step: import — pick a file
    # ------------------------------------------------------------------

    async def async_step_import(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        storage_dir = _ensure_storage_dir(self.hass.config.config_dir)

        def _list_files() -> list[str]:
            return sorted(f for f in os.listdir(storage_dir) if f.endswith(".yaml"))

        yaml_files = await self.hass.async_add_executor_job(_list_files)

        if not yaml_files:
            # No files available — show an informational form with an error
            return self.async_show_form(
                step_id="import",
                data_schema=vol.Schema({}),
                errors={"base": "no_yaml_files"},
                description_placeholders={"storage_dir": storage_dir},
            )

        if user_input is not None:
            self._import_filename = user_input.get("import_filename", "")
            if not self._import_filename:
                errors["import_filename"] = "no_file_selected"
            else:
                return await self.async_step_import_confirm()

        file_selector = SelectSelector(
            SelectSelectorConfig(
                options=[{"value": f, "label": f} for f in yaml_files],
                multiple=False,
                mode="dropdown",
            )
        )

        schema = vol.Schema(
            {
                vol.Required("import_filename"): file_selector,
            }
        )
        return self.async_show_form(
            step_id="import",
            data_schema=schema,
            errors=errors,
            description_placeholders={"storage_dir": storage_dir},
        )

    # ------------------------------------------------------------------
    # Step: import_confirm — choose replace or merge, then apply
    # ------------------------------------------------------------------

    async def async_step_import_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        errors: dict[str, str] = {}

        entry = self._entry
        base = dict(entry.data)
        base.update(entry.options or {})
        current_mappings: dict = base.get(CONF_MAPPINGS, {})

        storage_dir = _ensure_storage_dir(self.hass.config.config_dir)
        filepath = os.path.join(storage_dir, self._import_filename)

        if user_input is not None:
            mode: str = user_input.get("import_mode", IMPORT_MODE_REPLACE)

            try:
                def _read() -> dict:
                    return _load_yaml_mappings(filepath)

                imported_mappings = await self.hass.async_add_executor_job(_read)
            except Exception:  # noqa: BLE001
                errors["base"] = "import_failed"
            else:
                if mode == IMPORT_MODE_MERGE:
                    # Start with current, overlay imported (imported wins on conflict)
                    merged: dict = {}
                    for d_str, btns in current_mappings.items():
                        merged.setdefault(d_str, {}).update(btns)
                    for d_str, btns in imported_mappings.items():
                        merged.setdefault(d_str, {}).update(btns)
                    final_mappings = merged
                else:
                    final_mappings = imported_mappings

                return self.async_create_entry(
                    title="",
                    data={
                        CONF_REMOTE_IP: self._current_remote_ip(),
                        CONF_NUM_DEVICES: self._current_num_devices(),
                        CONF_MAPPINGS: final_mappings,
                    },
                )

        mode_selector = SelectSelector(
            SelectSelectorConfig(
                options=[
                    {
                        "value": IMPORT_MODE_REPLACE,
                        "label": "Replace — discard current mappings, use file only",
                    },
                    {
                        "value": IMPORT_MODE_MERGE,
                        "label": "Merge — keep current mappings, imported values win on conflict",
                    },
                ],
                multiple=False,
                mode="list",
            )
        )

        schema = vol.Schema(
            {
                vol.Required("import_mode", default=IMPORT_MODE_REPLACE): mode_selector,
            }
        )
        return self.async_show_form(
            step_id="import_confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={"filename": self._import_filename},
        )

    # ------------------------------------------------------------------
    # Step: edit_select — pick which mapped button to edit
    # ------------------------------------------------------------------

    async def async_step_edit_select(self, user_input: dict[str, Any] | None = None):
        entry = self._entry
        base = dict(entry.data)
        base.update(entry.options or {})

        current_mappings: dict = base.get(CONF_MAPPINGS, {})

        # Build a list of only the currently mapped buttons
        mapped_options: list[dict[str, str]] = []
        for d_str, btns in sorted(current_mappings.items(), key=lambda x: int(x[0])):
            for b_str in sorted(btns.keys(), key=lambda x: int(x)):
                key = f"{d_str}:{b_str}"
                label = _resolve_label(d_str, b_str)
                mapped_options.append({"value": key, "label": label})

        if not mapped_options:
            return self.async_abort(reason="no_mapped_buttons")

        if user_input is not None:
            self._edit_button = user_input.get("edit_button", "")
            if self._edit_button:
                return await self.async_step_edit_map()

        button_selector = SelectSelector(
            SelectSelectorConfig(
                options=mapped_options,
                multiple=False,
                mode="dropdown",
            )
        )

        schema = vol.Schema(
            {
                vol.Required("edit_button"): button_selector,
            }
        )
        return self.async_show_form(step_id="edit_select", data_schema=schema, errors={})

    # ------------------------------------------------------------------
    # Step: edit_map — ActionSelector pre-filled with existing action
    # ------------------------------------------------------------------

    async def async_step_edit_map(self, user_input: dict[str, Any] | None = None):
        entry = self._entry
        base = dict(entry.data)
        base.update(entry.options or {})

        current_mappings: dict = base.get(CONF_MAPPINGS, {})
        errors: dict[str, str] = {}

        if not self._edit_button or ":" not in self._edit_button:
            return self.async_abort(reason="invalid_selection")

        d_str, b_str = self._edit_button.split(":", 1)
        existing: dict = (current_mappings.get(d_str, {}) or {}).get(b_str, {})
        field_label = _resolve_label(d_str, b_str)

        if user_input is not None:
            action: Any = user_input.get(field_label)
            # HA 2024.x+ wraps ActionSelector result in a list
            if isinstance(action, list):
                action = action[0] if action else None

            if not action or not isinstance(action, dict):
                errors["base"] = "invalid_action"
            else:
                action_str: str = action.get("action", "")
                if not action_str or "." not in action_str:
                    errors["base"] = "invalid_action"
                else:
                    svc_domain, svc_name = action_str.split(".", 1)
                    target: dict[str, Any] = action.get("target", {})
                    entity_id: str = ""
                    if isinstance(target.get("entity_id"), list):
                        entity_id = target["entity_id"][0]
                    elif isinstance(target.get("entity_id"), str):
                        entity_id = target["entity_id"]

                    # Preserve all other mappings, update only this button
                    new_mappings: dict = {
                        d: dict(btns) for d, btns in current_mappings.items()
                    }
                    new_mappings.setdefault(d_str, {})[b_str] = {
                        CONF_ACTION: action,
                        CONF_DOMAIN: svc_domain.strip(),
                        CONF_SERVICE: svc_name.strip(),
                        CONF_ENTITY_ID: entity_id,
                    }

                    return self.async_create_entry(
                        title="",
                        data={
                            CONF_REMOTE_IP: self._current_remote_ip(),
                            CONF_NUM_DEVICES: self._current_num_devices(),
                            CONF_MAPPINGS: new_mappings,
                        },
                    )

        # Pre-populate with the existing raw action so the ActionSelector
        # renders with the current service and entity already filled in.
        # Wrap in a list — HA's ActionSelector always expects a list as default.
        existing_action = existing.get(CONF_ACTION)
        default_action = [existing_action] if existing_action else []

        schema = vol.Schema(
            {
                vol.Optional(field_label, default=default_action): ActionSelector(
                    ActionSelectorConfig()
                ),
            }
        )
        return self.async_show_form(
            step_id="edit_map",
            data_schema=schema,
            errors=errors,
        )
