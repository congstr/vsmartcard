#!/usr/bin/env python3
"""Check that a silent or truncated VICC reply cannot block VPCD indefinitely.

Run on Linux with: python3 tests/test_vpcd_timeout.py
"""

import socket
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def probe(binary, reply, mode):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        if mode == "client":
            listener.listen(1)
        else:
            listener.close()
        process = subprocess.Popen(
            [str(binary), mode, str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if mode == "client":
            listener.settimeout(2)
            peer = listener.accept()[0]
        else:
            for attempt in range(40):
                try:
                    peer = socket.create_connection(("127.0.0.1", port), timeout=2)
                    break
                except ConnectionRefusedError:
                    time.sleep(0.05)
            else:
                process.kill()
                process.communicate()
                raise AssertionError("VPCD did not start listening")
        with peer:
            peer.settimeout(2)
            request = b""
            while len(request) < 3:
                request += peer.recv(3 - len(request))
            assert request == b"\x00\x01\x04"
            if reply:
                peer.sendall(reply)
            try:
                stdout, stderr = process.communicate(timeout=3.5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise AssertionError("VPCD blocked on a relay response") from None
    assert not stderr, stderr
    return process.returncode, stdout.strip()


def main():
    with tempfile.TemporaryDirectory() as temporary:
        binary = Path(temporary) / "vpcd-timeout-probe"
        subprocess.run(
            [
                "cc", "-O2", "-DHAVE_DECL_MSG_NOSIGNAL=1",
                "-DVPCD_IO_TIMEOUT_SECONDS=2", "-o", str(binary),
                str(ROOT / "tests/vpcd_timeout_probe.c"),
                str(ROOT / "src/vpcd/vpcd.c"),
                str(ROOT / "src/vpcd/lock.c"),
            ],
            check=True,
        )
        for mode in ("client", "server"):
            for reply in (b"", b"\x00"):
                code, output = probe(binary, reply, mode)
                assert code == 1 and "result=-1" in output and "socket=-1" in output, output
            code, output = probe(binary, b"\x00\x02\x3b\x00", mode)
            assert code == 0 and "result=2" in output, output
    print("both modes: silent and truncated replies time out; complete ATR succeeds")


if __name__ == "__main__":
    main()
