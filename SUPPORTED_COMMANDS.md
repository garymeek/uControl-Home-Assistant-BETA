## Legend

| Symbol | Meaning |
|---|---|
| ✅ | Supported |
| ❌ | Not Supported |
| ⚠️ | Partial Support / Limited Testing |

---

# Tested Commands

| Device Type | Device Name | Command | Home Assistant Service | Entity ID Supported | Device ID Supported |
|---|---|---|---|---|---|
| Media Player | Apple TV | Remote Commands | `remote.send_command` | ✅ | ❌ |
| Media Player | Fire TV | ADB Commands | `androidtv.adb_command` | ✅ | ❌ |
| Media Player | LG TV | Button Commands | `webostv.button` | ✅ | ❌ |
| Media Player | Sky Q | Remote / Channel Commands | `media_player.play_media` | ✅ | ❌ |
| Media Player | Sonos | Play / Pause Media | `media_player.media_play_pause` | ✅ | ❌ |
| Scene | Home Assistant Scene | Activate Scene | `scene.turn_on` | ✅ | ❌ |
| Scene | Philips Hue Scene | Activate Hue Scene | `hue.activate_scene` | ✅ | ❌ |
| Automation | Home Assistant Automation | Trigger Automation | `automation.trigger` | ✅ | ❌ |
| Script | Home Assistant Script | Run Script | `script.turn_on` | ✅ | ❌ |


---