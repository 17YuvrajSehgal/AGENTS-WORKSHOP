import hashlib
import random
from addok.config import config, Config

Config.TESTING = True
config.load()

from addok.helpers.index import preprocess, extract_tokens

rng = random.Random(892)
streets = ["rue", "avenue", "boulevard", "chemin", "allée", "impasse", "place", "quai", "route"]
names = ["des Lilas", "Victor Hugo", "de la République", "Jean Jaurès", "du Général de Gaulle",
         "Pasteur", "de l'Église", "des Écoles", "Saint-Michel", "du Moulin", "Gambetta"]
cities = ["Paris", "Lyon", "Marseille", "Saint-Étienne", "Aix-en-Provence", "Château-Thierry",
          "Bordeaux", "Lille", "Nantes", "Montpellier"]

def make():
    return "{} {} {} {} {:05d}".format(rng.randint(1, 300), rng.choice(streets), rng.choice(names),
                                     rng.choice(cities), rng.randint(1000, 99999))

unique = [make() for _ in range(15000)]
words = list({w for s in unique for w in s.split()})
words.sort()

h = hashlib.sha256()
for rnd in range(6):
    for s in unique:
        h.update("|".join(preprocess(s)).encode())
    for _ in range(100000):
        w = rng.choice(words)
        h.update("|".join(preprocess(w)).encode())
    tokens = {}
    for s in unique[:5000]:
        extract_tokens(tokens, s, 1.0)
    for k in sorted(tokens):
        h.update("{}:{:.6f}".format(k, tokens[k]).encode())
print(h.hexdigest())
