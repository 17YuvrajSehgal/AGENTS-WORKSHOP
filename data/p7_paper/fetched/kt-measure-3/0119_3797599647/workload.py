import hashlib, os, shutil, sqlite3, sys, time
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import iPhoto  # locate this venv's source tree
sys.path.insert(0, str(Path(iPhoto.__file__).resolve().parent.parent.parent))

from PySide6.QtWidgets import QApplication, QStackedWidget, QStatusBar, QWidget, QMainWindow
from src.iPhoto.config import RECENTLY_DELETED_DIR_NAME
from src.iPhoto.cache.index_store import IndexStore
from src.iPhoto.library.manager import LibraryManager
from src.iPhoto.gui.ui.controllers.navigation_controller import NavigationController
from src.iPhoto.gui.ui.controllers.view_controller import ViewController

app = QApplication.instance() or QApplication([])


class Facade:
    def __init__(self):
        self.current_album = None
        self.open_requests = []

    def open_album(self, root):
        self.open_requests.append(root)
        album = SimpleNamespace(root=root.resolve(), manifest={"title": root.name})
        self.current_album = album
        return album

    def library_model_has_cached_data(self):
        return False


class AssetModel:
    def set_filter_mode(self, mode):
        self.filter_mode = mode

    def rowCount(self):
        return 0

    def ensure_chronological_order(self):
        pass


class Sidebar:
    def select_path(self, path):
        pass

    def select_static_node(self, title):
        pass


class Dialog:
    def bind_library_dialog(self):
        pass

    def show_error(self, msg):
        pass


class Context:
    def __init__(self, library):
        self.library = library
        self.facade = None

    def remember_album(self, root):
        pass


def make_view():
    stack = QStackedWidget()
    g, d, e = QWidget(), QWidget(), QWidget()
    for w in (g, d, e):
        stack.addWidget(w)
    vc = ViewController(stack, g, d, e)
    vc._keep = (stack, g, d, e)
    return vc


base = Path("/tmp/kt_516")
shutil.rmtree(base, ignore_errors=True)
lib_root = base / "Library"
lib_root.mkdir(parents=True)

manager = LibraryManager()
manager.bind_path(lib_root)
trash = manager.ensure_deleted_directory()

results = []


def wait_cleanup(controller):
    deadline = time.monotonic() + 20
    while True:
        app.processEvents()
        if not getattr(controller, "_trash_cleanup_running", False):
            break
        if time.monotonic() > deadline:
            break
        time.sleep(0.001)
    app.processEvents()


def open_trash(before_events=None):
    facade = Facade()
    ctx = Context(manager)
    ctx.facade = facade
    vc = make_view()
    controller = NavigationController(
        ctx, facade, AssetModel(), Sidebar(), QStatusBar(), Dialog(), vc, QMainWindow()
    )
    controller.open_recently_deleted()
    if before_events is not None:
        before_events()
    wait_cleanup(controller)
    return controller, facade


def snapshot():
    return sorted(r.get("rel") for r in IndexStore(lib_root).read_all())


def record(tag, controller, facade, remaining):
    results.append((tag, len(facade.open_requests), controller.static_selection(), len(remaining),
                    hashlib.sha256("\n".join(remaining).encode()).hexdigest()[:16]))
    print(results[-1][:4])


def fill(it, mode, n):
    for p in trash.iterdir():
        p.unlink()
    rels = []
    for i in range(n):
        name = f"img_{it}_{i}.jpg"
        rel = f"{RECENTLY_DELETED_DIR_NAME}/{name}"
        rels.append(rel)
        if (mode in (0, 3) and i % 2 == 0) or mode == 2:
            (trash / name).write_bytes(b"x" * 16)
    store = IndexStore(lib_root)
    if mode == 2:
        # trash files exist but nothing in the index points to the trash
        store.write_rows([{"rel": f"Album/{r}", "id": f"id:a:{r}"} for r in rels])
    elif mode == 3:
        store.write_rows([{"rel": r, "id": f"id:{r}"} for i, r in enumerate(rels) if i % 2 == 0])
    else:
        store.write_rows([{"rel": r, "id": f"id:{r}"} for r in rels])


ITER = 40
N = 400
for it in range(ITER):
    fill(it, it % 4, N)
    c, f = open_trash()
    record(it, c, f, snapshot())

db = lib_root / ".iPhoto" / "global_index.db"


def reset_db():
    for suffix in ("", "-wal", "-shm"):
        Path(str(db) + suffix).unlink(missing_ok=True)


def corrupt_db():
    con = sqlite3.connect(db)
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    con.close()
    for suffix in ("-wal", "-shm"):
        Path(str(db) + suffix).unlink(missing_ok=True)
    data = bytearray(db.read_bytes())
    for k in range(4096, len(data)):
        data[k] = 0xA5
    db.write_bytes(bytes(data))


# Unreadable trash folder
fill(100, 0, 50)
os.chmod(trash, 0)
c, f = open_trash()
os.chmod(trash, 0o755)
record("noperm", c, f, snapshot())

# Trash folder disappears (dangling link) before background work starts
fill(101, 0, 50)
def _dangle():
    shutil.rmtree(trash)
    os.symlink(base / "nowhere", trash)
c, f = open_trash(_dangle)
os.unlink(trash)
trash.mkdir()
record("dangling", c, f, snapshot())

# Trash folder is a link pointing outside the library
outside = base / "outside"
outside.mkdir()
shutil.rmtree(trash)
os.symlink(outside, trash)
(outside / "a.jpg").write_bytes(b"x")
c, f = open_trash()
os.unlink(trash)
trash.mkdir()
record("outside", c, f, snapshot())

# Damaged index database, with and without files in the trash
for tag, mode in (("corrupt_files", 0), ("corrupt_empty", 1)):
    fill(102, mode, 300)
    corrupt_db()
    c, f = open_trash()
    reset_db()
    record(tag, c, f, snapshot())

print(hashlib.sha256(repr(results).encode()).hexdigest())
