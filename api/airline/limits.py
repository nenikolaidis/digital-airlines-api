from flask import current_app, request
from flask_limiter import Limiter


def client_ip():
    """The caller's IP address, which rate limits are counted against.

    Behind a proxy every request comes from the proxy's address, so CLIENT_IP_HEADER can name a header
    that a trusted proxy sets to the real client IP (on Render, Cloudflare's CF-Connecting-IP).
    """
    header = current_app.config["CLIENT_IP_HEADER"]
    if header and request.headers.get(header):
        return request.headers[header].split(",")[0].strip()
    return request.remote_addr or "unknown"


limiter = Limiter(key_func=client_ip)


def login_limit():
    return current_app.config["LOGIN_RATE_LIMIT"]


def register_limit():
    return current_app.config["REGISTER_RATE_LIMIT"]
