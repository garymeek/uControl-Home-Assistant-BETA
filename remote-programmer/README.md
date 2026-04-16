# 🎮 uControl Remote — Setup Guide

## 📡 1. Connect the Remote

- Ensure the remote is connected to your **Wi-Fi network**
- Assign it an **IP address**
- It is **strongly recommended** to create a **DHCP reservation (static IP)** on your router

📌 Instructions for Wi-Fi setup are included in the remote packaging

---

## 🖥️ 2. Open Remote Tool

- Launch the **Remote Tool**
- Select:
  ```
  1 - Setup Remote
  ```

---

## 📺 3. Add Devices

- Enter the devices you want to control  
- ⚠️ **Order matters**:
  - `Device 1 = First device added`
  - This order is used inside Home Assistant later
- Assign each device to a category:
  - 📺 TV  
  - 🔊 Audio  
  - 🔌 Input  

✔️ Once you’ve added the last device, press **Enter** to complete setup

---

## 🔊 4. Volume Control Configuration

Choose how volume should behave:

- **Per-device volume (Recommended for simple setups)**  
  → Each device controls its own volume  

- **Shared volume (AVR mode)**  
  → Volume defaults to the first **Audio device** (e.g. AVR)

---

## 📸 5. Save Configuration Summary

- Take a **screenshot of the configuration summary**

💡 This is extremely useful for:
- Debugging  
- Support  
- Future changes  

---

## ⚙️ 6. Generate & Upload Configuration

1. Generate the template  
2. Select:
   ```
   Y (Yes) to upload configuration
   ```

### Enter the following:

- 🌐 **Remote IP Address**  
- 🏠 **Controller IP Address** (your Home Assistant server)  
- 🏷️ **Zone Name**  
  - Examples:
    - Living Room  
    - Home Cinema  
    - Bedroom  

---

## 🚀 7. Upload Process

- The tool will:
  - Connect to the remote  
  - Upload the configuration  

⏳ Wait for completion

---

## ⚠️ 8. Check for Errors

- Review any errors shown after upload  
- Take a **screenshot if needed**

---

## 🔚 9. Finish

- Exit the Remote Tool  
- Your remote is now ready for use with Home Assistant 🎉

---

# 💡 Pro Tips

- 🔒 Always use a **static IP** for reliability  
- 🧠 Keep device order consistent — it directly affects HA mapping  
- 📸 Save setup screenshots — saves time later  
- 🎯 Only add devices you actually use  
