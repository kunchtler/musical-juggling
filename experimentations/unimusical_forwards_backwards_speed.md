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
import musicaljuggling.automata.musical_siteswap2 as msbackwards
import musicaljuggling.automata.musical_siteswap as msforwards
from time import time
```

```python
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
    "A'"
]
```

```python
%%time
forward = msforwards.MusicalAutomaton(beau_danube, 5, autobuild=True)
```

```python
%%time
backward = msbackwards.MusicalAutomaton(beau_danube, 5, autobuild=True)
```

```python
forward.draw(path="beau_danube_forwards.svg")
backward.draw(path="beau_danube_backwards.svg")
```

```python

```
