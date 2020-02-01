import os
import select
import subprocess
import threading
from argparse import ArgumentParser
from contextlib import contextmanager
from hashlib import sha1
from pathlib import Path

import toml
from IPython import get_ipython

from . import __version__
from .rustdef import export_names, prepare_self  # rust functions


def line_macic_parser():
    parser = ArgumentParser()

    subparser = parser.add_subparsers()
    depends_parser = subparser.add_parser("depends")
    depends_parser.set_defaults(command="depends")
    depends_parser.add_argument("crates", nargs="+")
    return parser


def cell_magic_parser():
    parser = ArgumentParser()
    parser.add_argument("--force-rebuild", action="store_true")
    return parser


class BuildError(Exception):
    def __init__(self):
        ...

    def _render_traceback_(self):
        return []


showtraceback = None


def exception_handler(
    exc_tuple=None,
    filename=None,
    tb_offset=None,
    exception_only=False,
    running_compiled_code=False,
):
    ipython = get_ipython()
    print(ipython.get_exception_only())
    ipython.showtraceback = showtraceback


def wrap(func):
    def wrapper(*args, **kwargs):
        stdout_backup = os.dup(1)
        r, w = os.pipe()
        os.close(1)
        os.dup2(w, 1)
        os.close(w)
        r2, w2 = os.pipe()

        def redirect():
            while True:
                rs, _, _ = select.select([r, r2], [], [])

                if r in rs:
                    buf = os.read(r, 1000)
                    print(buf.decode("utf-8"), end="")

                if r2 in rs:
                    break

        thread = threading.Thread(target=redirect)
        thread.start()

        get_ipython().showtraceback = exception_handler
        ret = func(*args, **kwargs)
        os.write(w2, b"x")

        thread.join()
        os.close(1)
        os.dup2(stdout_backup, 1)
        os.close(stdout_backup)

        os.close(r2)
        os.close(w2)

        return ret

    return wrapper


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

[dependencies.rustdef]
 path = "../rustdef"
 default-features = false
 features = ["numpy-bridge"]

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
// #![allow(unused)]
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
        global showtraceback
        showtraceback = ipython.showtraceback
        self.ipython = ipython
        self.line_parser = line_macic_parser()
        self.cell_parser = cell_magic_parser()
        self.mod_names = []
        self.dependencies = {}
        self.root = Path.cwd() / ".rustdef"
        self.root.mkdir(exist_ok=True)
        (self.root / ".cargo").mkdir(exist_ok=True)
        (self.root / ".cargo/config").write_text(self.config)
        prepare_self(str(self.root))

    def invoke(self, line, cell=None):
        if cell is None:
            self.command(line)
        else:
            self.run(line, cell)

    def command(self, line):
        args = self.line_parser.parse_args(line.split())
        if args.command == "depends":
            self.add_dependencies(args.crates)

    def add_dependencies(self, crates):
        for crate in crates:
            if "==" in crate:
                sep_idx = crate.index("==")
                self.dependencies[crate[:sep_idx]] = crate[sep_idx + 2 :]
            else:
                self.dependencies[crate] = "*"

    def run(self, line, cell):
        mod_name = f"rustdef_cell_{sha1(bytes(cell, 'utf-8')).hexdigest()}"
        exported_functions = self.add_src(mod_name, cell)
        args = self.cell_parser.parse_args(line.split())

        new_mod_names = self.mod_names + [mod_name]
        self.update_workspace(new_mod_names)

        if args.force_rebuild or not self.exists_wheel(mod_name):
            print("Building..")
            self.build(mod_name)
        else:
            print("Use previous build")

        with self.installed(mod_name):
            functions = ",".join(exported_functions)
            exec_line = f"from {mod_name} import {functions}"
            ls = {}
            gs = {}
            exec(exec_line, gs, ls)
            self.ipython.push({fn: wrap(ls[fn]) for fn in exported_functions})
            self.mod_names = new_mod_names

    def add_src(self, mod_name, src):
        exported_functions = export_names(src)

        package_root = self.root / mod_name
        package_root.mkdir(exist_ok=True)
        (package_root / "Cargo.toml").write_text(
            self.cargo_tpl.format(
                mod_name, toml.dumps(self.dependencies), __version__
            )
        )
        (package_root / "src").mkdir(exist_ok=True)

        register_function = "\n".join(
            [
                f"m.add_wrapped(wrap_pyfunction!({fname}))?;"
                for fname in exported_functions
            ]
        )

        src = self.lib_tpl.format(mod_name, register_function, src)
        (package_root / f"src/lib.rs").write_text(src)

        return exported_functions

    def update_workspace(self, mod_names):
        (self.root / "Cargo.toml").write_text(
            self.workspace_tpl.format(
                "[" + ",".join([f'"{p}"' for p in mod_names]) + "]"
            )
        )

    def exists_wheel(self, mod_name):
        wheel = list(self.root.glob(f"target/wheels/*{mod_name}*.whl"))
        return len(wheel) > 0

    def build(self, mod_name):
        cwd = Path.cwd().resolve()
        os.chdir(self.root / mod_name)
        self.ipython.system_piped("maturin build --release")
        exit_code = self.ipython.user_ns["_exit_code"]
        os.chdir(str(cwd))
        if exit_code != 0:
            raise BuildError()

    def install(self, mod_name):
        for wheel in self.root.glob(f"target/wheels/*{mod_name}*.whl"):
            ret = subprocess.run(["pip", "install", str(wheel)])
            if ret.returncode != 0:
                print("ignore", str(wheel))
            else:
                return

        raise RuntimeError("wheel installation failed")

    def uninstall(self, mod_name):
        mod_name_kebab = mod_name.replace("_", "-")
        ret = subprocess.run(f"pip uninstall -qy {mod_name_kebab}".split())
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
