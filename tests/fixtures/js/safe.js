// Nothing in this file may be reported.
import GLib from 'gi://GLib';

export function isFile(scheme) {
    return scheme.toLowerCase() === 'file';
}

export function isFileEn(scheme) {
    return scheme.toLocaleLowerCase('en-US') === 'file';
}

export function sortNames(names) {
    return names.sort((a, b) => a.localeCompare(b, undefined, {sensitivity: 'base'}));
}

export function isPng(name) {
    return name.toLocaleLowerCase() === 'png';
}

export function ascii(name) {
    return GLib.ascii_strdown(name, -1) === 'integer';
}

const re = /x.toLocaleLowerCase() === 'file'/;
const doc = `s.toLocaleLowerCase() === 'file'`;
// s.toLocaleLowerCase() === 'file'

export function suppressed(s) {
    return s.toLocaleLowerCase() === 'ini'; // dotless: ignore
}
