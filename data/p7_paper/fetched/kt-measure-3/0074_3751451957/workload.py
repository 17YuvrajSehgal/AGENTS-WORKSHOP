import sys, os, hashlib, io, contextlib
SRC = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), '..', '..', 'src')
sys.path.insert(0, os.path.abspath(SRC))
from pubsub import pub
from modules.network.messaging_service import PubSubMessagingService
from system_loop import SystemLoop

N_ITER = 60
log = []
results = []

class Driver:
    def __init__(self, loop):
        self.loop = loop
        self.count = 0
    def on_loop(self):
        self.count += 1
        if self.count >= N_ITER:
            self.loop._state = SystemLoop.STATE_STOPPED
    def on_log(self, message):
        log.append(message)
    def on_exit(self):
        log.append('exit')

with contextlib.redirect_stdout(io.StringIO()):
    ms = PubSubMessagingService()
    loop = SystemLoop(ms)
    d = Driver(loop)
    pub.subscribe(d.on_loop, 'system/loop')
    pub.subscribe(d.on_log, 'log')
    pub.subscribe(d.on_exit, 'system/exit')
    # state transitions
    ms.publish('system/throttle', requestor='a')
    results.append((loop._state, loop.sleep_interval))
    ms.publish('system/wake', requestor='a')
    results.append((loop._state, loop.sleep_interval))
    ms.publish('gpio/motion', value=10)
    results.append((loop._state, loop.sleep_interval))
    loop.start()
results.append(('iterations', d.count, loop._state))
digest = hashlib.sha256(repr(results).encode() + repr([m for m in log if 'interval' not in str(m)]).encode()).hexdigest()
print(results)
print(digest)
