use std::io;
use pyo3::Python;
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
    return sys.stdout.write(buf.decode('utf-8'))
", "write_fn.py", "write_fn").unwrap();
        let ret = write_fn.call1("write", (buf,));
        dbg!(&ret);
        ret.map_err(|_| -> io::Error { io::ErrorKind::Other.into() })?;
        Ok(buf.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        self.0.run("import sys; sys.stdout.flush()", None, None).unwrap();
        Ok(())
    }
}

