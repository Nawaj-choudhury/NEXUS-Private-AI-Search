import ipaddress
import socket
from urllib.parse import urljoin, urlparse, urlunparse


def normalize_url(url: str, allow_localhost: bool = False) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Only well-formed http(s) URLs without embedded credentials are allowed")
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if not hostname:
        raise ValueError("URL hostname is required")
    if not allow_localhost and _is_blocked_host(hostname):
        raise ValueError("Local, loopback, link-local, and private network destinations are blocked")
    port = parsed.port
    netloc = hostname if port is None else f"{hostname}:{port}"
    return urlunparse((parsed.scheme.lower(), netloc, parsed.path or "/", "", parsed.query, ""))


def resolve_link(base_url: str, link: str, allow_localhost: bool = False) -> str | None:
    if not link or link.startswith(("#", "mailto:", "javascript:", "tel:")):
        return None
    try:
        return normalize_url(urljoin(base_url, link), allow_localhost)
    except ValueError:
        return None


def _is_blocked_host(hostname: str) -> bool:
    if hostname in {"localhost", "localhost.localdomain"}:
        return True
    try:
        addresses = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    for address in {item[4][0] for item in addresses}:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_unspecified or ip.is_reserved:
            return True
    return False