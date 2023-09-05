import sys # take command line arguments

#* constants
SERVER_IP = sys.argv[1] if len(sys.argv) > 1 else "tenbin-b735da2f640d.herokuapp.com"
SSL = sys.argv[2]=="True" if len(sys.argv) > 2 else True
SERVER_URL = f'http{"s" if SSL else ""}://{SERVER_IP}'
WSS_URL = f'ws{"s" if SSL else ""}://{SERVER_IP}/game'

CLIENT_VERSION = "20230811.dev"