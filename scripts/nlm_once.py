#!/usr/bin/env python3
"""Run nlm CLI with automatic mutation retries disabled.

Prevents duplicate remote slide/source creation when network RPCs time out.
"""
import os
import sys

# Download commands do not expose their own profile option. This wrapper
# accepts it explicitly and isolates the subprocess before importing the CLI.
if len(sys.argv) > 2 and sys.argv[1] == "--profile":
    os.environ["NLM_PROFILE"] = sys.argv[2]
    del sys.argv[1:3]
os.environ["NOTEBOOKLM_RATE_LIMIT_MAX_RETRIES"] = "0"
import notebooklm_tools.core.base as base

base.DEFAULT_MAX_RETRIES = 0
from notebooklm_tools.cli.main import cli_main

if __name__ == "__main__":
    sys.exit(cli_main())
