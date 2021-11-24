import os
import select
import subprocess
import sys
import threading
import uuid
from argparse import ArgumentParser
from contextlib import contextmanager
from hashlib import sha1
from pathlib import Path

import toml
from IPython import get_ipython
from IPython.display import display, Javascript

from .rustdef import get_function_names_with_attribute  # rust functions


def line_macic_parser():
    parser = ArgumentParser(prog="%rustdef")

    subparser = parser.add_subparsers()
    deps_parser = subparser.add_parser("deps", help="Dependencies related subcommands")
    deps_subparser = deps_parser.add_subparsers()
    add_parser = deps_subparser.add_parser(
        "add", help="Add dependencies", description="Add dependencies"
    )
    add_parser.set_defaults(command="add")
    add_parser.add_argument(
        "args", nargs="+", help="Dependencies to be added. See cargo-edit"
    )

    show_parser = deps_subparser.add_parser("show", help="Show dependencies")
    show_parser.set_defaults(command="show")

    rm_parser = deps_subparser.add_parser("rm", help="Remove dependencies")
    rm_parser.set_defaults(command="rm")
    rm_parser.add_argument(
        "args", nargs="+", help="Dependencies to be removed. See cargo-edit"
    )

    clean_parser = subparser.add_parser(
        "clean", help="Clean build cache", description="Clean build cache"
    )
    clean_parser.set_defaults(command="clean")
    clean_parser.add_argument(
        "--cargo", action="store_true", help="Run `cargo clean` additionally"
    )
    return parser


def cell_magic_parser():
    parser = ArgumentParser(
        prog="%%rustdef",
        description="Define rust functions in notebook cells. "
        "Functions with #[pyfunction] are available in python",
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Build code even if there exists cache",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Build with release profile. (debug profile by default)",
    )
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
        stderr_backup = os.dup(2)
        r, w = os.pipe()
        os.close(1)
        os.close(2)
        os.dup2(w, 1)
        os.dup2(w, 2)
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
        os.dup2(stderr_backup, 2)
        os.close(stderr_backup)

        os.close(r2)
        os.close(w2)

        return ret

    return wrapper


class RustdefMagic:
    workspace_tpl = """
[workspace]
members = {}
"""

    config = """
[target.x86_64-apple-darwin]
rustflags = [
  "-C", "link-arg=-undefined",
  "-C", "link-arg=dynamic_lookup",
]
"""

    lib_tpl = """
#![allow(unused)]
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[pymodule]
fn {}(_py: Python, m: &PyModule) -> PyResult<()> {{
{}

{}
Ok(())
}}
"""

    js = """
require(['notebook/js/codecell'], function(codecell) {
    codecell.CodeCell.options_default.highlight_modes['text/x-rustsrc']
        = {'reg':[/^%%rustdef/]} ;
    Jupyter.notebook.events.one('kernel_ready.Kernel', function(){
        Jupyter.notebook.get_cells().map(function(cell){
        if (cell.cell_type == 'code'){ cell.auto_highlight(); } }) ;
    });
});
"""

    def __init__(self, ipython):
        global showtraceback
        showtraceback = ipython.showtraceback
        self.ipython = ipython
        self.line_parser = line_macic_parser()
        self.cell_parser = cell_magic_parser()
        self.dependencies = {}
        self.root = Path.home() / ".rustdef"
        self.root.mkdir(exist_ok=True)
        (self.root / ".cargo").mkdir(exist_ok=True)
        (self.root / ".cargo/config").write_text(self.config)

        display(Javascript(self.js))

        self.create_template()

    def create_template(self):
        self.template_uuid = f"template-{uuid.uuid1()}"
        self.template_path = self.root / self.template_uuid
        self.template_path.mkdir(parents=True)
        self.add_workspace_member(self.template_uuid)

        subprocess.run(
            ["cargo", "init", "--lib", "--vcs", "none"],
            cwd=self.template_path,
            check=True,
        )
        with open(self.template_path / "Cargo.toml", "a") as f:
            f.write("\n" "[lib]\n" 'crate-type = ["cdylib"]\n\n')

        # numpy compatible version
        pyo3 = ["pyo3@0.15.1", "--features", "extension-module"]
        try:
            self.add_dependencies(pyo3)
        except subprocess.CalledProcessError as e:
            print("Please install cargo-edit", file=sys.stderr)
            raise e

    def invoke(self, line, cell=None):
        if cell is None:
            self.command(line)
        else:
            self.run(line, cell)

    def command(self, line):
        try:
            args = self.line_parser.parse_args(line.split())
        except SystemExit:
            return

        if args.command == "add":
            self.add_dependencies(args.args)

        elif args.command == "rm":
            self.rm_dependencies(args.args)

        elif args.command == "show":
            self.show_dependencies()

        elif args.command == "clean":
            self.clean(args.cargo)

    def add_dependencies(self, args):
        cmd = ["cargo", "add"] + args
        subprocess.run(cmd, cwd=self.template_path, check=True)

    def rm_dependencies(self, args):
        cmd = ["cargo", "rm"] + args
        subprocess.run(cmd, cwd=self.template_path, check=True)

    def show_dependencies(self):
        with open(self.template_path / "Cargo.toml") as f:
            manifest = toml.load(f)

        print(toml.dumps(manifest["dependencies"]))

    def clean(self, cargo):
        wheels = (self.root / "target/wheels").glob("*.whl")
        for w in wheels:
            w.unlink()

        if cargo:
            cwd = os.getcwd()
            os.chdir(str(self.root))
            self.ipython.system_raw("cargo clean")
            os.chdir(cwd)

    def run(self, line, cell):
        try:
            args = self.cell_parser.parse_args(line.split())
        except SystemExit:
            return

        crate_name = f"rustdef_cell_{sha1(bytes(cell, 'utf-8')).hexdigest()}"
        exported_functions = [
            fn for fns in self.add_src(crate_name, cell).values() for fn in fns
        ]

        self.add_workspace_member(crate_name)

        if args.force_rebuild or not self.exists_wheel(crate_name):
            print("Building..")
            self.build(crate_name, args.release)
        else:
            print("Use previous build")

        with self.installed(crate_name):
            functions = ",".join(exported_functions)
            exec_line = f"from {crate_name} import {functions}"
            ls = {}
            gs = {}
            exec(exec_line, gs, ls)
            self.ipython.push({fn: wrap(ls[fn]) for fn in exported_functions})

    def add_src(self, crate_name, src):
        functions = {
            "pyfn": get_function_names_with_attribute(src, "pyfn"),
            "pyfunction": get_function_names_with_attribute(src, "pyfunction"),
        }

        crate_root = self.root / crate_name
        crate_root.mkdir(exist_ok=True)

        manifest = toml.load(self.template_path / "Cargo.toml")
        manifest["package"]["name"] = crate_name
        with open(crate_root / "Cargo.toml", "w") as f:
            toml.dump(manifest, f)

        (crate_root / "src").mkdir(exist_ok=True)

        register_function = "\n".join(
            [
                f"m.add_wrapped(wrap_pyfunction!({fname}))?;"
                for fname in functions["pyfunction"]
            ]
        )

        src = self.lib_tpl.format(crate_name, src, register_function)
        (crate_root / "src/lib.rs").write_text(src)

        return functions

    def add_workspace_member(self, crate):

        workspace_manifest = {"workspace": {"members": []}}
        if (self.root / "Cargo.toml").exists():
            with open(self.root / "Cargo.toml", "r") as f:
                workspace_manifest = toml.load(f)

        workspace_manifest["workspace"]["members"].append(crate)

        with open(self.root / "Cargo.toml", "w") as f:
            toml.dump(workspace_manifest, f)

    def exists_wheel(self, mod_name):
        wheel = list(self.root.glob(f"target/wheels/*{mod_name}*.whl"))
        return len(wheel) > 0

    def build(self, mod_name, release):
        cwd = Path.cwd().resolve()
        os.chdir(self.root / mod_name)
        opts = [
            "--manylinux",
            "off",
            "--interpreter",
            sys.executable,
        ]
        if release:
            opts.append("--release")

        cmd = "maturin build  " + " ".join(opts)
        self.ipython.system_piped(cmd)
        exit_code = self.ipython.user_ns["_exit_code"]
        os.chdir(str(cwd))
        if exit_code != 0:
            raise BuildError()

    def install(self, mod_name):
        for wheel in self.root.glob(f"target/wheels/*{mod_name}*.whl"):
            ret = subprocess.run(f"python -m pip install {wheel}".split())
            if ret.returncode != 0:
                print("ignore", str(wheel))
            else:
                return

        raise RuntimeError("wheel installation failed")

    def uninstall(self, mod_name):
        mod_name_kebab = mod_name.replace("_", "-")
        ret = subprocess.run(f"python -m pip uninstall -qy {mod_name_kebab}".split())
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
