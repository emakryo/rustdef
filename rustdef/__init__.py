from .magic import RustdefMagic

def load_ipython_extension(ipython):
    print("load rustdef")

    magic = RustdefMagic(ipython)
    ipython.register_magic_function(magic.invoke, magic_kind='cell', magic_name='rustdef')

def unload_ipython_extension(ipython):
    print("unload rustdef")
