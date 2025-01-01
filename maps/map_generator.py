import json

li = []
li.append({"width": 31 * 16, "height": 21 * 16})
a = {}
a["name"] = "city1.png"
a["type"] = "background"
a["cord"] = [(i, j) for i in range(1, 30) for j in range(1, 20)]
li.append(a)
b = {}
b["name"] = "city6.png"
b["type"] = "wall"
b["cord"] = []
b["cord"].extend([(0, i) for i in range(0, 21)])
b["cord"].extend([(30, i) for i in range(0, 21)])
b["cord"].extend([(i, 0) for i in range(1, 30)])
b["cord"].extend([(i, 20) for i in range(1, 30)])
li.append(b)
with open("1.json", "w") as f:
    f.write(json.dumps(li))
