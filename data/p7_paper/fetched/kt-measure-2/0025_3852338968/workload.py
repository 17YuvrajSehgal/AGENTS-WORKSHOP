import hashlib, random, warnings
warnings.filterwarnings("ignore")
from espial.analysis import process_markdown

random.seed(14)
vocab = ["the", "a", "you", "your", "it's", "with", "network", "graph", "python",
         "knowledge", "espial", "notes", "markdown", "idea", "concept", "and", "of",
         "[link](http://example.com/x)", "[ref](https://foo.org/a/b)", "learning",
         "system", "data", "is", "to", "were", "tag", "entity", "search"]
docs = [" ".join(random.choice(vocab) for _ in range(2000)) for _ in range(200)]
h = hashlib.sha256()
for _ in range(10):
    for d in docs:
        h.update(process_markdown(d).encode())
print(h.hexdigest())
