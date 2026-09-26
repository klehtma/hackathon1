from camoufox.sync_api import Camoufox
from browserforge.fingerprints import Screen

class Driver:
    def __init__(self):
        self._cf = Camoufox(
            humanize=True,
            geoip=True,
            screen=Screen(max_width=1920, max_height=1080),
            block_webrtc=True,
        )
        self.browser = self._cf.__enter__()
        self.page = self.browser.new_page()

    def close(self):
        self._cf.__exit__(None, None, None)

    def __enter__(self):
        return self.page

    def __exit__(self, *exc):
        self.close()