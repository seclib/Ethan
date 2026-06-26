#!/usr/bin/env python3
"""ETHAN CLI — Runtime client (Unix socket + HTTP fallback)."""

import json
import socket
import time
from typing import Iterator, Dict, Any

SOCKET_PATH = "/run/ethan/runtime.sock"
HTTP_URL = "http://localhost:8002"
TIMEOUT = 30


class RuntimeClient:
    """Client for ETHAN Runtime communication."""
    
    def __init__(self):
        self.socket_path = SOCKET_PATH
        self.http_url = HTTP_URL
        self.timeout = TIMEOUT
    
    def send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to Runtime (blocking)."""
        # Try Unix socket first
        try:
            return self._send_socket(request)
        except (ConnectionRefusedError, FileNotFoundError):
            # Fallback to HTTP
            return self._send_http(request)
    
    def stream(self, request: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Stream response from Runtime."""
        request["stream"] = True
        
        # Try Unix socket first
        try:
            yield from self._stream_socket(request)
        except (ConnectionRefusedError, FileNotFoundError):
            # Fallback to HTTP (SSE)
            yield from self._stream_http(request)
    
    def _send_socket(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send via Unix socket."""
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            sock.connect(self.socket_path)
            sock.sendall(json.dumps(request).encode() + b"\n")
            response = sock.recv(65536).decode()
            return json.loads(response)
    
    def _stream_socket(self, request: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Stream via Unix socket."""
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            sock.connect(self.socket_path)
            sock.sendall(json.dumps(request).encode() + b"\n")
            
            buffer = ""
            while True:
                chunk = sock.recv(4096).decode()
                if not chunk:
                    break
                
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line:
                        yield json.loads(line)
    
    def _send_http(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send via HTTP (fallback)."""
        try:
            import requests
        except ImportError:
            raise RuntimeError("HTTP fallback requires 'requests' library")
        
        resp = requests.post(f"{self.http_url}/", json=request, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()
    
    def _stream_http(self, request: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Stream via HTTP SSE (fallback)."""
        try:
            import requests
        except ImportError:
            raise RuntimeError("HTTP fallback requires 'requests' library")
        
        resp = requests.post(f"{self.http_url}/stream", json=request, stream=True, timeout=self.timeout)
        resp.raise_for_status()
        
        for line in resp.iter_lines():
            if line.startswith(b"data: "):
                yield json.loads(line[6:])