🔌 uControl IP Bridge — Installation & Setup Guide
🚀 Install via HACS (Recommended)

Steps:
Open HACS
Go to Integrations
Click the ⋮ (top right) → Custom repositories

Add:

https://github.com/garymeek/uControl-Home-Assistant-BETA.git

Category: Integration

Click Add
Search for uControl IP Bridge
Click Download
Restart Home Assistant
🛠️ Manual Installation (Advanced)
Install the Samba/SMB add-on (or use File Editor)

Copy the integration files (ignore the remote programmer folder) to:

\\<HA IP>\config\custom_components\uControl\
Restart Home Assistant
⚙️ Integration Setup
Go to:
Settings → Devices & Services
Click ➕ Add Integration
Search for uControl IP Bridge
Click Add Entry
Enter:
🌐 Remote IP
🔢 Number of Devices (must match uControl remote setup)
🎛️ Configuration
Click the ⚙️ Cog (Options)
Click 🔘 Buttons to Configure
Add only the buttons you actually plan to use

📌 Important:

Device numbering matches the order in the remote
→ Device 1 = First device added
🔗 Action Mapping
After selecting buttons:
Assign Home Assistant actions to each button
Save configuration

✅ You’re now ready to go

🎮 Buttons Available in the Integration

Each device exposes the following buttons:

🔢 Numeric & Navigation
ID	Button
0	Info
1	0
2	Guide
3–11	1–9
19	Down
21	Left
22	Enter
23	Right
25	Up
🎨 Colour Buttons
ID	Button
12	🔴 Red
13	🟢 Green
14	🟡 Yellow
15	🔵 Blue
🔊 Volume & Channels
ID	Button
16	🔉 Vol-
26	🔊 Vol+
20	🔇 Mute
18	CH Down
28	CH Up
📺 Media Controls
ID	Button
29	⏺️ Record
30	⏸️ Pause
31	⏹️ Stop
32	⏮️ Previous
33	▶️ Play
34	⏭️ Next
📱 Navigation & System
ID	Button
17	⬅️ Back
24	☰ Menu
27	🏠 Home
🔄 Device Selection
ID	Button
39	📺 TV Device Selected
40	🔊 Audio Device Selected
41	🔌 Input Device Selected
⚡ Power Control
ID	Button
49	🔘 Power ON (Short Press)
50	🔘 Power OFF (Long Press)
🔁 Sequence Buttons (Macros)

These are global buttons (not tied to a device)

Each supports:

👆 Short Press
✋ Long Press
Available Sequences:
Sequence 1
Sequence 2
Sequence 3
Sequence 4

💡 Perfect for:

“Watch TV” scenes
Full system power on/off
Multi-device automation
💡 Pro Tips
Only add buttons you actually use → keeps UI clean
Use Sequences for client-friendly automation
Map long press = OFF, short press = ON for intuitive control
Keep device order consistent with uControl setup
