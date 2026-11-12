import os
import socket


def _is_port_open(host: str, port: int, timeout: float = 0.8) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def get_local_proxy_url() -> str:
    """Detect local proxy port (v2rayN mixed:10808, Clash 7890, or HTTP 10809)."""
    env_proxy = os.environ.get("OVERSEAS_PROXY", "").strip()
    if env_proxy:
        return env_proxy

    if _is_port_open("127.0.0.1", 10808):
        return "socks5h://127.0.0.1:10808"

    if _is_port_open("127.0.0.1", 10809):
        return "http://127.0.0.1:10809"

    if _is_port_open("127.0.0.1", 7890):
        return "http://127.0.0.1:7890"

    return "socks5h://127.0.0.1:10808"


def get_requests_proxies() -> dict[str, str]:
    proxy_url = get_local_proxy_url()
    return {
        "http": proxy_url,
        "https": proxy_url,
    }
