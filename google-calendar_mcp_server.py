#!/usr/bin/env python3
"""MCP Server for Google Calendar API."""

import logging

from fastmcp import FastMCP

from google_calendar_mcp.cli import parse_args
from google_calendar_mcp.config import configure_logging
from google_calendar_mcp.tools import register_tools

configure_logging()
logger = logging.getLogger("calendar-mcp-server")

mcp = FastMCP("CL Google Calendar MCP Server")
register_tools(mcp)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Google Calendar MCP Server Starting")
    logger.info("=" * 60)

    args = parse_args()

    run_kwargs = {}
    if args.transport:
        run_kwargs["transport"] = args.transport
        logger.info(f"Transport: {args.transport}")
    if args.host:
        run_kwargs["host"] = args.host
        logger.info(f"Host: {args.host}")
    if args.port:
        run_kwargs["port"] = args.port
        logger.info(f"Port: {args.port}")

    try:
        mcp.run(**run_kwargs)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server crashed: {e}", exc_info=True)
        raise
