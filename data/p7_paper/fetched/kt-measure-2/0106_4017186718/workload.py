import sys, os, json, pathlib, hashlib, logging, random, tempfile, shutil

SCRIPTS = pathlib.Path(sys.prefix).resolve().parent / 'src' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import kanban_update as kb

logging.disable(logging.CRITICAL)

pathlib.Path('/tmp/kt_12').mkdir(parents=True, exist_ok=True)
WORK = pathlib.Path(tempfile.mkdtemp(dir='/tmp/kt_12'))
noop = WORK / 'noop_refresh.py'
noop.write_text('')
kb.REFRESH_SCRIPT = noop  # avoid writing into the repo's data dir
tasks_file = WORK / 'tasks_source.json'
kb.TASKS_FILE = tasks_file

rng = random.Random(12)
tasks = []
for i in range(150):
    tasks.append({
        'id': f'JJC-{i:05d}', 'title': f'任务标题 number {i} ' + 'x' * rng.randint(5, 40),
        'official': '中书令', 'org': '中书省', 'state': 'Inbox', 'now': '-',
        'eta': '-', 'block': '无', 'output': '', 'ac': '',
        'flow_log': [{'at': '2026-01-01T00:00:00Z', 'from': '皇上', 'to': '中书省',
                      'remark': 'r' * rng.randint(10, 60)} for _ in range(rng.randint(1, 6))],
        'updatedAt': '2026-01-01T00:00:00Z',
    })
tasks_file.write_text(json.dumps(tasks, ensure_ascii=False))

states = ['Zhongshu', 'Menxia', 'Assigned', 'Doing', 'Review']
for r in range(12):
    tid = f'JJC-{r:05d}'
    kb.cmd_create(f'NEW-{r:04d}', f'新建任务用于性能测试第{r}号', 'Zhongshu', '中书省', '中书令', f'备注内容 {r}')
    for s in states:
        kb.cmd_state(tid, s, f'进行中 {s}')
    kb.cmd_flow(tid, '中书省', '门下省', f'规划方案提交审核 {r}')
    kb.cmd_progress(tid, f'正在分析需求 {r}', '调研技术选型✅|撰写设计文档🔄|实现原型', 100 + r, 0.01, 5)
    kb.cmd_todo(tid, '1', '实现API接口', 'in-progress')
    kb.cmd_todo(tid, '1', '', 'completed')
    if r % 2:
        kb.cmd_block(tid, f'等待依赖 {r}')
    else:
        kb.cmd_done(tid, f'/tmp/out{r}', f'完成摘要 {r}')

data = json.loads(tasks_file.read_text())
def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k not in ('at', 'updatedAt', 'startedAt', 'lastProgressAt')}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o
s = json.dumps(strip(data), ensure_ascii=False, sort_keys=True)
print(len(data))
print(hashlib.sha256(s.encode()).hexdigest())
shutil.rmtree(WORK, ignore_errors=True)
