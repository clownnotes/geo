# -*- coding: utf-8 -*-
"""
GEO Worker 命令行入口 (python3 -m tools.worker --host 127.0.0.1 --port 18092)
"""

import sys
import argparse
from tools.worker.app import create_server, DEFAULT_HOST, DEFAULT_PORT, validate_bind_host
from tools.worker.auth import get_expected_token, ENV_INTERNAL_TOKEN


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="GEO Stateless Asynchronous Worker Service")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Bind port (default: 18092)")
    return parser.parse_args()


def main():
    """主启动函数"""
    args = parse_args()
    try:
        host = validate_bind_host(args.host)
    except ValueError as err:
        sys.stderr.write(f"Startup Error: {str(err)}\n")
        sys.exit(1)

    token = get_expected_token()
    if not token:
        sys.stderr.write(f"Startup Warning: {ENV_INTERNAL_TOKEN} environment variable is not configured.\n")

    server = create_server(host=host, port=args.port)
    sys.stdout.write(f"GEO Worker started at http://{host}:{args.port}\n")
    sys.stdout.flush()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stdout.write("GEO Worker shutting down...\n")
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
