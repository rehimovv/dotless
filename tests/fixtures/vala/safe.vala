// Nothing in this file may be reported.
public class Probe {
    public bool is_integer (string type) {
        return type.ascii_down () == "integer";
    }

    public bool same (string a, string b) {
        return a.casefold () == b.casefold ();
    }

    public bool is_png (string s) {
        return s.down () == "png";
    }

    public string doc () {
        // s.down () == "integer" in a comment
        return "s.down () == \"integer\"";
    }

    public bool suppressed (string s) {
        return s.down () == "ini"; // dotless: ignore
    }
}
