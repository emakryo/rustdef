use pyo3::exceptions::RuntimeError;
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use syn;
use std::path::Path;
use zip;
use std::fmt::Display;
use std::io::{Cursor, copy};
use std::fs;

fn runtime_error<E: Display>(e: E) -> PyErr {
    RuntimeError::py_err(format!("{}", e))
}

fn has_fuction_attribute(item: &syn::Item, attr: &str) -> bool {
    let itemfn = if let syn::Item::Fn(item) = item {
        item
    } else {
        return false;
    };

    for a in itemfn.attrs.iter() {
        match a.path.get_ident().map(|t| t.to_string()) {
            Some(x) if &x == attr => { return true; },
            _ => ()
        }
    }
    false
}

#[pyfunction]
fn export_names(code: &str) -> Vec<String> {
    let parsed: syn::File = if let Ok(f) = syn::parse_str(code) {
        f
    } else {
        return Vec::new();
    };

    let mut names = Vec::new();
    for item in parsed.items.iter() {
        if has_fuction_attribute(item, "pyfunction") || has_fuction_attribute(item, "pyf") {
            if let syn::Item::Fn(itemfn) = item {
                names.push(itemfn.sig.ident.to_string());
            }
        }
    }
    names
}

#[pyfunction]
fn prepare_self(package_root: &str) -> PyResult<()> {
    let zipped = Cursor::new(&include_bytes!("../package.zip")[..]);
    let mut zipped = zip::ZipArchive::new(zipped)
        .map_err(runtime_error)?;

    let path = Path::new(package_root).join("rustdef");
    for i in 0..zipped.len() {
        let mut z = zipped.by_index(i).map_err(runtime_error)?;
        let name = path.join(z.sanitized_name());
        println!("{:?}", name);

        if z.is_dir() {
            fs::create_dir_all(name)?;
        } else if z.is_file() {
            if let Some(p) = name.parent() {
                fs::create_dir_all(p)?;
            }
            let mut f = fs::File::create(name)?;
            copy(&mut z, &mut f)?;
        }
    }

    Ok(())
}

#[pymodule]
fn rustdef(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(export_names))?;
    m.add_wrapped(wrap_pyfunction!(prepare_self))?;

    Ok(())
}
