"""Workload: DomService.get_serialized_dom_tree over a stand-in CDP client
(browser replaced by synthetic DOM / snapshot / AX data), small and large pages."""
import asyncio
import hashlib
import logging
import random

from browser_use.dom.service import DomService
from browser_use.dom.serializer.serializer import DOMTreeSerializer

logging.disable(logging.CRITICAL)


def build_page(n_items, seed):
	rnd = random.Random(seed)
	ids = iter(range(1, 10**7))
	flat = []  # (node dict, layout or None)

	def mk(node_type, name, value='', attrs=None, parent=None, layout=None):
		nid = next(ids)
		n = {'nodeId': nid, 'backendNodeId': nid + 100000, 'nodeType': node_type, 'nodeName': name,
			 'nodeValue': value, 'localName': name.lower()}
		if attrs:
			a = []
			for k, v in attrs.items():
				a += [k, v]
			n['attributes'] = a
		if parent is not None:
			n['parentId'] = parent['nodeId']
			parent.setdefault('children', []).append(n)
		flat.append((n, layout))
		return n

	vis = {'display': 'block', 'visibility': 'visible', 'opacity': '1', 'cursor': 'auto', 'overflow': 'visible'}
	doc = mk(9, '#document')
	doc['frameId'] = 'F1'
	html = mk(1, 'HTML', parent=doc, layout=((0, 0, 1280, 20000), vis, (0, 0, 1280, 800), (0, 0, 1280, 20000)))
	html['frameId'] = 'F1'
	head = mk(1, 'HEAD', parent=html)
	for t in ('META', 'TITLE', 'SCRIPT', 'STYLE', 'LINK'):
		mk(1, t, parent=head)
	body = mk(1, 'BODY', parent=html, layout=((0, 0, 1280, 20000), vis, None, None))
	y = 0
	for i in range(n_items):
		hidden = rnd.random() < 0.1
		st = dict(vis)
		if hidden:
			st['display'] = 'none'
		div = mk(1, 'DIV', attrs={'class': f'row r{i % 7}'}, parent=body,
				 layout=((0, y, 1280, 40), st, None, None))
		kind = rnd.randrange(5)
		if kind == 0:
			b = mk(1, 'BUTTON', attrs={'type': 'button', 'id': f'b{i}'}, parent=div,
				   layout=((10, y + 5, 80, 30), dict(st, cursor='pointer'), None, None))
			mk(3, '#text', f'Click {i}', parent=b, layout=((12, y + 8, 60, 20), st, None, None))
		elif kind == 1:
			a = mk(1, 'A', attrs={'href': f'/p/{i}'}, parent=div,
				   layout=((10, y + 5, 120, 20), dict(st, cursor='pointer'), None, None))
			mk(3, '#text', f'Link number {i}', parent=a, layout=((10, y + 5, 120, 20), st, None, None))
		elif kind == 2:
			mk(1, 'INPUT', attrs={'type': 'text', 'name': f'f{i}', 'placeholder': 'search'}, parent=div,
			   layout=((10, y + 5, 200, 30), st, None, None))
		elif kind == 3:
			sp = mk(1, 'SPAN', parent=div, layout=((10, y + 5, 300, 20), st, None, None))
			mk(3, '#text', f'Paragraph text {i} lorem ipsum', parent=sp, layout=((10, y + 5, 300, 20), st, None, None))
		else:
			mk(1, 'DIV', attrs={'role': 'button', 'onclick': 'x()'}, parent=div,
			   layout=((10, y + 5, 50, 0 if rnd.random() < 0.3 else 25), st, None, None))
		y += 40
	n_elements = sum(1 for n, _ in flat if n['nodeType'] == 1)
	return doc, flat, n_elements


class _NS:
	def __init__(self, handler, domain):
		self._h, self._d = handler, domain

	def __getattr__(self, method):
		async def call(params=None, session_id=None):
			await asyncio.sleep(0)
			return self._h(self._d, method, params or {})
		return call


class _Send:
	def __init__(self, handler):
		self._h = handler

	def __getattr__(self, domain):
		return _NS(self._h, domain)


class FakeCDPClient:
	"""Stand-in for the browser CDP websocket client."""

	def __init__(self, page):
		self.doc, self.flat, self.n_elements = page
		self.send = _Send(self.handle)

	def handle(self, domain, method, params):
		key = f'{domain}.{method}'
		if key == 'Runtime.evaluate':
			expr = params.get('expression', '')
			if 'querySelectorAll("*").length' in expr:
				return {'result': {'type': 'number', 'value': self.n_elements}}
			if 'readyState' in expr:
				return {'result': {'type': 'string', 'value': 'complete'}}
			return {'result': {'type': 'object', 'value': {}}}
		if key == 'DOM.getDocument':
			return {'root': self.doc}
		if key == 'DOMSnapshot.captureSnapshot':
			return self.snapshot(params)
		if key == 'Page.getLayoutMetrics':
			return {'visualViewport': {'clientWidth': 1280}, 'cssVisualViewport': {'clientWidth': 1280},
					'cssLayoutViewport': {'clientWidth': 1280}}
		if key == 'Page.getFrameTree':
			return {'frameTree': {'frame': {'id': 'F1'}, 'childFrames': []}}
		if key == 'Accessibility.getFullAXTree':
			nodes = []
			for n, _ in self.flat:
				if n['nodeType'] == 1 and n['nodeName'] in ('BUTTON', 'A', 'INPUT', 'DIV'):
					role = {'BUTTON': 'button', 'A': 'link', 'INPUT': 'textbox', 'DIV': 'generic'}[n['nodeName']]
					nodes.append({'nodeId': str(n['nodeId']), 'ignored': False, 'backendDOMNodeId': n['backendNodeId'],
								  'role': {'type': 'role', 'value': role}, 'name': {'type': 'computedString', 'value': f"n{n['nodeId']}"},
								  'properties': [{'name': 'focusable', 'value': {'type': 'boolean', 'value': role != 'generic'}}]})
			return {'nodes': nodes}
		raise RuntimeError(key)

	def snapshot(self, params):
		styles_req = params['computedStyles']
		strings = []
		sidx = {}

		def s(v):
			if v not in sidx:
				sidx[v] = len(strings)
				strings.append(v)
			return sidx[v]

		backend = []
		layout = {'nodeIndex': [], 'bounds': [], 'styles': [], 'clientRects': [], 'scrollRects': []}
		if params.get('includePaintOrder'):
			layout['paintOrders'] = []
		clickable = []
		for i, (n, lay) in enumerate(self.flat):
			backend.append(n['backendNodeId'])
			if n['nodeName'] in ('BUTTON', 'A'):
				clickable.append(i)
			if lay is None:
				continue
			bounds, st, client, scroll = lay
			layout['nodeIndex'].append(i)
			layout['bounds'].append(list(bounds))
			layout['styles'].append([s(st.get(k, '')) for k in styles_req])
			layout['clientRects'].append(list(client) if client else [])
			layout['scrollRects'].append(list(scroll) if scroll else [])
			if 'paintOrders' in layout:
				layout['paintOrders'].append(len(layout['nodeIndex']))
		return {'documents': [{'nodes': {'backendNodeId': backend, 'isClickable': {'index': clickable}}, 'layout': layout}],
				'strings': strings}


class FakeCDPSession:
	def __init__(self, client):
		self.cdp_client = client
		self.session_id = 'S1'


class FakeBrowserSession:
	"""Stand-in for BrowserSession (only the I/O surface DomService uses)."""

	def __init__(self, page):
		self.logger = logging.getLogger('kt')
		self.cdp_client = FakeCDPClient(page)
		self.current_target_id = 'T1'
		self.agent_focus = None

	async def get_or_create_cdp_session(self, target_id=None, focus=True):
		return FakeCDPSession(self.cdp_client)


def digest_tree(node, h):
	h.update(f"{node.node_id}|{node.node_name}|{node.is_visible}|{node.ax_node.role if node.ax_node else None}\n".encode())
	for c in node.children_and_shadow_roots:
		digest_tree(c, h)
	if node.content_document:
		digest_tree(node.content_document, h)


async def run():
	h = hashlib.sha256()
	pages = [build_page(300, 1), build_page(900, 2), build_page(2600, 4)]
	for page in pages:
		print('elements', page[2])
		svc = DomService(FakeBrowserSession(page))
		for _ in range(2):
			state, root, _t = await svc.get_serialized_dom_tree()
			digest_tree(root, h)
			text = state.llm_representation()
			h.update(text.encode())
			h.update(str(sorted(state.selector_map)).encode())
			print('selector_map', len(state.selector_map))
			# re-serialize with previous state (exercises serializer path again)
			st2, _ = DOMTreeSerializer(root, state).serialize_accessible_elements()
			h.update(st2.llm_representation().encode())
	return h.hexdigest()


if __name__ == '__main__':
	print(asyncio.run(run()))
