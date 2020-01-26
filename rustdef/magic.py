import os
import subprocess
from pathlib import Path
from hashlib import sha1
from tempfile import TemporaryDirectory
from .rustdef import pyfunction_names  # rust function


class RustdefMagic:
    workspace_tpl = """
[workspace]
members = {}
"""
    cargo_tpl = """
[package]
name = "{}"
authors = ["rustdef-magic"]
version = "0.1.0"
edition = "2018"

[lib]
crate-type = ["cdylib"]

[dependencies.pyo3]
version = "0.9.0-alpha.1"
features = ["extension-module"]
"""
    config = """
[target.x86_64-apple-darwin]
rustflags = [
  "-C", "link-arg=-undefined",
  "-C", "link-arg=dynamic_lookup",
]
"""
    lib_tpl = """
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
#[pymodule]
fn {}(_py: Python, m: &PyModule) -> PyResult<()> {{
{}
Ok(())
}}

{}
"""

    def __init__(self, ipython):
        self.ipython = ipython
        self.mod_names = []
        self.root = Path.cwd() / ".rustdef"
        self.root.mkdir(exist_ok=True)
        (self.root / ".cargo").mkdir(exist_ok=True)
        (self.root / ".cargo/config").write_text(self.config)

    def invoke(self, line, cell):
        mod_name, exported_functions = self.add_src(cell)

        new_mod_names = self.mod_names + [mod_name]
        self.update_workspace(new_mod_names)
        print("Building..")
        self.build(mod_name)

        exec_line = f"from {mod_name} import {','.join(exported_functions)}"
        ls = {}
        gs = {}
        exec(exec_line, gs, ls)
        self.ipython.push({fn: ls[fn] for fn in exported_functions})

        self.mod_names = new_mod_names

    def add_src(self, src):
        mod_name = f"rustdef_cell_{sha1(bytes(src, 'utf-8')).hexdigest()}"
        exported_functions = pyfunction_names(src)

        package_root = self.root / mod_name
        package_root.mkdir(exist_ok=True)
        (package_root / "Cargo.toml").write_text(self.cargo_tpl.format(mod_name))
        (package_root / "src").mkdir(exist_ok=True)

        register_function = "\n".join([
            f"m.add_wrapped(wrap_pyfunction!({fname}))?;" for fname in exported_functions
        ])

        src = self.lib_tpl.format(mod_name, register_function, src)
        (package_root / f"src/lib.rs").write_text(src)

        return mod_name, exported_functions

    def update_workspace(self, mod_names):
        (self.root / "Cargo.toml").write_text(self.workspace_tpl.format(
            "[" + ",".join([f'"{p}"' for p in mod_names]) + "]"))

    def build(self, mod_name):
        cwd = Path.cwd().resolve()
        os.chdir(self.root / mod_name)
        self.ipython.system_piped("maturin build")

        wheel = list(self.root.glob("target/wheels/*.whl"))
        ret = subprocess.run("pip install -U".split() + wheel)
        if ret.returncode != 0:
            print("installation failed")
            raise RuntimeError("wheel installation failed")

        os.chdir(cwd)
