import asyncio, hashlib, json, os, random, shutil, logging
import numpy as np
from lightrag import LightRAG
from lightrag.base import DocStatus
from lightrag.utils import EmbeddingFunc, logger
from lightrag.kg.shared_storage import initialize_share_data, initialize_pipeline_status

logger.setLevel(logging.CRITICAL)
WD = "/tmp/kt_2853/wd"
N = 20000

async def emb(texts, **kw):
    return np.zeros((len(texts), 8), dtype=np.float32)

async def llm(prompt, **kw):
    return ""

def make_docs():
    rnd = random.Random(1234)
    sts = [DocStatus.PENDING.value, DocStatus.PROCESSING.value, DocStatus.FAILED.value,
           DocStatus.PROCESSED.value, DocStatus.PREPROCESSED.value]
    docs = {}
    for i in range(N):
        d = {
            "content_summary": f"summary {i}", "content_length": rnd.randint(10, 5000),
            "status": rnd.choice(sts),
            "created_at": f"2025-01-01T00:00:{i%60:02d}+00:00",
            "updated_at": f"2025-01-02T00:00:{i%60:02d}+00:00",
            "track_id": f"t{i%37}", "chunks_count": i % 11,
            "chunks_list": [f"chunk-{i}-{j}" for j in range(i % 4)],
        }
        if i % 3: d["file_path"] = f"f{i}.txt"
        if i % 5 == 0: d["metadata"] = {"k": i}
        if i % 7 == 0: d["error_msg"] = "err"
        if i % 13 == 0: d["content"] = "old"
        docs[f"doc-{i}"] = d
    return docs

def digest_docs(res):
    return sorted((k, v.status if isinstance(v.status, str) else v.status.value, v.file_path,
                   v.content_length, json.dumps(v.metadata, sort_keys=True), v.error_msg)
                  for k, v in res.items() if not k.startswith("real-"))

async def main():
    shutil.rmtree(WD, ignore_errors=True)
    os.makedirs(WD)
    initialize_share_data()
    rag = LightRAG(working_dir=WD, llm_model_func=llm,
                   embedding_func=EmbeddingFunc(embedding_dim=8, max_token_size=512, func=emb))
    await rag.initialize_storages()
    await initialize_pipeline_status()
    ds = rag.doc_status
    docs = make_docs()
    out = []
    # all non-processed docs: pipeline path sees nothing / scans docs
    processed_only = {k: dict(v, status=DocStatus.PROCESSED.value) for k, v in docs.items()}
    await ds.upsert(processed_only)
    for _ in range(8):
        await rag.apipeline_process_enqueue_documents()
    out.append(len(await ds.get_docs_by_status(DocStatus.PROCESSED)))
    await asyncio.gather(*[rag.ainsert(f"Document number {i}. Alice met Bob in Paris.",
                                       ids=f"real-{i}") for i in range(3)])
    out.append(sorted((await ds.get_status_counts()).items()))
    await ds.upsert(docs)
    for _ in range(4):
        for st in [DocStatus.PENDING, DocStatus.PROCESSING, DocStatus.FAILED,
                   DocStatus.PROCESSED, DocStatus.PREPROCESSED]:
            r = await ds.get_docs_by_status(st)
            out.append((st.value, digest_docs(r)))
    await rag.finalize_storages()
    h = hashlib.sha256(json.dumps(out).encode()).hexdigest()
    print(len(out))
    print(h)

asyncio.run(main())
