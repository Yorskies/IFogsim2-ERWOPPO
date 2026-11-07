"""Strict client for the research v2 socket server (JSON Lines, protocol research-v2.1).

There is no fallback: a wire error, hash mismatch, timeout or dropped connection raises. A lost connection is never
turned into a finished episode.
"""

import json
from pathlib import Path
import socket
import subprocess

from .config import ROOT, read_json, sha256
from .contracts import validate_contract
from .engine_runner import JAR, find_java

SERVER_CLASS = "org.fog.erwo.v2.V2SocketServer"
SCHEMA = "research-v2.1"
ZERO_HASH = "0" * 64


class RpcError(RuntimeError):
    """The server answered with status=error. `code` is the server's error code."""

    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code, self.message = code, message


class ConnectionLostError(RuntimeError):
    """The socket closed, timed out or failed. The episode in progress is lost, not completed."""


class HandshakeError(RuntimeError):
    """The server is not the build/config this client was told to use."""


def file_sha256(path):
    import hashlib
    digest = hashlib.sha256()
    digest.update(Path(path).read_bytes())
    return digest.hexdigest()


def verify_handshake(handshake, config, *, require_jar_hash=True):
    """Check the server's identity against the local build receipt, config file and wire contract."""
    problems = []
    if handshake.get("schema_version") != SCHEMA:
        problems.append(f"schema_version {handshake.get('schema_version')!r}")
    if handshake.get("config_file_sha256") != file_sha256(ROOT / "configs/research_v2/default.json"):
        problems.append("config file in the JAR differs from configs/research_v2/default.json")
    if handshake.get("wire_contract_file_sha256") != file_sha256(ROOT / "configs/research_v2/wire_contract.json"):
        problems.append("wire contract in the JAR differs from configs/research_v2/wire_contract.json")
    if handshake.get("bound_config_sha256") not in (None, sha256(config)):
        problems.append("server is bound to a different canonical config hash")
    wire = read_json(ROOT / "configs/research_v2/wire_contract.json")
    if handshake.get("observation_dimension") != len(wire["observation_features"]) or handshake.get("actions") != wire["actions"]:
        problems.append("observation dimension or action list differs from the wire contract")
    receipt_path = ROOT / "ifogsim/build/research_v2/build_receipt.json"
    if require_jar_hash:
        if not receipt_path.is_file():
            problems.append("no build receipt to compare the JAR hash with")
        elif handshake.get("jar_sha256") != read_json(receipt_path)["artifact_sha256"]:
            problems.append("running JAR differs from the JAR recorded in the build receipt")
    if problems:
        raise HandshakeError("; ".join(problems))
    return handshake


class ServerProcess:
    """A V2SocketServer child JVM bound to loopback, started with the canonical config hash."""

    def __init__(self, config, *, port=None, any_port=False, rpc_timeout_s=None, jdk_home=None):
        java = find_java(jdk_home)
        if java is None or not JAR.is_file():
            raise RuntimeError("Need a JDK >= 21 (JAVA_HOME) and the built JAR: python ifogsim/build_v2.py")
        if port is None:
            port = 0 if any_port else config["execution"]["allowed_ports"][0]
        command = [java, "-cp", str(JAR), SERVER_CLASS, "--port", str(port), "--config-sha256", sha256(config)]
        if any_port:
            command.append("--allow-any-port")
        if rpc_timeout_s is not None:
            command += ["--rpc-timeout-s", str(rpc_timeout_s)]
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", cwd=ROOT)
        line = self.process.stdout.readline()
        try:
            ready = json.loads(line)
        except json.JSONDecodeError as error:
            self.process.kill()
            self.process.wait()
            detail = self.process.stderr.read()[-400:]
            self.close()
            raise RuntimeError(f"Server did not report readiness: {line!r} {detail}") from error
        self.host, self.port = ready["host"], ready["port"]

    def stderr_tail(self, limit=2000):
        """Whatever the server wrote to stderr so far (non-blocking only if the process has exited)."""
        if self.process.poll() is None:
            return ""
        return self.process.stderr.read()[-limit:]

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
        for stream in (self.process.stdout, self.process.stderr):
            if stream:
                stream.close()


class V2Client:
    def __init__(self, host, port, *, timeout_s=120.0, validate=True):
        self.validate = validate
        self.timeout_s = timeout_s
        self._counter = 0
        try:
            self.sock = socket.create_connection((host, port), timeout=timeout_s)
        except OSError as error:
            raise ConnectionLostError(f"cannot connect to {host}:{port}: {error}") from error
        self.sock.settimeout(timeout_s)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._reader = self.sock.makefile("rb")
        self.last_request = None

    def _send(self, request):
        data = (json.dumps(request, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            self.sock.sendall(data)
        except OSError as error:
            raise ConnectionLostError(f"send failed: {error}") from error

    def _receive(self):
        try:
            line = self._reader.readline()
        except (OSError, TimeoutError) as error:
            raise ConnectionLostError(f"receive failed or timed out: {error}") from error
        if not line:
            raise ConnectionLostError("server closed the connection")
        return json.loads(line)

    def request(self, operation, *, episode_id="-", config_sha256=ZERO_HASH, trace_sha256=ZERO_HASH, action=None,
                trace=None, options=None, request_id=None, raw=False):
        """Send one request and return the validated response (raises RpcError for status=error unless `raw`)."""
        self._counter += 1
        request = {"schema_version": SCHEMA, "request_id": request_id or f"r{self._counter}", "episode_id": episode_id,
                   "config_sha256": config_sha256, "trace_sha256": trace_sha256, "operation": operation, "action": action}
        if trace is not None:
            request["trace"] = trace
        if options is not None:
            request["options"] = options
        if self.validate:
            validate_contract("rpc_request", request)
        self.last_request = request
        self._send(request)
        return self._finish(request, raw)

    def resend_last(self, *, raw=False):
        """Retry the previous request byte-for-byte (same request_id); the server must answer idempotently."""
        self._send(self.last_request)
        return self._finish(self.last_request, raw)

    def _finish(self, request, raw):
        response = self._receive()
        if self.validate:
            validate_contract("rpc_response", response)
        if response["request_id"] != request["request_id"]:
            raise ConnectionLostError(f"response for {response['request_id']!r}, expected {request['request_id']!r}")
        if response["status"] != "ok" and not raw:
            raise RpcError(response["error"]["code"], response["error"]["message"])
        return response

    def send_raw_line(self, text):
        """Test hook: send an arbitrary frame (for malformed/legacy input) and return the parsed reply."""
        try:
            self.sock.sendall(text.encode("utf-8") + b"\n")
        except OSError as error:
            raise ConnectionLostError(f"send failed: {error}") from error
        return self._receive()

    def close(self):
        try:
            self._reader.close()
            self.sock.close()
        except OSError:
            pass
