PRODUCTION = True
SCREEN_SIZE = ""
# "" / "IPAD_LANDSCAPE" / "IPAD_PORTRAIT"
#* constants
SERVER_IP = "tenbin-b735da2f640d.herokuapp.com" if PRODUCTION else "localhost:8999"
SSL = PRODUCTION
SERVER_URL = f'http{"s" if SSL else ""}://{SERVER_IP}'
WSS_URL = f'ws{"s" if SSL else ""}://{SERVER_IP}/game'

CLIENT_VERSION = "20240811.0.app"

DISCORD_URL = "https://discord.gg/H6bsxqZyuu"
GOOGLE_PLAY_URL = "https://play.google.com/store/apps/details?id=com.kidprof.tenbin"
APP_STORE_URL = "https://play.google.com/store/apps/details?id=com.kidprof.tenbin"

#* Constants for the offline game, copied from backend
PARTICIPANTS_PER_GAME = 5
DEAD_LIMIT = -5
ROUND_LIMIT = 200;
ROUND_TIME_MS = 2 * 60 * 1000
SHORTENED_TIME_MS = 5 * 1000
SHORTENED_TIME_AMEND_MS = 30 * 1000
ROUND_ZERO_DIGEST_TIME_MS = 2 * 1000
ROUND_INFO_DIGEST_TIME_MS = 10 * 1000
DIGEST_TIME_MS = 5 * 1000
POPULATE_BOTS_TIME_MS = 15 * 1000
BOT_NICKNAMES = ["Alice","Clara","Ellen","Iris","Kate","Nora","Sarah"]