__version__ = "0.1.0"
__develop__ = True

from .magic import RustdefMagic


def load_ipython_extension(ipython):
    print("load rustdef")

    rust_magic = RustdefMagic(ipython)
    ipython.register_magic_function(
        rust_magic.invoke, magic_kind="line_cell", magic_name="rustdef"
    )


def unload_ipython_extension(ipython):
    print("unload rustdef")
