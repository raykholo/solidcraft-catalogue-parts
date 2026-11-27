// HIWIN EG guideway: fields from the ordering-code template -> configuration row + parameter overrides.
// Plain Rhai with the registered table(name, key[, column]) and refuse(kind, message), nothing else.
// Three products, three templates: a set (rail with blocks), a rail alone (EGR) and a block alone. Every refusal below is the
// Python generator's message (src/catalogue.py), in the order the Python generator checks.
// The model derives the hole count n and the end distance E itself (expressions in the .sc); they are computed here too, for the
// refusals the Python generator has.

fn g(x) {                         // Python's {:g} for the values these messages carry
    let f = x.to_float();
    if f == f.floor() && f.abs() < 1000000000.0 { f.to_int().to_string() } else { f.to_string() }
}

fn two_decimals(x) {              // Python's {:.2f}
    let s = ((x * 100.0).round() / 100.0).to_string();
    let dot = s.index_of(".");
    if dot < 0 { s + ".00" } else if s.len() - dot == 2 { s + "0" } else { s }
}

fn param(name) { table("params", name, "value") }

// the first dust-protection code (ZZ, DD or KK) standing alone in the option text, "" when there is none
fn dust_code(opt) {
    let run = "";
    for ch in opt.to_upper().chars() {
        if (ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9') {
            run += ch;
        } else {
            if run == "ZZ" || run == "DD" || run == "KK" { return run; }
            run = "";
        }
    }
    if run == "ZZ" || run == "DD" || run == "KK" { run } else { "" }
}

fn size_check(f) {
    if table("rails", f.size) == () {
        refuse("invalid", `EG size ${f.size}: catalogue sizes are 15, 20, 25, 30, 35`);
    }
}

fn rail_mount_check(rm) {
    if rm == "T" {
        refuse("not_modelled", "EGR rail mounted from the bottom (T) is valid HIWIN grammar, but the catalogue prints no tapped-hole dimensions for it (tables (1)-(3) on p.57-59 are the top-mounted R rail), so it is not drawn");
    }
}

fn options_check(f) {
    if "opt" in f && dust_code(f.opt) != "" {
        refuse("not_modelled", "dust-protection codes ZZ, DD and KK are valid HIWIN grammar; they change the overall block length (p.53), which is not drawn: leave the option out for the standard end seal and bottom seal length");
    }
}

// stainless steel (M): EG15C only. `load` is () for a rail alone.
fn stainless_check(f, load) {
    if !("mat" in f) { return false; }
    let ok = param("stainless_sizes").to_string().split("|");
    if !ok.contains(f.size) || (load != () && load != "C") {
        refuse("invalid", "stainless steel (M) exists for EG15C only (model number note 4, p.45)");
    }
    true
}

fn rail_checks(f, stainless) {
    size_check(f);
    let lim = if stainless { param("max_len_stainless") } else { param("max_len") };
    if f.length > lim.to_float() {
        let why = if stainless { " for stainless EGR15 (Table 2-2-22 note 4)" } else { "" };
        refuse("invalid", `rail length ${g(f.length)} mm above the maximum ${g(lim)} mm${why}`);
    }
    let r = table("rails", f.size);
    let lo = param("min_len");
    if f.length < lo.to_float() {
        refuse("invalid", `rail length ${g(f.length)} mm below the catalogue minimum ${g(lo)} mm (Table 2-2-1)`);
    }
    let two_es = 2.0 * r.Es.to_float();
    if f.length < two_es {
        refuse("invalid", `rail length ${g(f.length)} mm below 2 x Es = ${g(two_es)} mm`);
    }
}

// L = (n-1)P + 2E (Eq. 2.2, p.56): the most holes with Es <= E <= P/2
fn holes(length, rail) {
    let es = rail.Es.to_float();
    let p = rail.P.to_float();
    let n = ((length - 2.0 * es) / p).floor().to_int() + 1;
    let e = (length - (n - 1).to_float() * p) / 2.0;
    while e > p / 2.0 + 0.000000001 && e - p / 2.0 >= es {
        n += 1;
        e = (length - (n - 1).to_float() * p) / 2.0;
    }
    let gl = g(length);
    let e2 = two_decimals(e);
    if e < es - 0.000000001 {
        refuse("invalid", `rail length ${gl} leaves end distance ${e2} mm, below the standard ${g(es)} mm`);
    }
    if e > p / 2.0 + 0.000000001 {
        let half = g(p / 2.0);
        refuse("invalid", `rail length ${gl} leaves end distance ${e2} mm, above P/2 = ${half} mm (unstable rail end, p.56)`);
    }
    #{ n: n, e: e }
}

// the block of the row: EGH is top-mounted only
fn block_of(f) {
    if f.kind == "H" && f.mount != "A" {
        refuse("invalid", `EGH is mounted from the top only: EGH${f.size}${f.load}A (the catalogue lists EGH-SA / EGH-CA)`);
    }
    table("blocks", `EG${f.kind}-${f.load}${f.mount}-${f.size}`)
}

// what the Python generator says for a block code its regular expression does not accept (preload ZB, accuracy SP / UP on a block alone)
fn block_generic(f) {
    let code = `EG${f.kind}${f.size}${f.load}${f.mount}`;
    if f.eblock { code += "E"; }
    if "preload" in f { code += f.preload; }
    if "prec" in f { code += f.prec; }
    if "mat" in f { code += "M"; }
    if "opt" in f { code += "+" + f.opt; }
    refuse("invalid", `'${code}': expected a set EG<H|W><size><C|S><A|B><n>R<length>[Z0|ZA|ZB][C|H|P], e.g. EGH20CA2R1000ZAH, a rail EGR<size>R<length>, e.g. EGR25R1600, or a block EGW25CA`);
}

fn fit_check(f, b) {
    let gap = 10.0;                                 // BLOCK_GAP of the Python generator: the model's `gap` (illustration choice)
    let need = f.n.to_float() * b.L.to_float() + (f.n - 1).to_float() * gap;
    if need > f.length {
        let gl = g(f.length);
        let gb = g(b.L);
        let gg = g(gap);
        refuse("invalid", `${f.n} blocks of ${gb} mm with ${gg} mm gaps do not fit on a ${gl} mm rail`);
    }
}

fn resolve_set(f) {                                 // EG<kind><size><load><mount>[E]<n>R<length>...
    size_check(f);
    let b = block_of(f);
    rail_mount_check(f.rm);
    let stainless = stainless_check(f, f.load);
    rail_checks(f, stainless);
    holes(f.length, table("rails", f.size));
    if f.n < 1 {
        refuse("invalid", "a set has at least one block (the digit before R is the number of blocks per rail)");
    }
    fit_check(f, b);
    options_check(f);
    let row = `EG${f.kind}-${f.load}${f.mount}-${f.size}`;
    let len = `${g(f.length)} mm`;
    #{ configuration: row, parameters: #{ length: len, blocks: `${f.n}` } }
}

fn resolve_block(f) {                               // a block alone
    if ("preload" in f && f.preload == "ZB") || ("prec" in f && (f.prec == "SP" || f.prec == "UP")) { block_generic(f); }
    size_check(f);
    block_of(f);
    stainless_check(f, f.load);
    options_check(f);
    let row = `EG${f.kind}-${f.load}${f.mount}-${f.size}-block`;
    #{ configuration: row, parameters: #{} }
}

fn resolve_rail(f) {                                // EGR<size>R<length>...
    rail_mount_check(f.rm);
    size_check(f);
    let stainless = stainless_check(f, ());
    rail_checks(f, stainless);
    holes(f.length, table("rails", f.size));
    options_check(f);
    let len = `${g(f.length)} mm`;
    #{ configuration: `EGR-${f.size}`, parameters: #{ length: len } }
}

fn resolve(f) {
    if "n" in f { resolve_set(f) } else if "kind" in f { resolve_block(f) } else { resolve_rail(f) }
}

fn describe(f) {
    let rail = table("rails", f.size);
    if "kind" in f && !("length" in f) { return `EG${f.kind}${f.size}${f.load}${f.mount} block`; }
    let h = holes(f.length, rail);
    let blocks = if "n" in f { `; ${f.n} EG${f.kind}${f.size}${f.load}${f.mount} block(s)` } else { "" };
    `EGR${f.size} rail of ${g(f.length)} mm: ${h.n} holes at pitch ${g(rail.P)} mm, end distance ${g(h.e)} mm${blocks}`
}
