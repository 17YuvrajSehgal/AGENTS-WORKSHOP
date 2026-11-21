import copy
import hashlib
import json

import torch

from fast_llm_external_models.apriel2.cache import Apriel2Cache
from fast_llm_external_models.apriel2.configuration_apriel2 import Apriel2Config
from fast_llm_external_models.apriel2.conversion import compose_configs, plan_surgery

torch.manual_seed(0)
H = hashlib.sha256()


def upd(x):
    H.update(repr(x).encode())


ATT = {"type": "attention", "heads": 4, "head_groups": 2, "head_size": 16,
       "rotary": {"type": "mistral_1d", "theta": 10000.0}}
SWA = dict(ATT, window_size=8)
MAMBA = {"type": "mamba", "d_inner": 128, "d_state": 16, "dt_rank": 4, "d_xb": 16, "d_conv": 4}
GDN = {"type": "gdn", "value_heads": 4, "key_heads": 2, "key_head_dim": 16, "value_head_dim": 16,
       "convolution_layer": {"kernel_size": 4}}
MLP = {"mlp": {"type": "mlp", "intermediate_size": 64, "gated": True},
       "normalization": {"type": "rms_norm", "epsilon": 1e-5}}


def blk(mixer):
    return dict(MLP, mixer=mixer)


config = Apriel2Config(
    vocab_size=100,
    hidden_size=64,
    decoder={
        "type": "pattern",
        "num_blocks": 12,
        "pattern": ["attn", "swa", "mamba", "gdn", "sam", "ssg"],
        "blocks": {
            "attn": blk(ATT),
            "swa": blk(SWA),
            "mamba": blk(MAMBA),
            "gdn": blk(GDN),
            "sam": blk({"type": "stochastic", "main_mixer_name": "attention",
                        "mixers": {"attention": ATT, "mamba": MAMBA}}),
            "ssg": blk({"type": "stochastic", "main_mixer_name": "swa",
                        "mixers": {"swa": SWA, "gdn": GDN}}),
        },
    },
)


def cache_workload(iters):
    B = 4
    for it in range(iters):
        cache = Apriel2Cache(config)
        n = len(cache)
        for i in range(n):
            layer = cache.layers[i]
            if isinstance(layer, dict):
                cache.set_active_mixer(i, list(layer.keys())[it % 2])
        upd((cache.is_initialized, cache.max_batch_size, cache.max_cache_len, cache.has_previous_state))
        for step in range(6):
            T = 3 if step == 0 else 1
            for i in range(n):
                mt = cache.mixer_types[i]
                layer = cache.layers[i]
                active = cache.active_mixers[i]
                sub = layer[active] if isinstance(layer, dict) else layer
                if hasattr(sub, "key"):
                    k = torch.full((B, 2, T, 4), float(step + i))
                    kk, vv = cache.update(k, k + 1, i)
                    upd(tuple(kk.shape))
                else:
                    cache.conv_states[i] = torch.full((B, 8, 4), float(step))
                    cache.recurrent_states[i] = torch.full((B, 8, 4), float(i))
                upd((mt, cache.get_seq_length(i), cache.get_mask_sizes(torch.arange(T), i),
                     cache.get_max_cache_shape(i)))
            upd((cache.is_initialized, cache.max_batch_size, cache.has_previous_state, cache.max_cache_len))
            cache.reorder_cache(torch.tensor([3, 2, 1, 0]))
            cache.batch_repeat_interleave(2)
            cache.batch_select_indices(torch.tensor([0, 2, 4, 6]))
        k0, v0 = cache[0]
        upd((tuple(k0.shape), float(k0.sum()), float(v0.sum())))
        cache.crop(4)
        upd([cache.get_seq_length(i) for i in range(n)])
        upd([cache.get_mask_sizes(torch.arange(2), i) for i in range(n)])
        cache.reset()
        upd((cache.is_initialized, cache.max_batch_size, cache.has_previous_state))


SOURCE = {
    "model_type": "apriel2",
    "hidden_size": 64,
    "vocab_size": 100,
    "decoder": {"type": "fixed", "num_blocks": 3, "block": blk(dict(ATT, heads=4, head_groups=2, head_size=16))},
}

CHAIN = [
    {"decoder": {"block": {"mixer": {"type": "stochastic", "main_mixer_name": "attention",
                                     "mixers": {"attention": {"init": "transfer"}}},
                           "mlp": {"init": "transfer"}, "normalization": {"init": "transfer"}}}},
    {"decoder": {"block": {"mixer": {"mixers": {"sliding_window": {"type": "attention", "init": "transfer",
                                                                   "window_size": 512}}}}}},
    {"decoder": {"block": {"mixer": {"mixers": {"gdn": {"type": "gdn", "init": "transfer",
                                                        "convolution_layer": {"kernel_size": 4}}}}}}},
    {"decoder": {"block": {"mixer": {"mixers": {"mamba": {"type": "mamba", "init": "transfer",
                                                          "d_inner": 64, "d_xb": 32, "dt_rank": 4,
                                                          "d_state": 16, "d_conv": 4, "repeat_kv_before_conv": True, "conv_bias": True, "dt_proj_bias": True, "dt_min": 0.001, "dt_max": 0.1, "dt_init_floor": 1e-4}}}}}},
]


def strip(d):
    if isinstance(d, dict):
        return {k: strip(v) for k, v in d.items() if k != "init"}
    if isinstance(d, list):
        return [strip(x) for x in d]
    return d


def conversion_workload(iters):
    for _ in range(iters):
        state = copy.deepcopy(SOURCE)
        merged = {}
        for surgery in CHAIN:
            merged = compose_configs(merged, surgery)
            target = compose_configs(state, surgery)
            plan = plan_surgery(state, target)
            upd(sorted(str(k) for k in plan.mappings))
            state = strip(target)
            upd(json.dumps(state, sort_keys=True, default=str))
        upd(json.dumps(compose_configs(SOURCE, merged), sort_keys=True, default=str))


cache_workload(100)
conversion_workload(40)
print(H.hexdigest())
