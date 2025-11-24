from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request, HTTPException
import ipaddress
import logging
import os
import secrets
from base64 import b64decode

logger = logging.getLogger(__name__)

class SmartAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Define LAN ranges
        self.lan_ranges = [
            ipaddress.ip_network("127.0.0.0/8"),
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
        ]
        # Credentials from env or default
        self.username = os.getenv("API_USERNAME", "admin")
        self.password = os.getenv("API_PASSWORD", "attendance2025")

    async def dispatch(self, request: Request, call_next):
        # Allow OPTIONS (CORS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get Client IP
        client_ip = request.client.host
        # Handle headers from proxy (X-Forwarded-For)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0]

        is_lan = False
        try:
            ip = ipaddress.ip_address(client_ip)
            for network in self.lan_ranges:
                if ip in network:
                    is_lan = True
                    break
        except ValueError:
            pass # Invalid IP, treat as WAN

        # If LAN, bypass auth
        if is_lan:
            return await call_next(request)

        # If WAN, require Basic Auth
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required for WAN access"},
                headers={"WWW-Authenticate": "Basic"},
            )

        try:
            encoded_credentials = auth_header.split(" ")[1]
            decoded_credentials = b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded_credentials.split(":", 1)
        except Exception:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication credentials"},
                headers={"WWW-Authenticate": "Basic"},
            )

        if not (secrets.compare_digest(username, self.username) and 
                secrets.compare_digest(password, self.password)):
            return JSONResponse(
                status_code=401,
                content={"detail": "Incorrect username or password"},
                headers={"WWW-Authenticate": "Basic"},
            )

        return await call_next(request)
