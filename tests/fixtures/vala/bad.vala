// Locale-dependent case mapping. Each flagged line has an EXPECT marker.
public class Probe {
    public bool is_integer (string type) {
        return type.down () == "integer"; // EXPECT DL006 high
    }

    public string kind (string ext) {
        switch (ext.up ()) { // EXPECT DL006 high
        case "BMP":
            return "bitmap";
        case "TIFF":
            return "tiff";
        default:
            return "";
        }
    }

    public bool is_config (string path) {
        var lower = path.down (); // EXPECT DL006 high
        return lower.has_suffix (".ini");
    }

    public string title (string s) {
        return s.up (); // EXPECT DL006 low
    }

    public string? lookup (HashTable<string, string> map, string name) {
        return map.lookup (name.down ()); // EXPECT DL006 high
    }
}
