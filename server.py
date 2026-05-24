#!/usr/bin/env python3
"""MCP Server for Google Calendar API."""

import logging

from fastmcp import FastMCP
from fastmcp_credentials import CredentialMiddleware, HeaderCredentialBackend

from google_calendar_mcp.cli import parse_args
from google_calendar_mcp.config import configure_logging
from google_calendar_mcp.tools import register_tools

configure_logging()
logger = logging.getLogger("calendar-mcp-server")

backend = HeaderCredentialBackend()
mcp = FastMCP(
    "CL Google Calendar MCP Server",
    # stateless_http=True disables in-memory session management so that every
    # POST request is handled independently.  This is required when the server
    # runs behind a load balancer or on a platform that can spin up multiple
    # instances (Cloud Run, Fly.io, Kubernetes, etc.).  Without this flag,
    # FastMCP stores sessions in the memory of whichever process handled
    # `initialize`.  A subsequent tool call that lands on a *different* process
    # returns {"code":-32600,"message":"Session not found"} because that process
    # has no record of the session.
    #
    # This server is safe to run stateless because:
    #   1. The MCP Gateway injects fresh OAuth credentials (x-mcp-cred-*)
    #      on every request, so per-session credential caching is not needed.
    #   2. All tools are independent calendar API calls with no cross-request
    #      server-side state.
    #   3. The SSE server-push endpoint is not used by any connected client.
    stateless_http=True,
    middleware=[CredentialMiddleware(backend, "oauth")],
)
register_tools(mcp)

# Expose ASGI app for hosting platform's (e.g. Vercel / Cloud Run) runtime.
app = mcp.http_app(path="/mcp", transport="streamable-http")


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
