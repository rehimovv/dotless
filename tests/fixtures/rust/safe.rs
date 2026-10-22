// Nothing in this file may be reported.
fn is_integer(s: &str) -> bool {
    s.to_lowercase() == "integer" || s.eq_ignore_ascii_case("INTEGER")
}

fn ascii(s: &str) -> String {
    s.to_ascii_lowercase()
}

fn folded(s: &str) -> glib::GString {
    glib::casefold(s)
}

// libc::strcasecmp(a, b) in a comment
const DOC: &str = r#"libc::tolower(c) in a raw string"#;

fn lifetimes<'a>(s: &'a str) -> &'a str {
    s
}
