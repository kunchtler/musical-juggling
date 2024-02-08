# Musical Juggling

This python repository aims at creating a package for musical juggling, namely how to juggle a given melody with musical balls.

A [nice performance](https://www.youtube.com/watch?v=FA5YuMTd6h0) by *Vincent Delavenère* examplifies what we mean by musical juggling.

It is part of an ongoing thesis on the subject (more information can be found on [these.fr](https://www.theses.fr/s3667420) (english and french) or [here](https://codimd.math.cnrs.fr/Thduti3KRPesQfSnio5kyw) (French version only)).

## Installation

### From pip / conda

Not available yet.

### In development mode

Installation works only on Linux.

The use of a python package manager is strongly advised. The next steps assume you have installed mamba, but conda also works (by replacing every `mamba` keyword with `conda`).

First, fork this repository, and create a new environment from `environment.yml` :

```
mamba env create -n name_of_the_environment -f environment.yml
```

Then activate the environment :

```
mamba activate name_of_the_environment
```

Pip allows to install a Python package in editable mode, which means that instead of copying the file to some place in the python path, it will instead redirect with a symlink to this very repository (meaning that any changes made here will have an immediate impact without having to reimport the library. It is quite handy :-))

```
pip install -e .
```

We will also need to compile some C++ files manually for now, or each time they are changed.

```
cd src/musicaljuggling/DLX; make lib
```

*Voila*, you can now use this package with `import musicaljuggling`.

## Usage

TODO