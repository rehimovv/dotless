// Locale-dependent case mapping. Each flagged line has an EXPECT marker.
use std::ffi::{CStr, CString};

unsafe fn is_integer(s: &CStr) -> bool {
    let low = glib::ffi::g_utf8_strdown(s.as_ptr(), -1); // EXPECT DL004 high
    let ret = CStr::from_ptr(low).to_str() == Ok("integer");
    glib::ffi::g_free(low as *mut _);
    ret
}

unsafe fn is_ini(s: &CString) -> bool {
    libc::strcasecmp(s.as_ptr(), b"ini\0".as_ptr() as *const _) == 0 // EXPECT DL002 high
}

unsafe fn upper(c: i32) -> i32 {
    libc::toupper(c) // EXPECT DL001 low
}
