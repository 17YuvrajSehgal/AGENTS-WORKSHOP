import asyncio
import hashlib
import json
import logging
import random
from datetime import datetime, timedelta, timezone

logging.disable(logging.CRITICAL)

from graphiti_core.cross_encoder.client import CrossEncoderClient
from graphiti_core.driver.kuzu_driver import KuzuDriver
from graphiti_core.edges import EntityEdge
from graphiti_core.embedder.client import EmbedderClient
from graphiti_core.graph_queries import get_fulltext_indices
from graphiti_core.driver.driver import GraphProvider
from graphiti_core.graphiti_types import GraphitiClients
from graphiti_core.llm_client import LLMClient
from graphiti_core.nodes import EntityNode, EpisodeType, EpisodicNode
from graphiti_core.tracer import NoOpTracer
from graphiti_core.utils.maintenance.edge_operations import resolve_extracted_edges

DIM = 32
GROUP = 'g1'
BASE_T = datetime(2024, 1, 1, tzinfo=timezone.utc)


def vec(text):
    h = hashlib.sha256(text.encode()).digest()
    v = [(b - 128) / 128.0 for b in h[:DIM]]
    n = sum(x * x for x in v) ** 0.5 or 1.0
    return [x / n for x in v]


class StubEmbedder(EmbedderClient):
    async def create(self, input_data):
        return vec(str(input_data))

    async def create_batch(self, input_data_list):
        return [vec(str(x)) for x in input_data_list]


class StubCrossEncoder(CrossEncoderClient):
    async def rank(self, query, passages):
        return sorted(((p, 1.0 / (1 + i)) for i, p in enumerate(passages)), key=lambda x: -x[1])


class StubLLM(LLMClient):
    """Deterministic stand-in for the remote LLM service."""

    def __init__(self):
        super().__init__(None, cache=False)

    async def _generate_response(self, messages, response_model=None, max_tokens=0, model_size=None):
        text = ''.join(m.content for m in messages)
        h = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        return {'duplicate_facts': [0] if h % 3 == 0 else [], 'contradicted_facts': [1] if h % 5 == 0 else []}


def fact_for(a, b, k):
    return f'entity {a} relates to entity {b} by fact number {k}'


async def build_graph(driver, n_nodes, n_edges, rng):
    nodes = []
    for i in range(n_nodes):
        n = EntityNode(
            uuid=f'node-{i:04d}', name=f'Entity {i}', group_id=GROUP, labels=['Entity'],
            created_at=BASE_T, summary=f'summary {i}', name_embedding=vec(f'Entity {i}'),
        )
        await n.save(driver)
        nodes.append(n)
    pairs = []
    for k in range(n_edges):
        a, b = rng.sample(range(n_nodes), 2)
        pairs.append((a, b))
        e = EntityEdge(
            uuid=f'edge-{k:05d}', source_node_uuid=nodes[a].uuid, target_node_uuid=nodes[b].uuid,
            name='RELATES', group_id=GROUP, fact=fact_for(a, b, k), episodes=['ep-0'],
            created_at=BASE_T, valid_at=BASE_T + timedelta(days=k),
            fact_embedding=vec(fact_for(a, b, k)),
        )
        await e.save(driver)
    return nodes, pairs


async def main():
    rng = random.Random(42)
    driver = KuzuDriver(':memory:')
    clients = GraphitiClients(
        driver=driver, llm_client=StubLLM(), embedder=StubEmbedder(),
        cross_encoder=StubCrossEncoder(), tracer=NoOpTracer(),
    )
    nodes, pairs = await build_graph(driver, 40, 300, rng)
    for q in get_fulltext_indices(GraphProvider.KUZU):
        await driver.execute_query(q)
    episode = EpisodicNode(
        uuid='ep-1', name='ep', group_id=GROUP, source=EpisodeType.text, source_description='d',
        content='content', valid_at=BASE_T + timedelta(days=500), created_at=BASE_T,
    )
    out = []
    for rnd in range(4):
        extracted = []
        for j in range(30):
            a, b = pairs[rng.randrange(len(pairs))]
            if rng.random() < 0.5:
                a, b = b, a  # reverse direction: only found by the bidirectional lookup
            extracted.append(EntityEdge(
                uuid=f'new-{rnd}-{j}', source_node_uuid=nodes[a].uuid, target_node_uuid=nodes[b].uuid,
                name='RELATES', group_id=GROUP, fact=f'new fact {rnd} {j} about {a} and {b}',
                episodes=[], created_at=BASE_T, valid_at=BASE_T + timedelta(days=400 + j),
            ))
        resolved, invalidated, new = await resolve_extracted_edges(
            clients, extracted, episode, nodes, {}, {}
        )
        out.append([
            [e.uuid for e in resolved],
            sorted(e.uuid for e in invalidated),
            [e.uuid for e in new],
        ])
        print(rnd, len(resolved), len(invalidated), len(new))
    print(hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest())


asyncio.run(main())
