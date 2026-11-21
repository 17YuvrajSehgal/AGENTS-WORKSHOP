"""Workload for DefaultActionWatchdog typing paths (_type_to_page, _input_text_element_node_impl).

No browser is available here, so the Chrome DevTools connection (external I/O)
is replaced by an in-process stand-in that records dispatched CDP commands.
The watchdog code, asyncio event loop and sleeps run unmodified.
"""
import asyncio
import hashlib
import json
import logging
import os

os.environ['XDG_CONFIG_HOME'] = '/tmp/kt_2727/config'
os.environ['XDG_CACHE_HOME'] = '/tmp/kt_2727/cache'
os.environ['BROWSER_USE_CONFIG_DIR'] = '/tmp/kt_2727/config/browseruse'
os.environ['ANONYMIZED_TELEMETRY'] = 'false'
os.environ['BROWSER_USE_CLOUD_SYNC'] = 'false'
from types import SimpleNamespace

from bubus import EventBus
from browser_use.browser.default_action_watchdog import DefaultActionWatchdog


class FakeCDPBrowser:
	def __init__(self):
		self.log = []
		self.typed = []

	async def call(self, domain, method, params=None, session_id=None):
		self.log.append((domain, method, json.dumps(params, sort_keys=True), session_id))
		if domain == 'Input' and method == 'dispatchKeyEvent' and params.get('type') == 'char':
			self.typed.append(params['text'])
		if domain == 'DOM' and method == 'resolveNode':
			return {'object': {'objectId': f'obj-{params["backendNodeId"]}'}}
		if domain == 'Runtime' and method == 'callFunctionOn' and params.get('returnByValue'):
			return {'result': {'value': {'visible': True, 'focusable': True, 'interactive': True, 'disabled': False,
				'bounds': {'x': 10, 'y': 20, 'width': 100, 'height': 30}, 'tagName': 'input', 'type': 'text'}}}
		return {}


class _Domain:
	def __init__(self, b, d):
		self._b, self._d = b, d

	def __getattr__(self, m):
		async def f(params=None, session_id=None):
			return await self._b.call(self._d, m, params, session_id)
		return f


class _Send:
	def __init__(self, b):
		self._b = b

	def __getattr__(self, d):
		return _Domain(self._b, d)


def make_watchdog(browser):
	client = SimpleNamespace(send=_Send(browser))
	cdp_session = SimpleNamespace(cdp_client=client, session_id='sess-1', target_id='target-1')

	async def get_or_create_cdp_session(target_id=None, focus=True):
		return cdp_session

	logger = logging.getLogger('workload')
	logger.setLevel(logging.CRITICAL)
	session = SimpleNamespace(cdp_client=client, logger=logger, get_or_create_cdp_session=get_or_create_cdp_session)
	return DefaultActionWatchdog.model_construct(event_bus=EventBus(), browser_session=session)


async def main():
	browser = FakeCDPBrowser()
	wd = make_watchdog(browser)
	texts = ['The quick brown fox jumps over the lazy dog. ' * 2, 'hello@example.com', 'Search query 42']
	for t in texts:
		await wd._type_to_page(t)
	node = SimpleNamespace(target_id='target-1', backend_node_id=1234)
	for t in ['user name 12', 'secret-pass-99']:
		await wd._input_text_element_node_impl(node, t, clear_existing=True)
	return browser


browser = asyncio.run(main())
typed = ''.join(browser.typed)
print('commands:', len(browser.log))
print('typed:', typed)
print(hashlib.sha256(json.dumps(browser.log).encode()).hexdigest())
