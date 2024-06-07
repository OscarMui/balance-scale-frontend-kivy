PRODUCTION = False

#* constants
SERVER_IP = "tenbin-b735da2f640d.herokuapp.com" if PRODUCTION else "localhost:8999"
SSL = PRODUCTION
SERVER_URL = f'http{"s" if SSL else ""}://{SERVER_IP}'
WSS_URL = f'ws{"s" if SSL else ""}://{SERVER_IP}/game'

CLIENT_VERSION = "20240106.0.app"

DISCORD_URL = "https://discord.gg/H6bsxqZyuu"