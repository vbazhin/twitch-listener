"""Utilities for Twitch Listener needs."""

def join_urls(*args):
    """The util join urls to path.

    Unlike requests.compat.urljoin, it works for joining multiple urls.
    """
    return '/'.join(arg.strip('/') for arg in args).strip('/')
