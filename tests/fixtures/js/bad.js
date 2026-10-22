// Locale-dependent case mapping. Each flagged line has an EXPECT marker.
import GLib from 'gi://GLib';

export function isFile(scheme) {
    return scheme.toLocaleLowerCase() === 'file'; // EXPECT DL007 high
}

export function isInteger(type) {
    return type.toLocaleUpperCase(undefined) === 'INTEGER'; // EXPECT DL007 high
}

export function label(s) {
    return s.toLocaleUpperCase(); // EXPECT DL007 low
}

export function isIni(name) {
    const low = GLib.utf8_strdown(name, -1); // EXPECT DL004 high
    return low.endsWith('.ini');
}

export function isIgnore(word) {
    return word.localeCompare('ignore', undefined, {sensitivity: 'base'}) === 0; // EXPECT DL008 high
}

export function lookup(map, name) {
    return map.get(name.toLocaleLowerCase()); // EXPECT DL007 high
}
