import json
names = ["UP", "LEFT", "DOWN", "RIGHT"]
dist = {0: "adjacent", 1: "2 away", 2: "3+ away"}
data = json.load(open("models/10sess.txt"))
for key, q in data["q"].items():
    print("STATE")
    for n, (b, g, r) in zip(names, json.loads(key)):
        print(f"  {n:5} danger {dist[b]:8} green={g} red={r}")
    print("  Q:", {n: round(v, 4) for n, v in zip(names, q)})
