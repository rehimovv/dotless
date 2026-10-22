// Locale probe for Vala string methods.
// Usage: probe-vala LOCALE

string loc;

void emit (string api, string result) {
    stdout.printf ("vala\t%s\t%s\t%s\n", api, loc, result.escape ());
}

void emit_cp (string api, unichar c) {
    emit (api, "U+%04X".printf ((uint) c));
}

int main (string[] args) {
    loc = args.length > 1 ? args[1] : "";
    if (Intl.setlocale (LocaleCategory.ALL, loc) == null) {
        emit ("setlocale", "FAILED");
        return 1;
    }

    // Read the inputs from a variable so the compiler cannot fold them.
    string upper = args.length > 2 ? args[2] : "INTEGER";
    string lower = upper.ascii_down ();

    emit ("string.down()", upper.down ());
    emit ("string.up()", lower.up ());
    emit ("string.casefold()", upper.casefold ());
    emit ("string.ascii_down()", upper.ascii_down ());
    emit ("string.ascii_up()", lower.ascii_up ());
    emit ("string.down() == \"integer\"", upper.down () == "integer" ? "equal" : "NOT equal");
    emit_cp ("unichar.tolower('I')", upper.get_char (0).tolower ());
    emit_cp ("unichar.toupper('i')", lower.get_char (0).toupper ());
    emit ("string.collate() sign", "%d".printf (lower.collate (upper).clamp (-1, 1)));
    return 0;
}
