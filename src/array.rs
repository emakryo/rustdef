use pyo3::{FromPy, PyObject, Python, IntoPy, FromPyObject, types::PyAny, PyResult};
use ndarray::ArrayD;
use numpy::{PyArray, TypeNum};

/// Wrapper newtype for ArrayBase.
/// Implement convenient conversions

pub struct Numpy<T>(pub ArrayD<T>);

impl<T: TypeNum> FromPy<Numpy<T>> for PyObject {
    fn from_py(other: Numpy<T>, py: Python) -> PyObject {
        let a = PyArray::from_array(py, &other.0);
        a.into_py(py)
    }
}

impl<T: TypeNum> From<Numpy<T>> for ArrayD<T> {
    fn from(x: Numpy<T>) -> ArrayD<T> {
        x.0
    }
}

impl<T: TypeNum> Numpy<T> {
    pub fn as_array(&self) -> &ArrayD<T> {
        &self.0
    }
    pub fn into_array(self) -> ArrayD<T> {
        self.0
    }
}

impl<'a, T: TypeNum+Clone> FromPyObject<'a> for Numpy<T> {
    fn extract(obj: &'a PyAny) -> PyResult<Self> {
        let a: &PyArray<_, _> = FromPyObject::extract(obj)?;
        Ok(Numpy(a.to_owned_array()))
    }
}

//pyobject_native_type_convert!(
//    Numpy<T>,
//    *npyffi::PY_ARRAY_API.get_type_object(npyffi::ArrayType::PyArray_Type),
//    Some("numpy"),
//    npyffi::PyArray_Check,
//    T
//);
//
//pyobject_native_type_named!(Numpy<T>, T);

//impl<T> ::pyo3::type_object::PyTypeInfo for Numpy<T> {
//    type Type = ();
//    type BaseType = ::pyo3::types::PyAny;
//    const NAME: &'static str = "Numpy<T>";
//    const MODULE: Option<&'static str> = Some("numpy");
//    const SIZE: usize = ::std::mem::size_of::<::pyo3::ffi::PyObject>();
//    const OFFSET: isize = 0;
//    #[inline]
//    unsafe fn type_object() -> &'static mut ::pyo3::ffi::PyTypeObject {
//        &mut *npyffi::PY_ARRAY_API.get_type_object(npyffi::ArrayType::PyArray_Type)
//    }
//    #[allow(unused_unsafe)]
//    fn is_instance(ptr: &::pyo3::types::PyAny) -> bool {
//        use ::pyo3::AsPyPointer;
//        unsafe { npyffi::PyArray_Check(ptr.as_ptr()) > 0 }
//    }
//}
//impl<T> ::pyo3::type_object::PyObjectAlloc for Numpy<T> {}
//unsafe impl<T> ::pyo3::type_object::PyTypeObject for Numpy<T> {
//    fn init_type() -> std::ptr::NonNull<::pyo3::ffi::PyTypeObject> {
//        unsafe {
//            std::ptr::NonNull::new_unchecked(
//                <Self as ::pyo3::type_object::PyTypeInfo>::type_object() as *mut _,
//            )
//        }
//    }
//}
////impl<T> ::pyo3::ToPyObject for Numpy<T> {
////    #[inline]
////    fn to_object(&self, py: ::pyo3::Python) -> ::pyo3::PyObject {
////        use ::pyo3::AsPyPointer;
////        self.into_py(py)
////    }
////}
//impl<T> ::std::fmt::Debug for Numpy<T> {
//    fn fmt(&self, f: &mut ::std::fmt::Formatter) -> Result<(), ::std::fmt::Error> {
//        use ::pyo3::ObjectProtocol;
//        let s = self.repr().map_err(|_| ::std::fmt::Error)?;
//        f.write_str(&s.to_string_lossy())
//    }
//}
//impl<T> ::std::fmt::Display for Numpy<T> {
//    fn fmt(&self, f: &mut ::std::fmt::Formatter) -> Result<(), ::std::fmt::Error> {
//        use ::pyo3::ObjectProtocol;
//        let s = self.str().map_err(|_| ::std::fmt::Error)?;
//        f.write_str(&s.to_string_lossy())
//    }
//}
//impl<T> ::std::convert::AsRef<::pyo3::types::PyAny> for Numpy<T> {
//    #[inline]
//    fn as_ref(&self) -> &::pyo3::types::PyAny {
//        unsafe { &*(self as *const Numpy<T> as *const ::pyo3::types::PyAny) }
//    }
//}
//unsafe impl<T> ::pyo3::PyNativeType for Numpy<T> {}
////impl<T> ::pyo3::AsPyPointer for Numpy<T> {
////    /// Gets the underlying FFI pointer, returns a borrowed pointer.
////    #[inline]
////    fn as_ptr(&self) -> *mut ::pyo3::ffi::PyObject {
////        self.0.as_ptr()
////    }
////}
//impl<T> PartialEq for Numpy<T> {
//    #[inline]
//    fn eq(&self, o: &Numpy<T>) -> bool {
//        use ::pyo3::AsPyPointer;
//        self.as_ptr() == o.as_ptr()
//    }
//}