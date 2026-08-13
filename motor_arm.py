from pymavlink import mavutil
import sys, time

GAZ = int(sys.argv[1]) if len(sys.argv) > 1 else 1150   # 1000 min, 2000 maks
SURE = int(sys.argv[2]) if len(sys.argv) > 2 else 10

m = mavutil.mavlink_connection('/dev/ttyACM0', baud=115200)
m.wait_heartbeat(timeout=10)
print("bagli")

# Arming kontrolleri kapali - GPS/pusula yok
m.mav.param_set_send(m.target_system, m.target_component,
    b'ARMING_CHECK', 0.0, mavutil.mavlink.MAV_PARAM_TYPE_INT32)
time.sleep(1)

m.set_mode_apm('STABILIZE')
time.sleep(1)

print("ARM...")
m.mav.command_long_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0,0,0,0,0,0)
time.sleep(3)

print(f"gaz {GAZ}, {SURE} sn - Ctrl+C ile DURDUR")
try:
    t0 = time.time()
    while time.time() - t0 < SURE:
        m.mav.rc_channels_override_send(
            m.target_system, m.target_component,
            1500, 1500, GAZ, 1500, 0,0,0,0)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nkullanici durdurdu")
finally:
    m.mav.rc_channels_override_send(m.target_system, m.target_component,
        1500, 1500, 1000, 1500, 0,0,0,0)
    time.sleep(1)
    m.mav.command_long_send(m.target_system, m.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 0, 0,0,0,0,0,0)
    print("DISARM")
