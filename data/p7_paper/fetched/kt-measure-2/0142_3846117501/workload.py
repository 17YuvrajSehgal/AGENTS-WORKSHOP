import os, sys, hashlib, logging, shutil

side = os.path.basename(os.path.dirname(os.path.abspath(sys.prefix)))
SRC = os.path.join(os.path.dirname(os.path.abspath(sys.prefix)), "src")
sys.path.insert(0, SRC)

# Redirect the app's runtime data directories (db/logs/config/downloads) to /tmp
# instead of writing into the source tree (utils.get_app_root_dir honours sys.frozen).
ROOT = f"/tmp/kt_19/{side}/app"
shutil.rmtree(ROOT, ignore_errors=True)
os.makedirs(ROOT, exist_ok=True)
sys.frozen = True
sys.executable = os.path.join(ROOT, "python")

logging.disable(logging.CRITICAL)

from modules import task_manager as tm  # noqa: E402
from modules.subtitle_translator import SubtitleTranslator, TranslationConfig  # noqa: E402

WORDS = ["hello", "world", "video", "great", "today", "music", "really", "think",
         "people", "going", "about", "something", "watch", "time", "know"]


class FakeLLM:
    """Stand-in for the OpenAI network client: deterministic 'translation'."""
    def translate_batch(self, texts, target_language, batch_id=""):
        out = []
        for t in texts:
            h = hashlib.md5(t.encode()).hexdigest()
            out.append("1. 翻译" + "".join(chr(0x4E00 + int(h[i:i + 2], 16)) for i in range(0, 16, 2)))
        return out

    def translate_batch_strict(self, texts, target_language, batch_id=""):
        return self.translate_batch(texts, target_language, batch_id)


def make_srt(path, n, seed):
    lines = []
    for i in range(n):
        s = i * 2
        words = [WORDS[(i * 7 + seed * 3 + k * 5) % len(WORDS)] for k in range(6 + i % 5)]
        lines.append(f"{i+1}\n00:{s//60:02d}:{s%60:02d},000 --> 00:{(s+1)//60:02d}:{(s+1)%60:02d},500\n{' '.join(words)}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


h = hashlib.sha256()
work = f"/tmp/kt_19/{side}/subs"
os.makedirs(work, exist_ok=True)

for rnd in range(4):
    cfg = TranslationConfig(batch_size=5, max_workers=4, retry_delay=0)
    tr = SubtitleTranslator(cfg, task_id=f"wl{rnd}")
    tr.llm_requester = FakeLLM()
    inp = os.path.join(work, f"in{rnd}.srt")
    out = os.path.join(work, f"out{rnd}.srt")
    make_srt(inp, 1500, rnd)
    prog = []
    ok = tr.translate_file(inp, out, progress_callback=lambda p, c, t: prog.append(c))
    h.update(repr((ok, max(prog) if prog else 0)).encode())
    with open(out, "rb") as f:
        h.update(f.read())

# Task deletion paths (delete_task / clear_all_tasks) on a local SQLite DB
for rnd in range(3):
    conn = tm.get_db_connection()
    ids = [f"task-{rnd}-{i:04d}" for i in range(300)]
    conn.executemany("INSERT INTO tasks (id, youtube_url, status) VALUES (?, ?, ?)",
                     [(t, f"https://example.invalid/{t}", tm.TASK_STATES['PENDING']) for t in ids])
    conn.commit()
    conn.close()
    res = [tm.delete_task(t, delete_files=True) for t in ids[:150]]
    res.append(tm.delete_task("missing-task"))
    res.append(tm.clear_all_tasks(delete_files=True))
    res.append(len(tm.get_all_tasks()))
    h.update(repr(res).encode())

# TaskProcessor.process_task over tasks whose stages are all checkpointed as done
import json as _json
proc = tm.TaskProcessor({
    'TRANSLATE_TITLE': True, 'GENERATE_TAGS': True, 'RECOMMEND_PARTITION': True,
    'CONTENT_MODERATION_ENABLED': True, 'SUBTITLE_TRANSLATION_ENABLED': True,
    'AUTO_MODE_ENABLED': True, 'MAX_CONCURRENT_TASKS': 2,
    'PENDING_SCAN_INTERVAL_SECONDS': 3600,
})
subfile = os.path.join(work, "out0.srt")
cp = _json.dumps({'version': 1, 'completed': list(tm.PIPELINE_STAGE_ORDER), 'updated_at': None})


def insert_done_task(tid):
    conn = tm.get_db_connection()
    conn.execute(
        "INSERT INTO tasks (id, youtube_url, status, video_title_original, video_title_translated, "
        "tags_generated, recommended_partition_id, moderation_result, subtitle_path_translated, "
        "acfun_upload_response, pipeline_checkpoint) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (tid, f"https://example.invalid/{tid}", tm.TASK_STATES['DOWNLOADED'], "orig", "译",
         "[]", "63", '{"pass": true}', subfile, '{"ac": 1}', cp))
    conn.commit()
    conn.close()


pt = []
for i in range(40):
    tid = f"proc-{i:03d}"
    insert_done_task(tid)
    proc.process_task(tid)
    t = tm.get_task(tid)
    pt.append((t['status'], t.get('error_message')))
# A task that was deleted (cancel requested in head) and re-created with the same id
tid = "proc-deleted"
insert_done_task(tid)
tm.delete_task(tid)
insert_done_task(tid)
proc.process_task(tid)
t = tm.get_task(tid)
pt.append(("deleted-then-recreated", t['status'], t.get('error_message')))
proc.shutdown()
tm.clear_all_tasks()
h.update(repr(pt).encode())


# --- AcFun upload flow against a local in-process HTTP server (stand-in for AcFun/Kuaishou) ---
import json, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from PIL import Image
from modules.acfun_uploader import AcfunUploader

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a):
        pass
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else b""
        p = self.path.split("?")[0]
        if p == "/login":
            r = {"result": 0}
        elif p == "/token":
            r = {"taskId": 12345, "token": "tok", "uploadConfig": {"partSize": 65536}}
        elif p in ("/fragment", "/complete"):
            r = {"result": 1, "n": len(body)}
        elif p == "/finish":
            r = {"result": 0}
        elif p == "/cvideo":
            r = {"result": 0, "videoId": 777}
        elif p == "/qiniu":
            r = {"info": {"token": "ctok"}}
        elif p == "/cover":
            r = {"url": "http://cover.invalid/c.jpg"}
        elif p == "/douga":
            r = {"result": 0, "dougaId": 4242}
        else:
            r = {"result": -1}
        data = json.dumps(r).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
srv.daemon_threads = True
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

acdir = f"/tmp/kt_19/{side}/acfun"
os.makedirs(acdir, exist_ok=True)
video = os.path.join(acdir, "v.mp4")
with open(video, "wb") as f:
    f.write(bytes((i * 31 + 7) % 256 for i in range(65536)) * 24)
cover = os.path.join(acdir, "c.jpg")
Image.new("RGB", (640, 360), (40, 90, 160)).save(cover)

temp_dir = os.path.join(SRC, "temp")
temp_existed = os.path.exists(temp_dir)
os.environ["NO_PROXY"] = "127.0.0.1"
for rnd in range(4):
    up = AcfunUploader("user", "pw", cookie_file=os.path.join(acdir, f"ck{rnd}.txt"))
    up.LOGIN_URL = base + "/login"
    up.TOKEN_URL = base + "/token"
    up.FRAGMENT_URL = base + "/fragment"
    up.COMPLETE_URL = base + "/complete"
    up.FINISH_URL = base + "/finish"
    up.C_VIDEO_URL = base + "/cvideo"
    up.C_DOUGA_URL = base + "/douga"
    up.QINIU_URL = base + "/qiniu"
    up.COVER_URL = base + "/cover"
    res = up.upload_video(video, cover, "T" * 60, "desc  text " * 50, [f"t{i}" for i in range(8)],
                          "63", original_url="https://www.youtube.com/watch?v=x" if rnd % 2 else None,
                          original_uploader="u", original_upload_date="20240101", task_id=f"ac{rnd}")
    h.update(repr(res).encode())
srv.shutdown()
if not temp_existed:
    shutil.rmtree(temp_dir, ignore_errors=True)

print(h.hexdigest())
