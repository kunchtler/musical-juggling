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
aut = om.Omnimusic(5, ["A", "B", "C"], autobuild=False)
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
test.draw("test.svg")
```

```python

```

```python
%load_ext autoreload
%autoreload 2
```

```python
import musicaljuggling.automata.omnimusic as om
```

```python
aut = om.Omnimusic(5, ["A", "B"], autobuild=True)
prefix = "AB5"
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

```
