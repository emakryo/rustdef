# rustdef

![](https://github.com/emakryo/rustdef/workflows/Test/badge.svg?branch=master)

Jupyter extension for jupyter notebook and rust user.

You can define functions in rust and then run as python functions.
This extension is built on [PyO3](https://github.com/PyO3/pyo3) and
[maturin](https://github.com/PyO3/maturin).

## Examples

- [Simple example](examples/simple.ipynb)
- [Type conversion](examples/types.ipynb)
- [Numpy example](examples/numpy.ipynb)

## Install

[Jupyter notebook](https://jupyter.org/install.html) and
[nightly rust](https://www.rust-lang.org/tools/install) are required.
Then, you can install `rustdef` by `pip`.

```shell script
$ pip install rustdef
```

## Magic command

Add dependencies
```
%rustdef depends CRATE...
```

Define rust functions
```
%%rustdef
#[pyfunction]
fn my_func(x: i64, y: &str) -> i64 {
    println!("{}", y);
    x + y.len() as i64
}
```
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
- [ ] specify dependency crate version
- [ ] class/module supports
- [ ] customizable module name
- [ ] verbose flag
- [ ] serde support
- [ ] windows support
