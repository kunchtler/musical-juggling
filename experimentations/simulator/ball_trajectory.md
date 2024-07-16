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
import matplotlib.pyplot as plt
import numpy as np
```

```python
g = 9.81

def x_pos(t, v0x, x0):
    return v0x * t + x0

def y_pos(t, v0y, y0):
    return - g / 2 * t**2 + v0y * t + y0

def f(x, v0x, x0, v0y, y0):
    X = (x - x0) / v0x
    return - g / 2 * X**2 + v0y * X + y0
```

```python
h = 3
tu = 0.5
td = 0.5
t1 = h * tu - td

x0 = -1
x1 = 1
y0 = 0

v0x = (x1 - x0) / t1
v0y = g / 2 * t1

t = np.linspace(0, t1)
x = np.linspace(x0, x1)

fig, ax = plt.subplots()

ax.plot(x_pos(t, v0x, x0), y_pos(t, v0y, y0), label="explicit")
ax.plot(x, f(x, v0x, x0, v0y, y0), label="implicit")


ax.grid()
ax.legend()
plt.show()
```

```python
fig, ax = plt.subplots()
tu_ref = 0.5
dx_ref = 1

curves_param = [(3, 0.5, 0.5), (3, 0.4, 0.4), (3, 0.3, 0.3), (3, 0.2, 0.2)]
for h, tu, td in curves_param:
    t1 = h * tu - td
    dx = dx_ref * (tu / tu_ref)**(1)
    x0 = -dx
    x1 = dx
    y0 = 0
    v0x = (x1 - x0) / t1
    v0y = g / 2 * t1
    t = np.linspace(0, t1)
    ax.plot(x_pos(t, v0x, x0), y_pos(t, v0y, y0), label=f"{h=}, {tu=}, {td=}")

ax.grid()
ax.legend()
plt.show()
```

```python

```
