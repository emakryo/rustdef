# rustdef

[![Test](https://github.com/emakryo/rustdef/workflows/Test/badge.svg?branch=master)](https://github.com/emakryo/rustdef/actions?query=branch%3Amaster)
[![PyPI version](https://badge.fury.io/py/rustdef.svg)](https://badge.fury.io/py/rustdef)

Jupyter extension for jupyter notebook and rust user.

You can define functions in rust and run them as python functions.
This extension is built on [PyO3](https://github.com/PyO3/pyo3) and
[maturin](https://github.com/PyO3/maturin).

## Examples

- [Get Started](examples/Get%20started.ipynb)
- [Type conversion](examples/types.ipynb)
- [Numpy example](examples/numpy.ipynb)

## Prerequisite

- Python >= 3.6 and pip >= 19.3
- [Jupyter notebook](https://jupyter.org/install.html)
- [Rust](https://www.rust-lang.org/tools/install)
- [cargo-edit](https://crates.io/crates/cargo-edit)

## Install

```shell script
$ pip install rustdef
```

## Usage

Define rust functions,
```rust
%%rustdef
#[pyfunction]
fn my_func(x: i64, y: &str) -> i64 {
    println!("{}", y);
    x + y.len() as i64
}
```

Add dependencies, (e.g. `num` crate)
```
%rustdef deps add num@0.4.0
```

Defined dependencies are valid only in the current notebook.

Show dependencies,
```
%rustdef deps show
```

```
num = "0.4.0"

[pyo3]
version = "0.13.2"
features = [ "extension-module",]
```

`pyo3` is included by default.

## Develop

### How it works?

Roughly, definitions in rustdef are available in python after the following steps.

1. Each rustdef magic cell is populated with module definition of pyo3
2. A new crate is generated for the rustdef cell
3. The crate is compiled into a python wheel by `maturin`
4. Install the wheel with pip
5. Functions with `#[pyfunction]` attributes are exported into interpreter name space in notebook
6. Ready to call the function in notebook!

### Build

`maturin` is required.

```shell script
$ pip install maturin
$ maturin build
$ pip install target/wheels/rustdef-{version}-{python}-{platform}.whl
```

### ToDo

- [ ] execute within rustdef cell
- [ ] class/module supports
- [ ] customizable module name
- [ ] use functions defined in another cell
- [ ] verbose flag
- [ ] serde support
- [ ] windows support
