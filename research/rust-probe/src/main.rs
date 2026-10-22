// Locale probe for Rust string APIs.
// Usage: LC_ALL=LOCALE cargo run [--features glib] -- LOCALE
//
// Rust never calls setlocale() itself. With the "glib" feature the probe
// calls GLib's C case mapping twice: before setlocale() (plain Rust binary)
// and after setlocale(LC_ALL, "") (what gtk::init() does).

use std::env;

fn emit(loc: &str, api: &str, result: &str) {
    println!("rust\t{}\t{}\t{}", api, loc, result.escape_unicode_non_ascii());
}

trait EscapeNonAscii {
    fn escape_unicode_non_ascii(&self) -> String;
}

impl EscapeNonAscii for str {
    fn escape_unicode_non_ascii(&self) -> String {
        self.chars()
            .map(|c| if c.is_ascii() { c.to_string() } else { c.escape_unicode().to_string() })
            .collect()
    }
}

fn main() {
    let loc = env::args().nth(1).unwrap_or_default();
    let upper = String::from("INTEGER");
    let lower = String::from("integer");

    emit(&loc, "str::to_lowercase()", &upper.to_lowercase());
    emit(&loc, "str::to_uppercase()", &lower.to_uppercase());
    emit(&loc, "str::to_ascii_lowercase()", &upper.to_ascii_lowercase());
    emit(&loc, "str::eq_ignore_ascii_case()",
         if upper.eq_ignore_ascii_case(&lower) { "equal" } else { "NOT equal" });

    #[cfg(feature = "glib")]
    unsafe {
        use std::ffi::{CStr, CString};
        let c = CString::new(upper.as_str()).unwrap();
        let down = |label: &str| {
            let p = glib::ffi::g_utf8_strdown(c.as_ptr(), -1);
            emit(&loc, label, CStr::from_ptr(p).to_str().unwrap());
            glib::ffi::g_free(p as *mut _);
        };
        down("g_utf8_strdown() without setlocale()");
        libc::setlocale(libc::LC_ALL, b"\0".as_ptr() as *const _);
        down("g_utf8_strdown() after setlocale(LC_ALL, \"\")");
    }
}
