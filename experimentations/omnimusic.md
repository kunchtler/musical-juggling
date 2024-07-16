---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.1
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

```python
%load_ext autoreload
%autoreload 2
```

```python
import musicaljuggling.automata.omnimusic as om
```

```python
aut = om.Omnimusic(3, ["A", "B"], autobuild=False)
```

```python
aut.build_states()
```

```python
for node in aut.nodes:
    print(node)
```

```python
aut.build_transitions()
```

```python
'''for node in aut.nodes:
    print(node'''
```

```python

```

```python

```

```python
%load_ext autoreload
%autoreload 2
```

```python
import musicaljuggling.automata.omnimusic as om
import ipysigma as ips
import networkx as nx
```

```python
aut = om.Omnimusic(6, ["A", "B"], autobuild=True)
prefix = "AB6"
```

```python
om.Automaton.to_automaton(aut).draw_interactive(prefix + "aut.html")
```

```python
aut_det = aut.determinize()
```

```python
aut_det.draw_interactive(prefix + "aut_det.html")
```

```python
aut_det_min = aut_det.minimize()
```

```python
aut_det_min.draw_interactive(prefix + "aut_det_min.html")
```

```python
aut_proj = aut.project()
```

```python
aut_proj.draw_interactive(prefix + "aut_proj.html")
```

```python
aut_proj_det = aut_proj.determinize()
```

```python
aut_proj_det.draw_interactive(prefix + "aut_proj_det.html")
```

```python
aut_proj_det_min = aut_proj_det.minimize()
```

```python
aut_proj_det_min.draw_interactive(prefix + "aut_proj_det_min.html")
```

```python
nx.is_isomorphic(aut_proj_det, aut_proj_det_min)
```

```python
import networkx as nx
```

```python
g = aut_proj_det_min.remove_unknown_attrs()
ips.Sigma(nx.convert_node_labels_to_integers(g))
```

```python
aut = om.Omnimusic(3, ["A", "B"], autobuild=True)
```

```python

```

```python
import musicaljuggling.automata.omnimusic as om
import pyvis
import networkx as nx
```

```python
aut = om.Omnimusic(2, ["A", "B"], autobuild=True)
om.Automaton.to_automaton(aut).draw_interactive("AB2.html")
```

```python
aut = aut.project().determinize().minimize()
aut.draw_interactive("AB2_proj_det_min.html")
```

```python

aut.add_node("Poubelle")
for node1 in aut.nodes():
    letters_met = set()
    for _, node2, letter in aut.out_edges(node1, data="transition"):
        letters_met.add(letter)
    for letter in aut.alphabet - letters_met:
        aut.add_edge(node1, "Poubelle", key=letter, transition=letter, label=letter)
aut.final_states = set(aut.nodes()) - aut.final_states
```

```python
for node in aut.nodes():
    print(node, end = " ")
    for value in aut[node].values():
        for letter in value.keys():
            print(letter, end=" ")
    print("")b
```

```python

```

```python
for node in aut.nodes():
    if node in aut.initial_states and node in aut.final_states:
        aut.nodes[node]["color"] = "#b969ff" #purple
    elif node in aut.initial_states:
        aut.nodes[node]["color"] = "#f2e65c" #yellow
    elif node in aut.final_states:
        aut.nodes[node]["color"] = "#fa3939" #red
    else:
        aut.nodes[node]["color"] = "#ff873d" #orange
clean_aut = nx.relabel_nodes(om.Automaton.to_automaton(aut), {state : str(state) for state in aut.nodes()})
```

```python
nt = pyvis.network.Network(
    height="900px",
    width="100%",
    directed=True,
    notebook=True)
nt.from_nx(clean_aut)
for node in nt.nodes:
    if "label" in node:
        del node["label"]
    if "fused_nodes" in node:
        del node["fused_nodes"]
    print(node)

nt.show("AB2.html")
```

```python

```
