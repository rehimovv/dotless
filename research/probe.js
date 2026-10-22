// Locale probe for JavaScript string APIs. Runs under both gjs and node.
// Usage: LC_ALL=LOCALE LANG=LOCALE gjs probe.js LOCALE
//        LC_ALL=LOCALE LANG=LOCALE node probe.js LOCALE

const isGjs = typeof imports !== 'undefined';
const engine = isGjs ? 'gjs' : 'node';
const args = isGjs ? ARGV : process.argv.slice(2);
const loc = args[0];
const out = isGjs ? print : s => console.log(s);

function emit(api, result) {
    const esc = String(result).replace(/[^\x20-\x7e]/g,
        c => `\\u${c.charCodeAt(0).toString(16).padStart(4, '0')}`);
    out(`${engine}\t${api}\t${loc}\t${esc}`);
}

const upper = 'INTEGER', lower = 'integer';
emit('Intl default locale', new Intl.Collator().resolvedOptions().locale);
emit('toLowerCase()', upper.toLowerCase());
emit('toUpperCase()', lower.toUpperCase());
emit('toLocaleLowerCase()', upper.toLocaleLowerCase());
emit('toLocaleUpperCase()', lower.toLocaleUpperCase());
emit("toLocaleLowerCase('en-US')", upper.toLocaleLowerCase('en-US'));
emit("toLocaleLowerCase('tr')", upper.toLocaleLowerCase('tr'));
emit("localeCompare(..., {sensitivity: 'base'}) === 0",
    upper.localeCompare(lower, undefined, {sensitivity: 'base'}) === 0 ? 'equal' : 'NOT equal');
emit('/integer/i.test("INTEGER")', /integer/i.test(upper) ? 'match' : 'NO match');

if (isGjs) {
    const GLib = imports.gi.GLib;
    emit('GLib.utf8_strdown()', GLib.utf8_strdown(upper, -1));
    emit('GLib.utf8_strup()', GLib.utf8_strup(lower, -1));
    emit('GLib.ascii_strdown()', GLib.ascii_strdown(upper, -1));
}
