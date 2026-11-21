import os, sys, hashlib, shutil, io, contextlib
import torch
torch.manual_seed(0)
torch.set_num_threads(1)

ROOT = "/tmp/kt_268"
MODEL = os.path.join(ROOT, "tiny_llama")
MISTRAL = os.path.join(ROOT, "tiny_mistral")

def build_model(MODEL=MODEL, kind="llama"):
    from transformers import (LlamaConfig, LlamaForCausalLM, MistralConfig, MistralForCausalLM,
                              PreTrainedTokenizerFast)
    from tokenizers import Tokenizer, models, pre_tokenizers
    if os.path.exists(os.path.join(MODEL, "model.safetensors.index.json")):
        return
    shutil.rmtree(MODEL, ignore_errors=True)
    os.makedirs(MODEL, exist_ok=True)
    torch.manual_seed(0)
    C, M = (LlamaConfig, LlamaForCausalLM) if kind == "llama" else (MistralConfig, MistralForCausalLM)
    cfg = C(vocab_size=512, hidden_size=128, intermediate_size=256,
            num_hidden_layers=8, num_attention_heads=4, num_key_value_heads=4,
            max_position_embeddings=256, tie_word_embeddings=False)
    m = M(cfg)
    m.save_pretrained(MODEL, safe_serialization=True, max_shard_size="200KB")
    vocab = {f"t{i}": i for i in range(511)}
    vocab["[UNK]"] = 511
    tk = Tokenizer(models.WordLevel(vocab=vocab, unk_token="[UNK]"))
    tk.pre_tokenizer = pre_tokenizers.Whitespace()
    PreTrainedTokenizerFast(tokenizer_object=tk, unk_token="[UNK]").save_pretrained(MODEL)

def main():
    build_model()
    from airllm.airllm import AirLLMLlama2
    h = hashlib.sha256()
    g = torch.Generator().manual_seed(1)
    sink = io.StringIO()
    for rep, (cls, path, pf, prof) in enumerate([(AirLLMLlama2, MODEL, True, False),
                                                 (AirLLMLlama2, MODEL, False, True),
                                                 (AirLLMLlama2, MODEL, True, True)]):
        ids = torch.randint(0, 512, (2, 48), generator=g)
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            # one forward per instance (layers are moved to meta after each forward)
            model = cls(path, device="cpu", dtype=torch.float32, max_seq_len=128,
                                 prefetching=pf, profiling_mode=prof)
            out = model(input_ids=ids, use_cache=False, return_dict=True)
        logits = out.logits if hasattr(out, "logits") else out[0]
        h.update(torch.round(logits.float() * 1e3).to(torch.int64).numpy().tobytes())
        print(rep, tuple(logits.shape), int(logits.argmax(-1).sum()))
    print(h.hexdigest())

if __name__ == "__main__":
    main()
