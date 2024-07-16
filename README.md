# Musical Juggling

This python repository aims at creating a package for musical juggling, namely how to juggle a given melody with musical balls.

A [nice performance](https://www.youtube.com/watch?v=FA5YuMTd6h0) by *Vincent Delavenère* examplifies what we mean by musical juggling.

It is part of an ongoing thesis on the subject (more information can be found on [these.fr](https://www.theses.fr/s3667420) (english and french) or [here](https://codimd.math.cnrs.fr/Thduti3KRPesQfSnio5kyw) (French version only)).

## Installation

### From pip / conda

Not available yet.

### In development mode

Installation works only on Linux.

#### Step 1: Creating the conda environement.

The use of a python package manager is strongly advised. The next steps assume you have installed mamba, but conda also works (by replacing every `mamba` keyword with `conda`). This is not a mamba nor a conda tutorial.

First, fork this repository, and create a new environment from `environment.yml` :

```Sh
mamba env create -n name_of_the_environment -f environment.yml
```

Then activate the environment :

```Sh
mamba activate name_of_the_environment
```

#### Step 2: Installing the library in editable mode.

Pip allows to install a Python package in editable mode, which means that instead of copying the file to some place in the python path, it will instead redirect with a symlink to this very repository (meaning that any changes made here will have an immediate impact without having to reimport the library. It is quite handy :-))

```Sh
pip install -e .
```

#### Step 3 (optional - needed for automata module): Installing awali.

We make use of a library called awali (and its python binding named awalipy) to manipulate automatas, which is developed [here](http://vaucanson-project.org/Awali/2.3/index.html). Its installation procedure is not as straightforward as getting the package from pip or conda, as it needs to be compiled. Full procedure is detailed on the [webpage of awali](http://vaucanson-project.org/Awali/2.3/download.html), and is resumed for our needs (namely to install it properly in the mamba environment) here :

First be sure you have activated the mamba environment. Then type the commands :

```Sh
VERSION=awali-all-v2.3.0-230512

wget "http://files.vaucanson-project.org/tarballs/$VERSION.tgz"
tar xzvf $VERSION.tgz
rm $VERSION.tgz
cd $VERSION
# Replaces lines 503 and 516 of awalipy/bridge-to-dyn/algos to add const to the equiv parameter.
# Else, cython in version >= 3 complains.
sed -i 's/\& equiv/const\& equiv/g' awalipy/bridge-to-dyn/algos.hh
mkdir _build
cd _build
cmake -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX -DFORCE_INSTALL_IN_PREFIX=TRUE -DCORA=FALSE -DDOCUMENTATION=FALSE ..
make
make recommended
make install
```

The make commands can be sped up using the argument `-jX` where X is the number of cores to use in parallel. 

When finished, you may delete the downloaded folder at the end :
```Sh
cd ../..
rm -rf $VERSION
```

#### Step 4 (optional - needed for simulator): Installing music21.

We will also need to compile some C++ files manually for now, or each time they are changed.
They are used to find musical juggling patterns in the simulator using Dancing Links

```Sh
cd src/musicaljuggling/DLX
make lib
```

#### Step 5 (optional - needed for ???): Installing music21.

[TODO](https://web.mit.edu/music21/doc/installing/index.html)

#### Step final: Enjoy.

*Voila*, you can now use this package with `import musicaljuggling`.

## Usage

TODO

Examples on how to use the code can be found in the "experimentations" folder.