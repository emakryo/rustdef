use std::io;
use pyo3::{Python, AsPyPointer, PyObject, PyErr, py_run};
use pyo3::types::PyAny;
use pyo3::prelude::PyModule;

pub struct PyWrite<'p>(Python<'p>);

impl<'p> PyWrite<'p> {
    pub fn new(python: Python) -> PyWrite {
        PyWrite(python)
    }
}

impl<'p> io::Write for PyWrite<'p> {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        let write_fn = PyModule::from_code(
            self.0, "\
def write(buf):
    import sys
    return sys.stdout.write(buf)
", "write_fn.py", "write_fn").unwrap();
        let ret = write_fn.call1("write", (buf,));
        let ret = ret.map_err(|_: PyErr| io::ErrorKind::Other)?;
        Ok(buf.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        self.0.run("import sys; sys.stdout.flush()", None, None).unwrap();
        Ok(())
    }
}

