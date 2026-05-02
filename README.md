# 🔌 uControl IP Bridge — Installation & Setup Guide

For ease it is recommedended that you configure the remote first using the remote programmer tool before completing the below steps

## 🚀 Install via HACS (Recommended)

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=garymeek&repository=uControl-Home-Assistant-BETA&category=integration)

### Steps:

1. Open **HACS**
2. Go to **Integrations**
3. Click the **⋮ (top right)** → **Custom repositories**
4. Add:
   ```
   https://github.com/garymeek/uControl-Home-Assistant-BETA.git
   ```
   Category: **Integration**
5. Click **Add**
6. Search for **uControl IP Bridge**
7. Click **Download**
8. Restart **Home Assistant**

---

## 🛠️ Manual Installation (Advanced)

1. Install the **Samba/SMB add-on** (or use File Editor)
2. Copy the integration files **(ignore the `remote programmer` folder)** to:

   ```
   \\<HA IP>\config\custom_components\uControl_ip\
   ```

3. Restart **Home Assistant**

---

## ⚙️ Integration Setup

1. Go to:
   **Settings → Devices & Services**
2. Click **➕ Add Integration**
3. Search for **uControl IP Bridge**
4. Click **Add Entry**
5. Enter:
   - 🌐 **Remote IP**
   - 🔢 **Number of Devices** (must match uControl remote setup)

---

## 🎛️ Configuration

1. Click the **⚙️ Cog (Options)**
2. Click **🔘 Buttons to Configure**
3. Add only the buttons you actually plan to use

📌 **Important:**
- Device numbering matches the order in the remote  
  → `Device 1 = First device added`

---

## 🔗 Action Mapping

1. After selecting buttons:
2. Assign **Home Assistant actions** to each button
3. Save configuration

✅ You’re now ready to go

---

# 🎮 Buttons Available in the Integration

Each device exposes the following buttons:

## 🔢 Numeric & Navigation

| ID | Button |
|----|--------|
| 0  | Info |
| 1  | 0 |
| 2  | Guide |
| 3–11 | 1–9 |
| 19 | Down |
| 21 | Left |
| 22 | Enter |
| 23 | Right |
| 25 | Up |

---

## 🎨 Colour Buttons

| ID | Button |
|----|--------|
| 12 | 🔴 Red |
| 13 | 🟢 Green |
| 14 | 🟡 Yellow |
| 15 | 🔵 Blue |

---

## 🔊 Volume & Channels

| ID | Button |
|----|--------|
| 16 | 🔉 Vol- |
| 26 | 🔊 Vol+ |
| 20 | 🔇 Mute |
| 18 | CH Down |
| 28 | CH Up |

---

## 📺 Media Controls

| ID | Button |
|----|--------|
| 29 | ⏺️ Record |
| 30 | ⏸️ Pause |
| 31 | ⏹️ Stop |
| 32 | ⏮️ Previous |
| 33 | ▶️ Play |
| 34 | ⏭️ Next |

---

## 📱 Navigation & System

| ID | Button |
|----|--------|
| 17 | ⬅️ Back |
| 24 | ☰ Menu |
| 27 | 🏠 Home |

---

## 🔄 Device Selection

| ID | Button |
|----|--------|
| 39 | 📺 TV Device Selected |
| 40 | 🔊 Audio Device Selected |
| 41 | 🔌 Input Device Selected |

---

## ⚡ Power Control

| ID | Button |
|----|--------|
| 49 | 🔘 Power ON (Short Press) |
| 50 | 🔘 Power OFF (Long Press) |

---

# 🔁 Sequence Buttons (Macros)

These are **global buttons** (not tied to a device)

Each supports:
- 👆 **Short Press**
- ✋ **Long Press**

### Available Sequences:

- Sequence 1  
- Sequence 2  
- Sequence 3  
- Sequence 4  

💡 Perfect for:
- “Watch TV” scenes
- Full system power on/off
- Multi-device automation

---

# 💡 Pro Tips

- Only add buttons you actually use → keeps UI clean  
- Use **Sequences** for client-friendly automation  
- Map **long press = OFF**, **short press = ON** for intuitive control  
- Keep device order consistent with uControl setup  
