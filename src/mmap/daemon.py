
import wifi
import client
from multiprocessing import Process, Manager
import time

try:
    import cPickle as pickle
except ImportError:
    import pickle

class DaemonNotRunningError(Exception):
    pass

def _daemon(shared):
    locator = wifi.make_locator()

    while True:
        try:
            cells = locator.scan()
        except wifi.WifiError:
            locator = wifi.make_locator()
            continue

        shared['latest_scan'] = pickle.dumps(cells)
        time.sleep(shared['update_interval'])

_daemon_process = None
_daemon_shared = None
def start(update_interval=15):
    global _daemon_process, _daemon_shared
    if _daemon_process:
        return

    manager = Manager()
    _daemon_shared = manager.dict()
    _daemon_shared['latest_scan'] = pickle.dumps([])
    _daemon_shared['update_interval'] = update_interval

    _daemon_process = Process(target=_daemon, args=(_daemon_shared,))
    _daemon_process.start()

def is_running():
    return _daemon_process is not None and _daemon_process.is_alive()

def _assert_running():
    if not is_running():
        raise DaemonNotRunningError()

def set_update_interval(interval):
    _assert_running()
    _daemon_shared['update_interval'] = interval

def get_latest_scan():
    _assert_running()
    return pickle.loads(_daemon_shared['latest_scan'])

def force_scan():
    raise NotImplemented()

def stop():
    global _daemon_process, _daemon_shared

    if is_running():
        _daemon_process.terminate()
    _daemon_process = None
    _daemon_shared = None











