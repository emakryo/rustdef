pub mod array;
pub use array::Numpy;

pub mod io;
pub use io::PyWrite;

use syn;
use quote::{quote, format_ident};
use pyo3::prelude::*;
use pyo3::{exceptions::RuntimeError, wrap_pyfunction};

fn is_pyfunction(item: &syn::Item) -> bool {
    let itemfn = if let syn::Item::Fn(item) = item {
        item
    } else {
        return false;
    };

    let attr = &syn::parse2::<syn::ItemFn>(quote!{
        #[pyfunction]
        fn dummy () {}
    }).unwrap().attrs[0];
    itemfn.attrs.iter().any(|a| a == attr)
}

fn is_pyfn(item: &syn::Item) -> bool {
    let itemfn = if let syn::Item::Fn(item) = item {
        item
    } else {
        return false;
    };
    itemfn.attrs.iter().any(|a|
        a.path.get_ident().map(|t| t.to_string()) == Some("pyfn".to_string()))
}

#[pyfunction]
fn export_names(code: &str) -> PyResult<Vec<String>> {
    let parsed: syn::File = syn::parse_str(code).map_err(|_| {
        RuntimeError::py_err("Failed to parse code")
    })?;
    let names = parsed.items.iter().filter_map(|item| {
        if is_pyfunction(item) || is_pyfn(item) {
            if let syn::Item::Fn(itemfn) = item {
                Some(itemfn.sig.ident.to_string())
            } else {
                None
            }
        } else {
            None
        }
    }).collect();

    Ok(names)
}

#[pyfunction]
fn process_src(mod_name: &str, code: &str) -> PyResult<String> {
    let parsed: syn::File = syn::parse_str(code).map_err(|_| {
        RuntimeError::py_err("Failed to parse code")
    })?;

    let pyfunctions: Vec<_> = parsed.items.iter().filter(|&item|is_pyfunction(item)).collect();
    let pyfns: Vec<_> = parsed.items.iter().filter(|&item| is_pyfn(item)).collect();
    let others: Vec<_> = parsed.items.iter().filter(|&item| !(is_pyfn(item) || is_pyfunction(item))).collect();

    let mod_name = format_ident!("{}", mod_name);

    let tokens = quote! {
        use pyo3::prelude::*;
        use pyo3::wrap_pyfunction;

        #( #pyfunctions )*

        #( #others )*

        #[pymodule]
        fn #mod_name (_py: Python, m: &PyModule) -> PyResult<()> {
            #( #pyfns )*
            Ok(())
        }
    };
    Ok(tokens.to_string())
}

#[pymodule]
fn rustdef(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(export_names))?;
    m.add_wrapped(wrap_pyfunction!(process_src))?;

    Ok(())
}
