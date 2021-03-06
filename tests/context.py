from pydbus import SessionBus, connect
import os

DBUS_SESSION_BUS_ADDRESS = os.getenv("DBUS_SESSION_BUS_ADDRESS")

with connect(DBUS_SESSION_BUS_ADDRESS) as bus:
	bus.dbus

del bus._dbus
try:
	bus.dbus
	assert(False)
except RuntimeError:
	pass

with SessionBus() as bus:
	pass

# SessionBus() and SystemBus() are not closed automatically, so this should work:
bus.dbus

with bus.request_name("net.lew21.Test"):
	pass

with bus.request_name("net.lew21.Test"):
	pass

with bus.request_name("net.lew21.Test"):
	try:
		bus.request_name("net.lew21.Test")
		assert(False)
	except RuntimeError:
		pass

with bus.watch_name("net.lew21.Test"):
	pass

with bus.subscribe(sender="net.lew21.Test"):
	pass
