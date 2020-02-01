# rustdef

Jupyter extension for jupyter notebook and rust user.

Define functions in rust and then run as python funcions.
This extension is built on [PyO3](https://github.com/PyO3/pyo3) and
[maturin](https://github.com/PyO3/maturin).

## Examples

- [Simple example](examples/simple.ipynb)
- [Numpy example](examples/numpy.ipynb)

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

Roughly, definitions in rustdef are available in python with following steps.

1. Each rustdef magic cell is populated with module definition of pyo3
2. A new member in cargo workspace is generated for each rustdef cell
3. The member crate is compiled into a python wheel by `maturin`
4. Install the wheel
5. Functions with `#[pyfunction]` attributes are exported into interpreter name space
6. Ready to call the function in jupyter!

### ToDo

- [ ] setup CI
- [ ] execute within rustdef cell
- [ ] dependency crate version
- [ ] class/module supports
- [ ] customizable module name
- [ ] verbose flag
- [ ] syntax highlight
- [ ] serde support
