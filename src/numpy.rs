use ndarray::{ArrayD, ArrayViewD, ArrayViewMutD};
use numpy::{PyArray, TypeNum};
use pyo3::exceptions::RuntimeError;
use pyo3::{types::PyAny, FromPy, FromPyObject, IntoPy, PyErr, PyObject, PyResult, Python};
use std::convert::TryFrom;

/// Wrapper type to connect ndarray in python and ndarray in rust .
pub enum Array<'a, T> {
    Mut(ArrayViewMutD<'a, T>),
    View(ArrayViewD<'a, T>),
    Own(ArrayD<T>),
}

impl<'a, T: TypeNum> FromPy<Array<'a, T>> for PyObject {
    fn from_py(other: Array<'a, T>, py: Python) -> PyObject {
        let a = match other {
            Array::Mut(a) => PyArray::from_array(py, &a),
            Array::View(a) => PyArray::from_array(py, &a),
            Array::Own(a) => PyArray::from_owned_array(py, a),
        };
        a.into_py(py)
    }
}

impl<'a, T: TypeNum> TryFrom<Array<'a, T>> for ArrayViewMutD<'a, T> {
    type Error = PyErr;
    fn try_from(x: Array<'a, T>) -> Result<Self, Self::Error> {
        x.as_mut_array()
    }
}

impl<'a, T: TypeNum> From<&'a Array<'a, T>> for ArrayViewD<'a, T> {
    fn from(x: &'a Array<'a, T>) -> Self {
        x.as_array()
    }
}

impl<'a, T: TypeNum> Array<'a, T> {
    /// Convert Numpy array to mutable array.
    /// If this is not a function argument, this call raise an RuntimeError
    pub fn as_mut_array(self) -> PyResult<ArrayViewMutD<'a, T>> {
        match self {
            Array::Mut(a) => Ok(a),
            Array::View(_) => RuntimeError::into("Immutable array"),
            Array::Own(_) => RuntimeError::into("Live too short"),
        }
    }
    /// Convert Numpy array to immutable array reference.
    pub fn as_array(&'a self) -> ArrayViewD<'a, T> {
        match self {
            Array::Mut(a) => a.view(),
            Array::View(a) => a.view(),
            Array::Own(a) => a.view(),
        }
    }
}

impl<'a, T: TypeNum + Clone> Array<'a, T> {
    /// Convert Numpy array to owned array.
    pub fn to_array(&self) -> ArrayD<T> {
        match self {
            Array::Mut(a) => a.view().to_owned(),
            Array::View(a) => a.to_owned(),
            Array::Own(a) => a.clone(),
        }
    }
}

impl<'a, T: TypeNum> FromPyObject<'a> for Array<'a, T> {
    fn extract(obj: &'a PyAny) -> PyResult<Self> {
        let a: &PyArray<_, _> = FromPyObject::extract(obj)?;
        Ok(Array::Mut(a.as_array_mut()))
    }
}

impl<'a, T: TypeNum> From<ArrayD<T>> for Array<'a, T> {
    fn from(x: ArrayD<T>) -> Self {
        Array::Own(x)
    }
}

impl<'a, T: TypeNum> From<&'a ArrayD<T>> for Array<'a, T> {
    fn from(x: &'a ArrayD<T>) -> Self {
        Array::View(x.view())
    }
}

impl<'a, T: TypeNum> From<&'a mut ArrayD<T>> for Array<'a, T> {
    fn from(x: &'a mut ArrayD<T>) -> Self {
        Array::Mut(x.view_mut())
    }
}

impl<'a, T: TypeNum> From<ArrayViewMutD<'a, T>> for Array<'a, T> {
    fn from(x: ArrayViewMutD<'a, T>) -> Self {
        Array::Mut(x)
    }
}

impl<'a, T: TypeNum> From<ArrayViewD<'a, T>> for Array<'a, T> {
    fn from(x: ArrayViewD<'a, T>) -> Self {
        Array::View(x)
    }
}
