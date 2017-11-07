from pydbus import SessionBus
from gi.repository import GLib
from threading import Thread
import sys
import time

loop = GLib.MainLoop()

bus = SessionBus()

SERVICE_NAME = "net.lew21.pydbus.tests.publish_replacable"

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

    def Id(self):
        res = self.id
        print("%s: Id() called" % res)
        return res

    def Quit(self):
        print("%s: quitting" % self.id)
        GLib.timeout_add_seconds(1, loop.quit)

time.sleep(2)
remote = bus.get(SERVICE_NAME)
id = remote.Id()
assert(id == "Old Owner")

with bus.publish(SERVICE_NAME, TestObject("New Owner"), replace=True):

    def t1_func():
        id = remote.Id()
        assert(id == "New Owner")
        remote.Quit()

    t1 = Thread(None, t1_func)
    t1.daemon = True

    t1.start()

    loop.run()

    t1.join()
