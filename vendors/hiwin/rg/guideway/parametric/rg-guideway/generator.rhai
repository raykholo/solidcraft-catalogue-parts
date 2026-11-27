// HIWIN RG roller guideway: fields from the ordering-code template -> configuration row + parameter overrides.
// Plain Rhai with the registered table(name, key[, column]) and refuse(kind, message), nothing else.
// Three products, three templates: a set (rail with blocks), a rail alone (RGR) and a block alone. A dust-protection code (+ZZ, +DD, +KK)
// replaces the block length L (Table 2-9-22): the answer carries it as the parameter L. Every refusal below is the Python generator's
// message (src/catalogue.py), in the order the Python generator checks.

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
fn dust_code(f) {
    if !("opt" in f) { return ""; }
    let run = "";
    for ch in f.opt.to_upper().chars() {
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
        refuse("invalid", `RG size ${f.size}: catalogue sizes are 15, 20, 25, 30, 35, 45, 55, 65`);
    }
}

fn rail_mount_check(rm) {
    if rm == "T" {
        refuse("not_modelled", "RGR rail mounted from the bottom (T) is valid HIWIN grammar, but the catalogue prints no tapped-hole dimensions for it (the rail columns on p.166-170 are the top-mounted R rail), so it is not drawn");
    }
}

fn rail_checks(f) {
    size_check(f);
    let lim = param("max_len");
    if f.length > lim.to_float() {
        refuse("invalid", `rail length ${g(f.length)} mm above the maximum ${g(lim)} mm (Table 2-9-29)`);
    }
    let lo = param("min_len");
    if f.length < lo.to_float() {
        refuse("invalid", `rail length ${g(f.length)} mm below the catalogue minimum ${g(lo)} mm (Table 2-9-2)`);
    }
}

fn precision_check(f, allowed, what) {
    if "prec" in f && !allowed.contains(f.prec) {
        let list = "";
        for v in allowed {
            if list != "" { list += ", "; }
            list += v;
        }
        refuse("invalid", `accuracy class ${f.prec} is not offered for ${what}: the RG series has ${list} there (model number, p.152-153)`);
    }
}

// L = (n-1)P + 2E (p.165): the most holes whose end distance E is the standard Es or lies within (smallest, P/2)
fn holes(length, rail) {
    let es = rail.Es.to_float();
    let p = rail.P.to_float();
    let lo = if es < p / 2.0 { es } else { p / 2.0 };
    let hi = p / 2.0;
    let n = ((length - 2.0 * lo + 0.000000001) / p).floor().to_int() + 1;
    let e = (length - (n - 1).to_float() * p) / 2.0;
    let gl = g(length);
    let e2 = two_decimals(e);
    if n < 2 || e < lo - 0.000000001 {
        refuse("invalid", `rail length ${gl} leaves end distance ${e2} mm, below the smallest end distance ${g(lo)} mm (p.165)`);
    }
    if (e - es).abs() > 0.000000001 && e > hi + 0.000000001 {
        let gh = g(hi);
        let ges = g(es);
        refuse("invalid", `rail length ${gl} leaves end distance ${e2} mm, above P/2 = ${gh} mm and not the standard Es = ${ges} mm (an unstable rail end, p.165)`);
    }
    #{ n: n, e: e }
}

// the block of the row, with the block length of a dust-protection code (Table 2-9-22)
fn block_of(f) {
    if f.kind == "L" || f.kind == "S" || f.kind == "F" {
        let what = if f.kind == "L" { "square, low" } else if f.kind == "S" { "square, ultra low" } else { "flange, ultra low" };
        refuse("not_modelled", `RG${f.kind} (${what}) is valid HIWIN grammar; its dimension table is not drawn here (RGH and RGW only)`);
    }
    if f.kind == "H" && f.mount != "A" {
        refuse("invalid", `RGH is mounted from the top only: RGH${f.size}${f.load}A (the catalogue lists RGH-CA / RGH-HA)`);
    }
    if f.kind == "W" && f.mount != "C" {
        refuse("invalid", `RGW has mounting code C (top or bottom): RGW${f.size}${f.load}C (the catalogue lists RGW-CC / RGW-HC)`);
    }
    let b = table("blocks", `RG${f.kind}-${f.load}${f.mount}-${f.size}`);
    if b == () {
        refuse("invalid", `RG${f.kind}${f.size}${f.load}${f.mount} is not in the catalogue table (no row for it: the RG15 tables list the heavy load C block only)`);
    }
    let dust = dust_code(f);
    if dust != "" {
        b.L = table("dust", `${f.size}${f.load}`, dust);
    }
    b
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

fn dust_parameters(f, b, params) {
    if dust_code(f) != "" { params.L = `${g(b.L)} mm`; }
    params
}

fn resolve_set(f) {                                 // RG<kind><size><load><mount>[E]<n>R<length>...
    size_check(f);
    let b = block_of(f);
    rail_mount_check(f.rm);
    rail_checks(f);
    precision_check(f, ["H", "P", "SP", "UP"], "a rail with blocks (non-interchangeable set)");
    holes(f.length, table("rails", f.size));
    if f.n < 1 {
        refuse("invalid", "a set has at least one block (the digit before R is the number of blocks per rail)");
    }
    fit_check(f, b);
    let row = `RG${f.kind}-${f.load}${f.mount}-${f.size}`;
    let len = `${g(f.length)} mm`;
    let nb = `${f.n}`;
    let ps = dust_parameters(f, b, #{ length: len, blocks: nb });
    #{ configuration: row, parameters: ps }
}

fn resolve_block(f) {                               // a block alone
    size_check(f);
    let b = block_of(f);
    if "preload" in f && f.preload == "ZB" {
        refuse("invalid", "the interchangeable block form has preload Z0 or ZA only (model number, p.152); ZB belongs to a set (non-interchangeable)");
    }
    precision_check(f, ["H", "P"], "an interchangeable block");
    let row = `RG${f.kind}-${f.load}${f.mount}-${f.size}-block`;
    #{ configuration: row, parameters: dust_parameters(f, b, #{}) }
}

fn resolve_rail(f) {                                // RGR<size>R<length>...
    rail_mount_check(f.rm);
    size_check(f);
    rail_checks(f);
    precision_check(f, ["H", "P"], "a rail ordered alone (interchangeable rail)");
    holes(f.length, table("rails", f.size));
    let len = `${g(f.length)} mm`;
    #{ configuration: `RGR-${f.size}`, parameters: #{ length: len } }
}

fn resolve(f) {
    if "n" in f { resolve_set(f) } else if "kind" in f { resolve_block(f) } else { resolve_rail(f) }
}

fn describe(f) {
    let rail = table("rails", f.size);
    if "kind" in f && !("length" in f) { return `RG${f.kind}${f.size}${f.load}${f.mount} block`; }
    let h = holes(f.length, rail);
    let blocks = if "n" in f { `; ${f.n} RG${f.kind}${f.size}${f.load}${f.mount} block(s)` } else { "" };
    `RGR${f.size} rail of ${g(f.length)} mm: ${h.n} holes at pitch ${g(rail.P)} mm, end distance ${g(h.e)} mm${blocks}`
}
