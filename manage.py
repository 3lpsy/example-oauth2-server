#!/usr/bin/env python3

import sys
from pathlib import Path
import argparse

from app import app, initialize_database, list_urls

def create_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='command to run', dest='command')
    run_parser = subparsers.add_parser('run', help='run server')
    run_parser.add_argument('--host', type=str, default="127.0.0.1", help="server host")
    run_parser.add_argument('--port', default=5555, type=int, help="server port")
    run_parser.add_argument('--debug', action="store_true", default=False, help="server debug mode")

    run_parser.add_argument('--cert', type=str, required=False, help="ssl certificate")
    run_parser.add_argument('--cert-key', type=str, required=False, help="ssl private key")
    db_parser = subparsers.add_parser('initdb', help='initialize db')
    urls_parser = subparsers.add_parser('urls', help='initialize db')
    return parser

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    commands = ['run', 'initdb', 'urls']
    command = args.command
    if command not in commands:
        print('[!] Command {} not found. Please use command from {}'.format(command, commands))
        sys.exit(1)
    if command == 'run':
        host = args.host
        port = args.port
        debug = args.debug
        if args.cert and args.cert_key:
            context = (args.cert, args.cert_key)
            print('[*] Running on {}:{} with SSL context {} (Debug: {})'.format(host, port, context, debug))
            app.run(host=host, port=port, ssl_context=context, debug=debug)
        else:
            print('[*] Running on {}:{} (Debug: {})'.format(host, port, debug))
            app.run(host=args.host, port=args.port, debug=args.debug)
    elif command == 'initdb':
        print('[*] Initializing database')
        initialize_database(app)
    elif command == 'urls':
        print('[*] Listing urls')
        list_urls(app)
