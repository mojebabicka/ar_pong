import twoen

device = twoen.Device("10.0.23.207", "Admin", "Test1234")
device.login()
print(device.get_last_restart())