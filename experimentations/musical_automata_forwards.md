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
import musicaljuggling.automata.musical_siteswap_forwards as ms
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

test = ms.MusicalAutomaton(beau_danube, 5, autobuild=False)
aut = test.automaton
```

```python
test.build_initial_states()
'''for state in test.initial_states:
    print(state)'''
```

```python
test.build_transitions()
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
#test.draw(notebook=False)
```

```python
for node in test.final_states:
    print(node)
```

```python
test.elagate()
```

```python
print("Nodes :")
'''for node in aut.nodes:
    print(node)
print("\nEdges :")
for edge in aut.edges:
    print(edge[0])
    print(edge[1])
    print("---")'''
```

```python
test.draw(path="acdll3.svg", notebook=False)
```
