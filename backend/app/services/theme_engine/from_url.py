"""(v2) Extract site colors — SSRF-guarded stub for Phase 1."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.models.theme import Theme
from app.services.theme_engine.presets import get_preset


def _is_private_host(hostname: str) -> bool:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return True
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            return True
    return False


def from_url(url: str, *, mood: str = "corporate") -> Theme:
    """Placeholder: validates URL safety then returns preset until Phase 5."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Only http(s) URLs are allowed")
    if _is_private_host(parsed.hostname):
        raise ValueError("URL resolves to a private/reserved address")
    theme = get_preset("neutral", mood=mood)
    theme.name = f"From URL · {parsed.hostname}"
    theme.source = "url"
    theme.contrast.adjustments.append("URL extraction deferred; using neutral preset")
    return theme
