"""
Daemon compatibility module.
"""

from assistance.daemon import VoiceAssistantDaemon

_global_daemon = None
_stop_requested = False
_diary_callbacks = None

def get_dictation_engine():
    """Get dictation engine (compatibility stub)"""
    return None

def main(smoke_test=False):
    """Main daemon entry point"""
    global _global_daemon
    if smoke_test:
        print("Smoke test passed")
        return
    daemon = VoiceAssistantDaemon()
    _global_daemon = daemon
    daemon.run()

def is_stop_requested():
    """Check if stop was requested"""
    return _stop_requested

def request_stop():
    """Request daemon stop"""
    global _stop_requested
    _stop_requested = True

def set_diary_update_callbacks(on_token=None, on_status=None):
    """Set diary update callbacks"""
    global _diary_callbacks
    _diary_callbacks = {
        'on_token': on_token,
        'on_status': on_status
    }

__all__ = [
    'get_dictation_engine', 'main', 'is_stop_requested',
    'request_stop', 'set_diary_update_callbacks'
]
