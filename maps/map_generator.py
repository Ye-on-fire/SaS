import json

li = []
li.append({"width": 41 * 16, "height": 31 * 16})
a = {}
a["name"] = "city2.png"
a["type"] = "background"
a["cord"] = [(i, j) for i in range(1, 40) for j in range(1, 30)]
li.append(a)
b = {}
b["name"] = "city5.png"
b["type"] = "wall"
b["cord"] = []
b["cord"].extend([(0, i) for i in range(0, 21)])
b["cord"].extend([(30, i) for i in range(0, 21)])
b["cord"].extend([(i, 0) for i in range(1, 30)])
b["cord"].extend([(i, 20) for i in range(1, 30)])
li.append(b)
with open("2.json", "w") as f:
    f.write(json.dumps(li))
