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

### ToDo

- [ ] execute within rustdef cell
- [ ] dependency crate version
- [ ] class/module supports
- [ ] customizable module name
- [ ] verbose flag
- [ ] syntax highlight
- [ ] serde support
