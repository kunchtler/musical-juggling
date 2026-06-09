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
from musicaljuggling.automata.musical_siteswap_backwards import MusicalAutomaton
import networkx as nx
```

```python
happy_birthday = [
    "C4", "C4",
    "D4", "", "C4", "", "F4", "",
    "E4", "", "", "", "C4", "C4",
    "D4", "", "C4", "", "G4", "",
    "F4", "", "", "", "C4", "C4",
    "C5", "", "A5", "", "F4", "",
    "E4", "", "D4", "", "B5", "B5",
    "A5", "", "F4", "", "G4", "",
    "F4"
]
```

```python
aut = MusicalAutomaton(happy_birthday, 7)
```

```python
print(f"{happy_birthday = }")
print(f"{aut = }")
aut_det = aut.determinize()
print(f"{aut_det = }")
aut_det_min = aut_det.minimize()
print(f"{aut_det_min = }")
print(f"{nx.is_isomorphic(aut_det, aut_det_min) = }")
```

```python
aut_det.draw_interactive("happy_birthday_det2.html")
```

```python

```
