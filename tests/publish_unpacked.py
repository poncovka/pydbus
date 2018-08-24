from pydbus import SessionBus
from gi.repository import GLib
from threading import Thread
import sys

done = 0
loop = GLib.MainLoop()

class TestObject(object):
	'''
<node>
	<interface name='net.lew21.pydbus.tests.publish_unpacked'>
		<method name='GetVariant'>
			<arg type='i' name='response' direction='in'/>
			<arg type='v' name='response' direction='out'/>
		</method>
	</interface>
</node>
	'''

	def GetVariant(self, x):
		return GLib.Variant('as', [str(x)])

bus = SessionBus()

with bus.publish("net.lew21.pydbus.tests.publish_unpacked", TestObject()):
	remote = bus.get("net.lew21.pydbus.tests.publish_unpacked")

	def try_quit():
		global done
		done += 1
		if done == 2:
			loop.quit()

	def callback1(argument, returned=None, error=None):
		assert argument == 1
		assert returned == ["1"]
		assert error is None

		print("unpack_result check async1 - ok")
		try_quit()

	def callback2(argument, returned=None, error=None):
		assert argument == 2
		assert isinstance(returned, GLib.Variant)
		assert returned.unpack() == (["2"],)
		assert error is None

		print("unpack_result check async2 - ok")
		try_quit()

	def t1_func():
		result = remote.GetVariant(1)
		assert result == ["1"]

		result = remote.GetVariant(2, unpack_result=False)
		assert isinstance(result, GLib.Variant)
		assert result.unpack() == (["2"],)

		remote.GetVariant(1, callback=callback1, callback_args=(1,))
		remote.GetVariant(2, callback=callback2, callback_args=(2,), unpack_result=False)

		print("unpack_result check sync - ok")

	t1 = Thread(None, t1_func)
	t1.daemon = True

	def handle_timeout():
		print("ERROR: Timeout.")
		sys.exit(1)

	GLib.timeout_add_seconds(2, handle_timeout)

	t1.start()

	loop.run()

	t1.join()
