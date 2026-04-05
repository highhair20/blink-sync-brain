"""
Shared async utilities for Blink Lens core modules.
"""

import asyncio
import subprocess
from typing import List


# Human-readable hints for common rsync exit codes.
_RSYNC_ERROR_HINTS = {
    1:  "syntax error — check rsync is installed on Pi #2",
    5:  "could not connect to Pi #2 — check that Pi #2 is online and SSH is working",
    10: "network error — check the connection between Drive Pi and Processor Pi",
    11: "file I/O error on Pi #2 — disk may be full or permissions may be wrong",
    23: "partial transfer — some files could not be transferred (check permissions on Pi #2)",
    35: "connection timed out — Pi #2 may be offline or overloaded",
}


def rsync_error_message(returncode: int, stderr: str) -> str:
    """Return a user-friendly error message for an rsync failure."""
    hint = _RSYNC_ERROR_HINTS.get(returncode, f"rsync error (code {returncode})")
    detail = stderr.strip()
    return f"{hint}: {detail}" if detail else hint


async def run_command(cmd: List[str]) -> subprocess.CompletedProcess:
    """Run a shell command asynchronously and return a CompletedProcess."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return subprocess.CompletedProcess(
        cmd, process.returncode, stdout.decode(), stderr.decode()
    )
