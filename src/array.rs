use std::convert::TryFrom;
use pyo3::{FromPy, PyObject, Python, IntoPy, FromPyObject, types::PyAny, PyResult, PyErr};
use pyo3::exceptions::RuntimeError;
use ndarray::{ArrayD, ArrayViewMutD, ArrayViewD};
use numpy::{PyArray, TypeNum};

/// Wrapper type to connect ndarray in python and ndarray in rust .
pub enum Numpy<'a, T>{
    Mut(ArrayViewMutD<'a, T>),
    View(ArrayViewD<'a, T>),
    Own(ArrayD<T>),
}

impl<'a, T: TypeNum> FromPy<Numpy<'a, T>> for PyObject {
    fn from_py(other: Numpy<'a, T>, py: Python) -> PyObject {
        let a = match other {
            Numpy::Mut(a) => PyArray::from_array(py, &a),
            Numpy::View(a) => PyArray::from_array(py, &a),
            Numpy::Own(a) => PyArray::from_owned_array(py, a),
        };
        a.into_py(py)
    }
}

impl<'a, T: TypeNum> TryFrom<Numpy<'a, T>> for ArrayViewMutD<'a, T> {
    type Error = PyErr;
    fn try_from(x: Numpy<'a, T>) -> Result<Self, Self::Error> {
        x.as_mut_array()
    }
}

impl<'a, T: TypeNum> From<&'a Numpy<'a, T>> for ArrayViewD<'a, T> {
    fn from(x: &'a Numpy<'a, T>) -> Self {
        x.as_array()
    }
}

impl<'a, T: TypeNum> Numpy<'a, T> {
    /// Convert Numpy array to mutable array.
    /// If this is not a function argument, this call raise an RuntimeError
    pub fn as_mut_array(self) -> PyResult<ArrayViewMutD<'a, T>> {
        match self {
            Numpy::Mut(a) => Ok(a),
            Numpy::View(_) => RuntimeError::into("Immutable array"),
            Numpy::Own(_) => RuntimeError::into("Live too short"),
        }
    }
    /// Convert Numpy array to immutable array reference.
    pub fn as_array(&'a self) -> ArrayViewD<'a, T> {
        match self {
            Numpy::Mut(a) => a.view(),
            Numpy::View(a) => a.view(),
            Numpy::Own(a) => a.view(),
        }
    }
}

impl<'a, T: TypeNum + Clone> Numpy<'a, T> {
    /// Convert Numpy array to owned array.
    pub fn to_array(&self) -> ArrayD<T> {
        match self {
            Numpy::Mut(a) => a.view().to_owned(),
            Numpy::View(a) => a.to_owned(),
            Numpy::Own(a) => a.clone(),
        }
    }
}

impl<'a, T: TypeNum> FromPyObject<'a> for Numpy<'a, T> {
    fn extract(obj: &'a PyAny) -> PyResult<Self> {
        let a: &PyArray<_, _> = FromPyObject::extract(obj)?;
        Ok(Numpy::Mut(a.as_array_mut()))
    }
}

impl<'a, T: TypeNum> From<ArrayD<T>> for Numpy<'a, T> {
    fn from(x: ArrayD<T>) -> Self {
        Numpy::Own(x)
    }
}

impl<'a, T: TypeNum> From<&'a ArrayD<T>> for Numpy<'a, T> {
    fn from(x: &'a ArrayD<T>) -> Self {
        Numpy::View(x.view())
    }
}

impl<'a, T: TypeNum> From<&'a mut ArrayD<T>> for Numpy<'a, T> {
    fn from(x: &'a mut ArrayD<T>) -> Self {
        Numpy::Mut(x.view_mut())
    }
}

impl<'a, T: TypeNum> From<ArrayViewMutD<'a, T>> for Numpy<'a, T> {
    fn from(x: ArrayViewMutD<'a, T>) -> Self {
        Numpy::Mut(x)
    }
}

impl<'a, T: TypeNum> From<ArrayViewD<'a, T>> for Numpy<'a, T> {
    fn from(x: ArrayViewD<'a, T>) -> Self {
        Numpy::View(x)
    }
}
