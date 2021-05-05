use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

fn has_fuction_attribute(item: &syn::Item, attr: &str) -> bool {
    let itemfn = if let syn::Item::Fn(item) = item {
        item
    } else {
        return false;
    };

    for a in itemfn.attrs.iter() {
        match a.path.get_ident().map(|t| t.to_string()) {
            Some(x) if x == attr => {
                return true;
            }
            _ => (),
        }
    }
    false
}

#[pyfunction]
fn get_function_names_with_attribute(code: &str, attr: &str) -> Vec<String> {
    let parsed: syn::File = if let Ok(f) = syn::parse_str(code) {
        f
    } else {
        return Vec::new();
    };

    let mut names = Vec::new();
    for item in parsed.items.iter() {
        if has_fuction_attribute(item, attr) {
            if let syn::Item::Fn(itemfn) = item {
                names.push(itemfn.sig.ident.to_string());
            }
        }
    }
    names
}

#[pymodule]
fn rustdef(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(get_function_names_with_attribute))?;

    Ok(())
}
