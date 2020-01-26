use syn;
use quote::quote;
use pyo3::prelude::*;
use pyo3::{exceptions::RuntimeError, wrap_pyfunction};

fn is_pyfunction(itemfn: &syn::ItemFn) -> bool {
    let attr = &syn::parse2::<syn::ItemFn>(quote!{
        #[pyfunction]
        fn dummy () {}
    }).unwrap().attrs[0];
    itemfn.attrs.iter().any(|a| a == attr)
}

#[pyfunction]
fn pyfunction_names(code: &str) -> PyResult<Vec<String>> {
    let parsed: syn::File = syn::parse_str(code).map_err(|_| {
        RuntimeError::py_err("Failed to parse code")
    })?;
    let names = parsed.items.iter().filter_map(|item| {
        let itemfn = if let syn::Item::Fn(itemfn) = item {
            itemfn
        } else {
            return None;
        };

        if is_pyfunction(itemfn) {
            Some(itemfn.sig.ident.to_string())
        } else {
            None
        }
    }).collect();

    Ok(names)
}

#[pymodule]
fn rustdef(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(pyfunction_names))?;
    Ok(())
}
