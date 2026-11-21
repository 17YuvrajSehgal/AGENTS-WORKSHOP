# PyThaiNLP #1319 "fix(newmm): resolve exponential BFS path explosion".
# Pilot workload (hand-written, experimenter has read the PR): tokenise
# repeated ambiguous text with the changed engine; last line = output digest.
import hashlib
import os

from pythainlp.tokenize import word_tokenize

N = int(os.environ.get("KT_N", "4000"))
# the PR's own regression example, scaled by N, with non-Thai text and an
# out-of-dictionary Thai string mixed in so the non-dictionary branches run
block = "ด้านหน้า" * 50 + " abc123 " + "ฆฆฆฬฬ"
text = block * (N // 50)
tokens = word_tokenize(text, engine="newmm")
print(len(tokens))
print(hashlib.sha256("|".join(tokens).encode()).hexdigest())
