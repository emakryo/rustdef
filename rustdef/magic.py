import os
import subprocess
from argparse import ArgumentParser
from contextlib import contextmanager
from pathlib import Path
from hashlib import sha1

import toml
from .rustdef import export_names, process_src  # rust functions

parser = ArgumentParser()

subparser = parser.add_subparsers()
depends_parser = subparser.add_parser('depends')
depends_parser.set_defaults(command="depends")
depends_parser.add_argument('crates', nargs='+')


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

[dependencies]
{}
rustdef = {{ path = "/Users/ryosuke.kamesawa/Develop/rustdef" }} # TODO: udpate here when released 

[dependencies.pyo3]
version = "0.8"
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
        self.dependencies = {}
        self.root = Path.cwd() / ".rustdef"
        self.root.mkdir(exist_ok=True)
        (self.root / ".cargo").mkdir(exist_ok=True)
        (self.root / ".cargo/config").write_text(self.config)

    def invoke(self, line, cell=None):
        if cell is None:
            self.command(line)
        else:
            self.run(line, cell)

    def command(self, line):
        args = parser.parse_args(line.split())
        if args.command == "depends":
            self.add_dependencies(args.crates)

    def add_dependencies(self, crates):
        for crate in crates:
            if "==" in crate:
                sep_idx = crate.index("==")
                self.dependencies[crate[:sep_idx]] = crate[sep_idx+2:]
            else:
                self.dependencies[crate] = "*"

    def run(self, line, cell):
        mod_name, exported_functions = self.add_src(cell)

        new_mod_names = self.mod_names + [mod_name]
        self.update_workspace(new_mod_names)

        if not self.exists_wheel(mod_name):
            print("Building..")
            self.build(mod_name)
        else:
            print("Use previous build")

        with self.installed(mod_name):
            exec_line = f"from {mod_name} import {','.join(exported_functions)}"
            ls = {}
            gs = {}
            exec(exec_line, gs, ls)
            self.ipython.push({fn: ls[fn] for fn in exported_functions})
            self.mod_names = new_mod_names

    def add_src(self, src):
        mod_name = f"rustdef_cell_{sha1(bytes(src, 'utf-8')).hexdigest()}"
        exported_functions = export_names(src)

        package_root = self.root / mod_name
        package_root.mkdir(exist_ok=True)
        (package_root / "Cargo.toml").write_text(self.cargo_tpl.format(mod_name, toml.dumps(self.dependencies)))
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

    def exists_wheel(self, mod_name):
        wheel = list(self.root.glob(f"target/wheels/*{mod_name}*.whl"))
        return len(wheel) > 0

    def build(self, mod_name):
        cwd = Path.cwd().resolve()
        os.chdir(self.root / mod_name)
        self.ipython.system_piped("maturin build")

        if self.ipython.user_ns['_exit_code'] != 0:
            raise RuntimeError("build failed")
        os.chdir(str(cwd))

    def install(self, mod_name):
        wheel = [str(w) for w in self.root.glob(f"target/wheels/*{mod_name}*.whl")]
        ret = subprocess.run("pip install".split() + wheel)
        if ret.returncode != 0:
            print("installation failed")
            raise RuntimeError("wheel installation failed")

    def uninstall(self, mod_name):
        ret = subprocess.run(f"pip uninstall -y {mod_name.replace('_', '-')}".split())
        if ret.returncode != 0:
            print("uninstallation failed")
            raise RuntimeError("wheel uninsallation failed")

    @contextmanager
    def installed(self, mod_name):
        self.install(mod_name)
        try:
            yield
        finally:
            self.uninstall(mod_name)
