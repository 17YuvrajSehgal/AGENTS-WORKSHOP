import os, sys, hashlib, random, warnings
warnings.simplefilter("ignore")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from unittest.mock import MagicMock
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from iPhoto.gui.ui.models.roles import Roles
from iPhoto.gui.ui.models.proxy_filter import AssetFilterProxyModel
from iPhoto.gui.ui.models.asset_list_model import AssetListModel

app = QApplication.instance() or QApplication([])
rng = random.Random(1234)
N = 10000
rows = []
for i in range(N):
    rows.append({
        "rel": f"album/img_{rng.randrange(10**6):06d}_{i}.jpg",
        "id": f"id{i}",
        "dt_sort": float(rng.randrange(2000)) if rng.random() > 0.05 else float("-inf"),
        "is_video": rng.random() < 0.2,
        "is_live": rng.random() < 0.1,
        "featured": rng.random() < 0.1,
    })

src = AssetListModel(MagicMock())
src._state_manager.set_rows(rows)
proxy = AssetFilterProxyModel()
proxy.setSourceModel(src)
proxy.setSortRole(Roles.DT)

h = hashlib.sha256()
def snap():
    n = proxy.rowCount()
    h.update(str(n).encode())
    for r in range(0, n, 37):
        h.update(str(proxy.data(proxy.index(r, 0), Roles.REL)).encode())
    return n

for rep in range(3):
    proxy.sort(0, Qt.SortOrder.AscendingOrder); snap()
    proxy.sort(0, Qt.SortOrder.DescendingOrder); snap()
    for _ in range(5):
        proxy.invalidateFilter(); snap()

proxy.set_filter_mode("videos"); print("videos", snap())
proxy.set_filter_mode(None); proxy.set_search_text("img_1"); print("search", snap())
proxy.set_search_text(""); print("all", snap())
print(h.hexdigest())
