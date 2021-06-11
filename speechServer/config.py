
# --- LOG ---
LOG = {"screen": True, "file": True, "log_file": open("./log.txt", "a"), "debug": False}
SID_LENGTH = 32

# --- REDIS ---
REDIS_URL = 'redis://localhost:6379/'
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# --- CHANNEL --
GOOGLE_CONNECT_CHANNEL = "google_connect"
GOOGLE_DISCONNECT_CHANNEL = "google_disconnect"
GOOGLE_ASR_RESULT_CHANNEL = "google_result"
GOOGLE_AUDIO_CHANNEL = "google_audios"


# --- websocket --
WEBSOCKETS_TIME_OUT = 30
RECEIVE_DATA_TIME_OUT = 5
LANGUAGES_CODE = {
    ""
}

# -- system --
# second
WEBSOCKETS_SURVIVAL_TIME = 120