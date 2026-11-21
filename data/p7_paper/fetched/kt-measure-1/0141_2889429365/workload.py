import hashlib
import os
os.environ.setdefault('MEM0_DIR', '/tmp/kt_230/mem0')
os.environ.setdefault('CREWAI_STORAGE_DIR', '/tmp/kt_230/crewai')
os.environ.setdefault('EMBEDCHAIN_CONFIG_DIR', '/tmp/kt_230')
import selenium.webdriver as _wd
from selenium.webdriver.common.by import By

# Stand-in for the Chrome browser (no browser available here).
class FakeElement:
    def __init__(self, tag, text):
        self.tag = tag
        self.text = text
    def get_attribute(self, name):
        if name == "outerHTML":
            return f"<{self.tag}>{self.text}</{self.tag}>"
        return None

class FakeChrome:
    def __init__(self, *args, **kwargs):
        self.url = None
        self.log = []
        self.cookies = []
    def __call__(self, *args, **kwargs):  # base calls self.driver(options=...)
        return self
    def get(self, url):
        self.url = url
        self.log.append(("get", url))
    def add_cookie(self, c):
        self.cookies.append(c)
        self.log.append(("cookie", tuple(sorted(c.items()))))
    def find_element(self, by, value):
        return FakeElement("body", f"body of {self.url}")
    def find_elements(self, by, value):
        return [FakeElement("div", f"{value} #{i} @ {self.url}") for i in range(5)]
    def close(self):
        self.log.append(("close",))
    def quit(self):
        self.log.append(("quit",))
        if len(self.log) % 2:
            raise RuntimeError("browser already gone")

_wd.Chrome = FakeChrome

from crewai_tools.tools.selenium_scraping_tool.selenium_scraping_tool import SeleniumScrapingTool

h = hashlib.sha256()
for i in range(400):
    cookie = {"name": "k", "value": str(i)} if i % 3 == 0 else None
    tool = SeleniumScrapingTool(website_url=f"https://example.com/{i}", cookie=cookie,
                                css_element="div.x" if i % 2 else None)
    tool.wait_time = 0
    for j in range(3):
        r = tool._run(website_url=f"https://example.com/{i}/{j}", return_html=bool(j % 2))
        h.update(r.encode())
    d = tool.driver
    tool.close()
    h.update(repr(d.log if d is not None else None).encode())
    h.update(tool.description.encode())
print(h.hexdigest())
