import os, shutil, asyncio, hashlib, logging, random
os.environ['ANONYMIZED_TELEMETRY'] = 'false'
os.environ['BROWSER_USE_CLOUD_SYNC'] = 'false'
os.environ['BROWSER_USE_LOGGING_LEVEL'] = 'error'
os.environ['BROWSER_USE_CONFIG_DIR'] = '/tmp/kt_2090/config'
os.environ['XDG_CONFIG_HOME'] = '/tmp/kt_2090/xdg_config'
os.environ['XDG_CACHE_HOME'] = '/tmp/kt_2090/xdg_cache'
from browser_use import Agent
from browser_use.agent.views import AgentState
logging.disable(logging.CRITICAL)

ROOT = '/tmp/kt_2090/run'


class FakeLLM:  # stand-in for the external LLM API (never invoked)
	model = 'fake'
	_verified_api_keys = True
	provider = 'openai'
	name = 'fake'

	@property
	def model_name(self):
		return 'fake'

	async def ainvoke(self, messages, output_format=None):
		raise RuntimeError('no llm')


rng = random.Random(1234)
WORDS = ['alpha', 'beta', 'gamma', 'delta', 'price', 'item', 'result', 'data', 'page', 'link']


def text(n):
	return '\n'.join(' '.join(rng.choice(WORDS) for _ in range(8)) for _ in range(n))


async def session(i, out):
	agent = Agent(task=f'task {i}', llm=FakeLLM(), enable_memory=False, task_id=f'00000000-fixed-{i:04d}',
				  file_system_path=os.path.join(ROOT, f'agent_{i}'))
	fs = agent.file_system
	reg = agent.controller.registry
	names = [f'notes_{k}.md' for k in range(4)] + ['results.md', 'bad name.txt']
	for name in names:
		r = await reg.execute_action('write_file', {'file_name': name, 'content': text(5)}, file_system=fs)
		out.append(r.extracted_content)
	for _ in range(3):
		for name in names[:4]:
			r = await reg.execute_action('append_file', {'file_name': name, 'content': '\n' + text(3)}, file_system=fs)
			out.append(r.extracted_content)
	for name in names + ['missing.md']:
		r = await reg.execute_action('read_file', {'file_name': name}, file_system=fs, available_file_paths=[])
		out.append(r.extracted_content)
	r = await reg.execute_action('done', {'text': 'Finished ' + text(4), 'success': True,
										  'files_to_display': names[:3] + ['todo.md', 'missing.md']}, file_system=fs)
	out.append(r.extracted_content)
	out.append(r.long_term_memory)
	out.append(repr(sorted(os.path.basename(p) for p in (r.attachments or []))))
	out.append(fs.describe() if hasattr(fs, 'describe') else '')
	st = AgentState()
	out.append(repr(sorted(st.model_dump().keys() - {'agent_id', 'file_system'})))


async def main():
	out = []
	for i in range(40):
		await session(i, out)
	return out


shutil.rmtree(ROOT, ignore_errors=True)
os.makedirs(ROOT, exist_ok=True)
out = asyncio.run(main())
shutil.rmtree(ROOT, ignore_errors=True)
print(len(out))
print(hashlib.sha256('\x00'.join(map(str, out)).encode()).hexdigest())
