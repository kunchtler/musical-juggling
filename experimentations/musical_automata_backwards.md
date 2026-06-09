---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.4
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
import musicaljuggling.automata.musical_siteswap_backwards as ms
import networkx as nx
```

```python
au_clair_de_la_lune = ["C", "C", "C", "D", "E", "", "D", "", "C", "E", "D", "D", "C"]
beau_danube = [
    "C", "E", "G",
    "G", "", "",
    "", "", "",
    "", "", "C",
    "C", "E", "G",
    "G", "", "",
    "", "", "",
    "", "", "D",
    "D", "F", "A'",
    "A'", "", "",
    "", "", "",
    "", "", "D",
    "D", "F", "A'",
    "A'", "", "",
    "", "", "",
    "", "", "C",
    "C", "E", "G",
    "C'", "", "",
    "", "", "",
    "", "", "C",
    "C", "E", "G",
    "C'", "", "",
    "", "", "",
    "", "", "D",
    "D", "F", "A'",
    "A'", "", "",
]
music = ["C", "D", "D", "D", "C"]

aut = ms.MusicalAutomaton(au_clair_de_la_lune, 6, autobuild=False)
```

```python
aut.build_final_states()
'''for state in test.final_states:
    print(state)'''
```

```python
aut.build_back_transitions()
'''print("Nodes :")
for node in aut.nodes:
    print(node)
print("\nEdges :")
for edge in aut.edges:
    print(edge[0])
    print(edge[1])
    print("---")'''
```

```python
aut.draw(path="test.svg", notebook=False)
```

```python
for node in aut.initial_states:
    print(node)
```

```python
aut.elagate(in_place=True)
'''print("Nodes :")
for node in aut.nodes:
    print(node)
print("\nEdges :")
for edge in aut.edges:
    print(edge[0])
    print(edge[1])
    print("---")'''
```

```python
aut.draw(path="test.svg", notebook=False)
```

```python

```

```python
%load_ext autoreload
%autoreload 2
```

```python
import musicaljuggling.automata.musical_siteswap_backwards as ms
import networkx as nx
import random as rd
import ipysigma as ips
```

```python
note_rates = {"A" : 1, "B" : 2, "C" : 1, "D": 3, "": 2}
song_length = 100
random_song = [rd.choices(list(note_rates.keys()), list(note_rates.values()))[0] for _ in range(song_length)]
au_clair_de_la_lune = ["C", "C", "C", "D", "E", "", "D", "", "C", "E", "D", "D", "C"]
aut = ms.MusicalAutomaton(au_clair_de_la_lune, 5, autobuild=True)
```

```python
print(f"{random_song = }")
print(f"{aut = }")
aut_det = aut.determinize()
print(f"{aut_det = }")
aut_det_min = aut_det.minimize()
print(f"{aut_det_min = }")
print(f"{nx.is_isomorphic(aut_det, aut_det_min) = }")
```

```python
ms.Automaton.to_automaton(aut).draw_interactive("au_clair_de_la_lune2.html")
aut_det.draw_interactive("au_clair_de_la_lune_det2.html")
```

```python
aut2 = ms.Automaton.to_automaton(aut).remove_unknown_attrs()
g = nx.relabel_nodes(aut2, {state : str(state) for state in aut2.nodes})
ips.Sigma(g)
```

```python
aut_det2 = aut_det.remove_unknown_attrs()
state_to_idx = {state : i for i, state in enumerate(aut_det2.nodes)}
g_det = nx.relabel_nodes(aut_det2, state_to_idx)
node_color = {state_to_idx[state] : next(iter(state)).time for state in aut_det2.nodes}
node_label = {state_to_idx[state] : str(state) for state in aut_det2.nodes}
ips.Sigma(g_det, start_layout=True, default_edge_type="curve", node_color=node_color, node_label=node_label)
```

```python
ips.Sigma(g, default_edge_type="curve", node_color=lambda node : next(iter(node)).time)
```

```python
a = frozenset([1, 2, 3])
rd.sample(a, k=1)
```

```python
next(iter(a))
```

```python

```
