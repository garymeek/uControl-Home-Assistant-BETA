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

