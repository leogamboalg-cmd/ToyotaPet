import obd
import time

ports = ["COM7", "COM8"]

for port in ports:
    print(f"\nTrying {port}...")

    try:
        connection = obd.OBD(port, fast=False, timeout=10)

        print("Status:", connection.status())
        print("Connected:", connection.is_connected())

        if connection.is_connected():
            rpm = connection.query(obd.commands.RPM)
            speed = connection.query(obd.commands.SPEED)

            print("RPM:", rpm.value)
            print("Speed:", speed.value)

            connection.close()
            print(f"\n✅ WORKING PORT: {port}")
            break

        connection.close()

    except Exception as e:
        print(f"Failed on {port}: {e}")

    time.sleep(1)
