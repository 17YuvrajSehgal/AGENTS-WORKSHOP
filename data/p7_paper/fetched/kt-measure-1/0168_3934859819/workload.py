import hashlib
import logging
import warnings

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

import torch

from olmoearth_pretrain.data.constants import Modality
from olmoearth_pretrain.datatypes import MaskValue
from olmoearth_pretrain.nn.flexi_patch_embed import FlexiPatchEmbed
from olmoearth_pretrain.nn.flexi_vit import Encoder, PoolingType, TokensAndMasks
from olmoearth_pretrain.train.loss import ModalityPatchDiscriminationLossNew

torch.manual_seed(0)
torch.set_num_threads(1)
h = hashlib.sha256()


def upd(t):
    h.update(f"{float(t.double().sum()):.4e}".encode())


# 1) Patch embedding (Conv2d -> Linear change)
spec = Modality.SENTINEL2_L2A
emb = FlexiPatchEmbed(spec, patch_size_at_16=4, in_chans=6, embedding_size=64)
with torch.no_grad():
    for i in range(20):
        x_t = torch.randn(8, 32, 32, 4, 6)
        out = emb(x_t)
        upd(out)
        x_s = torch.randn(8, 32, 32, 6)
        out = emb(x_s)
        upd(out)
        out = emb(x_s, patch_size=8)
        upd(out)

# 2) Encoder.add_removed_tokens
for i in range(200):
    b, n, d = 16, 256, 64
    tokens = torch.randn(b, n, d)
    mask = torch.rand(b, n) > 0.4
    sorted_mask, indices = torch.sort(mask.int(), dim=1, descending=True, stable=True)
    x = tokens.gather(1, indices[:, :, None].expand_as(tokens))
    k = int(sorted_mask.sum(-1).max())
    x = x[:, :k] * sorted_mask[:, :k, None]
    out, full_mask = Encoder.add_removed_tokens(x, indices, sorted_mask[:, :k].bool())
    upd(out)
    upd(full_mask)

# 3) Mean pooling
for i in range(100):
    bb, hh, ww, tt, bs, d = 8, 8, 8, 4, 2, 64
    toks = torch.randn(bb, hh, ww, tt, bs, d)
    m = torch.randint(0, 3, (bb, hh, ww, tt, bs))
    m[:, 0, 0, 0, 0] = MaskValue.ONLINE_ENCODER.value
    tam = TokensAndMasks(sentinel2_l2a=toks, sentinel2_l2a_mask=m)
    upd(tam.pool_unmasked_tokens(PoolingType.MEAN))
    upd(tam.pool_unmasked_tokens(PoolingType.MAX))

# 4) ModalityPatchDiscriminationLossNew
for pred2unit in (False, True):
    loss_fn = ModalityPatchDiscriminationLossNew(pred2unit=pred2unit)
    for i in range(40):
        b, t_h, t_w, t, d = 16, 8, 8, 3, 64
        s2_mask = torch.randint(0, 3, (b, t_h, t_w, t))
        s2_mask[0] = MaskValue.ONLINE_ENCODER.value
        ll_mask = torch.randint(0, 3, (b, 1))
        preds = TokensAndMasks(
            sentinel2_l2a=torch.randn((b, t_h, t_w, t, d)),
            sentinel2_l2a_mask=s2_mask,
            latlon=torch.randn((b, 1, d)),
            latlon_mask=ll_mask,
        )
        targets = TokensAndMasks(
            sentinel2_l2a=torch.randn((b, t_h, t_w, t, d)),
            sentinel2_l2a_mask=s2_mask,
            latlon=torch.randn((b, 1, d)),
            latlon_mask=ll_mask,
        )
        l = loss_fn.compute(preds, targets)
        upd(l)

print(h.hexdigest())
