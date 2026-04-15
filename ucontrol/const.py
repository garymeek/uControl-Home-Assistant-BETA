from __future__ import annotations

DOMAIN = "ucontrol_ip"

# Directory inside HA config where mapping YAMLs are persisted
STORAGE_DIR = "ucontrol_ip"

# Import merge modes
IMPORT_MODE_REPLACE = "replace"
IMPORT_MODE_MERGE = "merge"

CONF_REMOTE_IP = "remote_ip"
CONF_NUM_DEVICES = "num_devices"
CONF_MAPPINGS = "mappings"

# Maximum number of received commands kept in memory for diagnostics
COMMAND_LOG_MAX = 50

CONF_ACTION = "action"
CONF_DOMAIN = "domain"
CONF_SERVICE = "service"
CONF_ENTITY_ID = "entity_id"
CONF_SERVICE_DATA = "service_data"

BUTTON_IDS: list[int] = list(range(0, 35)) + [41, 49, 50]

# Buttons that only appear on a specific device
DEVICE_SPECIFIC_BUTTONS: dict[int, dict[int, str]] = {
    1: {39: "TV"},       # TV button only on device 1 (LG)
    2: {40: "Audio"},    # Audio button only on device 2 (Yamaha)
}

# Sequence devices (10-13) only have short press and long press
SEQUENCE_DEVICE_IDS: list[int] = [10, 11, 12, 13]

SEQUENCE_BUTTON_IDS: list[int] = [1, 2]

SEQUENCE_BUTTON_LABELS: dict[int, str] = {
    1: "Short Press",
    2: "Long Press",
}

BUTTON_LABELS: dict[int, str] = {
    0: "info",
    1: "0",
    2: "guide",
    3: "7",
    4: "8",
    5: "9",
    6: "4",
    7: "5",
    8: "6",
    9: "1",
    10: "2",
    11: "3",
    12: "Red",
    13: "Green",
    14: "Yellow",
    15: "Blue",
    16: "Vol-",
    17: "Back",
    18: "CHDown",
    19: "Down",
    20: "Mute",
    21: "Left",
    22: "Enter",
    23: "Right",
    24: "Menu",
    25: "Up",
    26: "Vol+",
    27: "Home",
    28: "CHUP",
    29: "Rec",
    30: "Pause",
    31: "Stop",
    32: "Previous",
    33: "Play",
    34: "Next",
    41: "Input",
    49: "Power On",
    50: "Power Off",
}
