// HIWIN MG rail set: fields from the ordering-code template -> configuration row + parameter overrides.
// Plain Rhai with the registered table(name, key[, column]) and refuse(kind, message), nothing else.
// The model derives the hole count n and the end distance E itself (expressions in the .sc); they are computed here too,
// for the refusal the Python generator has and for describe().

// Standard rail with the most holes that keep the end distance E >= Es (HIWIN S4 p.85: L = (n-1)P + 2E).
fn holes(length, rail) {
    let n = ((length - 2.0 * rail.Es) / rail.P).floor().to_int() + 1;
    let e = (length - (n - 1) * rail.P) / 2.0;
    #{ n: n, e: e }
}

fn g(x) {                         // Python's {:g} for the values these messages carry
    let f = x.to_float();
    if f == f.floor() && f.abs() < 1000000000.0 { f.to_int().to_string() } else { f.to_string() }
}

fn two_decimals(x) {
    let s = ((x * 100.0).round() / 100.0).to_string();
    let dot = s.index_of(".");
    if dot < 0 { s + ".00" } else if s.len() - dot == 2 { s + "0" } else { s }
}

fn resolve(f) {
    let rail = table("rails", f.size);
    let row = f.block + "-" + f.size;
    if rail == () || table("blocks", row) == () {
        refuse("invalid", `MGN${f.size}${f.block}: size not in this table (have 7, 9, 12, 15)`);
    }
    if f.blocks < 1 || f.blocks > 4 {
        refuse("invalid", `${f.blocks} blocks per rail: this generator draws 1 to 4`);
    }
    if f.length > rail.max_len {
        refuse("invalid", `MGNR${f.size} max single length is ${rail.max_len} mm`);
    }
    if f.length.to_float() < 2.0 * rail.Es.to_float() - 0.000000001 {
        let gl = g(f.length); let ge = g(rail.Es);
        refuse("invalid", `rail length ${gl} is shorter than two end distances (2 x ${ge} mm): no mounting hole fits`);
    }
    let h = holes(f.length, rail);
    if h.e < rail.Es - 0.000000001 {
        refuse("invalid", `rail length ${f.length.to_float()} leaves end distance ${two_decimals(h.e)} < ${rail.Es} mm`);
    }
    #{
        configuration: row,
        parameters: #{ length: `${f.length} mm`, blocks: `${f.blocks}` }
    }
}

fn describe(f) {
    let rail = table("rails", f.size);
    let h = holes(f.length, rail);
    `MGNR${f.size} rail of ${f.length} mm: ${h.n} holes at pitch ${rail.P} mm, end distance ${h.e} mm; ${f.blocks} MGN${f.size}${f.block} block(s)`
}
