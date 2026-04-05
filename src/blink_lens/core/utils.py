"""
Shared async utilities for Blink Lens core modules.
"""

import asyncio
import subprocess
from typing import List


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
