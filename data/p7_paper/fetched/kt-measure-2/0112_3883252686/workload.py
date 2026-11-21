import os, hashlib, logging
logging.disable(logging.CRITICAL)
from api.backends import factory

configs = [
    {"TTS_BACKEND": "official"},
    {"TTS_BACKEND": "official", "TTS_MODEL_NAME": "Qwen/Qwen3-TTS-12Hz-0.6B-Base"},
    {"TTS_BACKEND": "OFFICIAL", "TTS_MODEL_NAME": "Qwen/Qwen3-TTS-12Hz-1.7B-Base"},
    {"TTS_BACKEND": "vllm"},
    {"TTS_BACKEND": "vllm_omni", "TTS_MODEL_NAME": "Qwen/Qwen3-TTS-12Hz-0.6B-Base"},
    {"TTS_BACKEND": "vllm-omni"},
    {"TTS_BACKEND": "bogus"},
    {"TTS_BACKEND": "pytorch", "TTS_DEVICE": "cpu", "CPU_THREADS": "2", "CPU_INTEROP": "1"},
    {"TTS_BACKEND": "pytorch", "TTS_MODEL_ID": "Qwen/Qwen3-TTS-12Hz-0.6B-Base", "TTS_DTYPE": "float32", "TTS_ATTN": "eager", "CPU_THREADS": "2"},
    {"TTS_BACKEND": "openvino", "OV_MODEL_DIR": "/tmp/kt_12/ov_models", "OV_CACHE_DIR": "/tmp/kt_12/ov_cache"},
]
keys = ["TTS_BACKEND", "TTS_MODEL_NAME", "TTS_MODEL_ID", "TTS_DEVICE", "TTS_DTYPE", "TTS_ATTN", "CPU_THREADS", "CPU_INTEROP", "OV_MODEL_DIR", "OV_CACHE_DIR"]
h = hashlib.sha256()
N = 40000
for i in range(N):
    cfg = configs[i % len(configs)]
    for k in keys:
        os.environ.pop(k, None)
    os.environ.update(cfg)
    factory.reset_backend()
    try:
        b = factory.get_backend()
        out = "|".join(map(str, [type(b).__name__, b.get_model_id(), b.get_backend_name(),
                                 b.is_ready(), b.supports_voice_cloning(), b.get_model_type(),
                                 sorted(b.get_supported_voices()), b.get_supported_languages(),
                                 sorted(b.get_device_info().items())]))
        # cached path
        assert factory.get_backend() is b
    except ValueError as e:
        out = "ValueError:" + str(e).split(".")[0]
    if i < len(configs):
        print(out)
    h.update(out.encode())
factory.reset_backend()
print(h.hexdigest())
