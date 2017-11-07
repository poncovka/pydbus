from pydbus import SessionBus
from gi.repository import GLib
from threading import Thread
import sys

loop = GLib.MainLoop()

bus = SessionBus()

class TestObject(object):
    '''
<node>
    <interface name='net.lew21.pydbus.tests.publish_replacable'>
        <method name='Id'>
            <arg type='s' name='id' direction='out'/>
        </method>
        <method name='Quit'/>
    </interface>
</node>
    '''
    def __init__(self, id):
        self.id = id
        dbus = bus.get('org.freedesktop.DBus', '/org/freedesktop/DBus')
        dbus.NameLost.connect(self._handle_replacement_cb)

    def Id(self):
        res = self.id
        print("%s: Id() called" % res)
        return res

    def Quit(self):
        print("%s: quitting" % self.id)
        GLib.timeout_add_seconds(1, loop.quit)

    def _handle_replacement_cb(self, name):
        if name == "net.lew21.pydbus.tests.publish_replacable":
            print("%s: replaced" % self.id)
            self.Quit()

with bus.publish("net.lew21.pydbus.tests.publish_replacable", TestObject("Old Owner"), allow_replacement=True):
    remote = bus.get("net.lew21.pydbus.tests.publish_replacable")

    def t1_func():
        remote.Id()

    t1 = Thread(None, t1_func)
    t1.daemon = True

    t1.start()

    loop.run()

    t1.join()
