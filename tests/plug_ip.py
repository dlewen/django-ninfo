"""
Minimal ninfo plugin for testing CombinedQueryView.

Handles 'ip' type arguments and returns a simple dict result.
No template file is provided — render_template() will return str(result)
via the fallback path, which is sufficient for endpoint smoke tests.
"""
from ninfo import PluginBase


class IpPlugin(PluginBase):
    """IP lookup test plugin."""
    name = "testip"
    title = "Test IP Plugin"
    description = "Returns a fixed result for any IP address"
    cache_timeout = 60
    types = ["ip"]
    local = True
    remote = True

    def setup(self):
        pass

    def get_info(self, arg):
        return {"address": arg, "asn": "AS64496"}

    def to_json(self, result):
        return result


plugin_class = IpPlugin
