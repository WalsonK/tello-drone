import time
import os
import platform


def check_os():
    os_name = platform.system()
    print(f"OS name: {os_name}")
    return os_name


def switch_wifi(SSID, password=None):
    os_name = check_os()
    command = ""
    if os_name == "Windows":
        if password:
            command = f'netsh wlan connect name="{SSID}" ssid="{SSID}" key="{password}"'
        else:
            command = f'netsh wlan connect name="{SSID}" ssid="{SSID}"'
    elif os_name == "Linux":
        if password:
            command = f'nmcli device wifi connect "{SSID}" password "{password}"'
        else:
            command = f'nmcli device wifi connect "{SSID}"'
    elif os_name == "Darwin":
        if password:
            command = f"networksetup -setairportnetwork en0 {SSID} {password}"
        else:
            command = f'networksetup -setairportnetwork en0 "{SSID}"'

    if command != "":
        os.system(command)


switch_wifi('@styledbykev', 'keezywifi')
