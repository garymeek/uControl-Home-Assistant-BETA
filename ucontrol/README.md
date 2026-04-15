Installing the integration:
1) Install the add on for Samba/SMB access
2) Copy the files from the repo (ignoring the remote programmer folder) to \\<HA IP>\config\custom_components\uControl\
3) Restart HA
4)Go to Settings -> Devices & Services
5) Click Add integration
6) Search for uControl and select 'uControl IP Bridge'
7) Click Add entry
8) Enter the remote IP, and select the number of devices (match with how many you configured on the remote)
9) Click the Cog
10)Click buttons to configure
11) The device numbers correspond to the order in which you added the devices to the remote Device 1 = First device added
12) Add the buttons you would like to use (you must only add buttons that you will map to an HA action13
13) On the next screen you can add actions for each button
14) Should now be good to go

Buttons Available in the integration
===============================================
Each Device has the following buttons available

Button ID
==========
ID  Button 
0 - info 
1 - 0 
2 - guide 
3 - 7 
4 - 8 
5 - 9 
6 - 4 
7 - 5 
8 - 6 
9 - 1 
10 - 2 
11 - 3 
12 - Red 
13 - Green 
14 - Yellow 
15 - Blue 
16 - Vol- 
17 - Back 
18 - CHDown 
19 - Down 
20 - Mute 
21 - Left 
22 - Enter 
23 - Right 
24 - Menu 
25 - Up 
26 - Vol+ 
27 - Home 
28 - CHUP 
29 - Rec 
30 - Pause 
31 - Stop 
32 - Previous 
33 - Play 
34 - Next
39 - TV Device Selected
40 - Audio Device Selected
41 - Input Device Selected
49 - Power On (these are added to the Power On menu - short press of power button)
50 - Power Off (these are added to the Power Off menu - long press of power button)

Sequence Buttons
================
These are global (not device context specific) and configured for short and long press (to give you an on an off option for a macro)

Sequence 1 -4
Long Press
Short Press

