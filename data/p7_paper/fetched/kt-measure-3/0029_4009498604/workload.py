import asyncio, hashlib, os, random, struct, sys

SRC = os.path.normpath(os.path.join(sys.prefix, "..", "src"))
os.chdir(SRC)
sys.path.insert(0, SRC)
ENV = dict(
    APP_HOST="127.0.0.1", APP_PORT="10000", DOMAIN="example.com",
    DB_USER="u", DB_PASS="p", DB_NAME="db", DB_HOST="localhost", DB_PORT="3306",
    REDIS_USER="default", REDIS_PASS="", REDIS_HOST="localhost", REDIS_PORT="6379", REDIS_DB="0",
    OSU_API_KEY="", DATA_DIRECTORY="/tmp/kt_748/.data",
    SSL_CERT_PATH="/tmp/x.crt", SSL_KEY_PATH="/tmp/x.key",
    MIRROR_SEARCH_ENDPOINT="http://localhost/s", MIRROR_DOWNLOAD_ENDPOINT="http://localhost/d",
    COMMAND_PREFIX="!", SEASONAL_BGS="a,b", MENU_ICON_URL="http://localhost/i",
    MENU_ONCLICK_URL="http://localhost", DATADOG_API_KEY="", DATADOG_APP_KEY="",
    DEBUG="False", REDIRECT_OSU_URLS="True", PP_CACHED_ACCS="90,95,98,99,100",
    DISALLOWED_NAMES="mrekk", DISALLOWED_PASSWORDS="password", DISALLOW_OLD_CLIENTS="False",
    DISALLOW_INGAME_REGISTRATION="True", DISCORD_AUDIT_LOG_WEBHOOK="", DISCORD_INVITE="x",
    AUTOMATICALLY_REPORT_PROBLEMS="False", LOG_WITH_COLORS="False", TUNNEL_TOKEN="x",
    DEVELOPER_MODE="False",
)
for k, v in ENV.items():
    os.environ[k] = v

import random as _random
_random.seed(748)
import bcrypt
import app  # noqa
import app.state
import app.packets
from app.api.domains import cho
from app.constants.gamemodes import GameMode
from app.constants.privileges import Privileges
from app.objects.player import ModeData, Player

rng = random.Random(748)
players = app.state.sessions.players
N_PLAYERS = 300
for i in range(N_PLAYERS):
    priv = Privileges.UNRESTRICTED | Privileges.VERIFIED
    if i % 17 == 0:
        priv = Privileges.VERIFIED  # restricted
    p = Player(id=1000 + i, name=f"user{i}", priv=priv, pw_bcrypt=None, token=f"tok{i}")
    for m in GameMode:
        p.stats[m] = ModeData(
            tscore=rng.randint(0, 10**9), rscore=rng.randint(0, 10**8),
            pp=rng.randint(0, 80000), acc=rng.uniform(80, 100),
            plays=rng.randint(0, 5000), playtime=rng.randint(0, 10**6),
            max_combo=rng.randint(0, 3000), total_hits=rng.randint(0, 10**6),
            rank=rng.randint(1, 10**5), grades={},
        )
    players.append(p)

bot = Player(id=1, name="BanchoBot", priv=Privileges.UNRESTRICTED, pw_bcrypt=None, token="", is_bot_client=True)
for m in GameMode:
    bot.stats[m] = ModeData(tscore=0, rscore=0, pp=0, acc=0.0, plays=0, playtime=0, max_combo=0, total_hits=0, rank=0, grades={})
app.state.sessions.bot = bot


def wstr(s):
    if not s:
        return b"\x00"
    b = s.encode()
    out = bytearray(b"\x0b")
    n = len(b)
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            break
    return bytes(out) + b


def change_action_packet(action, text, md5, mods, mode, map_id):
    body = bytes([action]) + wstr(text) + wstr(md5) + struct.pack("<IBi", mods, mode, map_id)
    return struct.pack("<HxI", 0, len(body)) + body


packet_map = app.state.packets["all"]


class FakeDB:
    """Stand-in for the MySQL client (external service)."""

    def __init__(self):
        self.n = 0
        self.next_user = None

    async def execute(self, query, params=None):
        self.n += 1
        return 0

    async def fetch_one(self, query, params=None):
        self.n += 1
        if self.next_user is not None and "users" in str(query):
            return dict(self.next_user)
        return {"id": 1}

    async def fetch_all(self, query, params=None):
        self.n += 1
        if "stats" not in str(query):
            return []
        rows = []
        for m in (0, 1, 2, 3, 4, 5, 6, 8):
            rows.append(dict(
                id=1, mode=m, tscore=rng.randint(0, 10**9), rscore=rng.randint(0, 10**8),
                pp=rng.randint(0, 20000), acc=rng.uniform(80, 100), plays=rng.randint(0, 5000),
                playtime=rng.randint(0, 10**6), max_combo=rng.randint(0, 3000),
                total_hits=rng.randint(0, 10**6), replay_views=0,
                xh_count=1, x_count=2, sh_count=3, s_count=4, a_count=5,
            ))
        return rows


class FakeRedis:
    """Stand-in for the Redis client (external service)."""

    async def zrevrank(self, key, member):
        return (int(member) * 7 + len(key)) % 1000

    async def zadd(self, key, mapping):
        return 1


db = FakeDB()
app.state.services.database = db
app.state.services.redis = FakeRedis()


async def main():
    app.state.loop = asyncio.get_running_loop()
    h = hashlib.sha256()
    for it in range(2500):
        p = players[rng.randrange(N_PLAYERS)]
        mods = rng.choice([0, 8, 64, 128, 8192, 16])
        pkt = change_action_packet(
            rng.randrange(0, 13), f"Artist - Title [{it}]",
            hashlib.md5(str(it).encode()).hexdigest(), mods,
            rng.randrange(0, 4), rng.randint(1, 4000000),
        )
        with memoryview(pkt) as view:
            for packet in app.packets.BanchoPacketReader(view, packet_map):
                await packet.handle(p)
        if it % 50 == 49:
            for q in players:
                d = q.dequeue()
                if d:
                    h.update(d)
    for it in range(1500):
        p = players[rng.randrange(N_PLAYERS)]
        k = it % 4
        if k == 0:
            await p.stats_from_sql_full()
        elif k == 1:
            await p.add_privs(Privileges.SUPPORTER)
        elif k == 2:
            await p.remove_privs(Privileges.SUPPORTER)
        else:
            await p.update_privs(p.priv)
        h.update(app.packets.user_stats(p))
        h.update(app.packets.user_presence(p))
    pw_md5 = hashlib.md5(b"hunter2").hexdigest().encode()
    pw_bcrypt = bcrypt.hashpw(pw_md5, b"$2b$04$abcdefghijklmnopqrstuu").decode()
    headers = {"CF-IPCountry": "CA", "CF-IPLatitude": "43.1", "CF-IPLongitude": "-79.2"}
    import ipaddress
    ip = ipaddress.ip_address("10.0.0.1")
    for i in range(60):
        name = f"login{i}"
        db.next_user = dict(
            id=50000 + i, name=name, safe_name=name, priv=int(Privileges.UNRESTRICTED | Privileges.VERIFIED),
            pw_bcrypt=pw_bcrypt, country="ca", silence_end=0, donor_end=0, creation_time=0,
            latest_activity=0, clan_id=0, clan_priv=0, preferred_mode=0, play_style=0,
            custom_badge_name=None, custom_badge_icon=None, userpage_content=None, api_key=None,
        )
        md5 = hashlib.md5(name.encode()).hexdigest()
        body = (f"{name}\n{pw_md5.decode()}\nb20240123|-5|0|{md5}:aa.bb.:{md5}:{md5}:{md5}:|0\n").encode()
        resp = await cho.handle_osu_login_request(headers, body, ip)
        h.update(resp["response_body"])
        db.next_user = None
        # a few status changes after each login
        for _ in range(5):
            p = players[rng.randrange(len(players))]
            pkt = change_action_packet(rng.randrange(0, 13), "x", "y", 0, rng.randrange(4), 1)
            with memoryview(pkt) as view:
                for packet in app.packets.BanchoPacketReader(view, packet_map):
                    await packet.handle(p)
    for _ in range(3):
        await asyncio.sleep(0)
    for q in players:
        d = q.dequeue()
        if d:
            h.update(d)
    print(h.hexdigest())


asyncio.run(main())
