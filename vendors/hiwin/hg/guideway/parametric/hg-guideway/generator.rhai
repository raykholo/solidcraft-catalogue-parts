// HIWIN HG guideway: fields from the ordering-code template -> configuration row + parameter overrides.
// Plain Rhai with the registered table(name, key[, column]) and refuse(kind, message), nothing else.
// Three products, three templates: a set (rail with blocks), a rail alone (HGR) and a block alone. The rail is mounted from the top (R,
// counterbored) or from the bottom (T, tapped): that is part of the configuration row's name. Every refusal below is the Python
// generator's message (src/catalogue.py), in the order the Python generator checks.

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

fn size_check(f) {
    if table("rails", f.size) == () {
        refuse("invalid", `HG size ${f.size}: catalogue sizes are 15, 20, 25, 30, 35, 45, 55, 65`);
    }
}

// stainless steel (M): HG15C, HG20C, HG25C. `load` is () for a rail alone.
fn stainless_check(f, load) {
    if !("mat" in f) { return false; }
    let ok = param("stainless_sizes").to_string().split("|");
    if !ok.contains(f.size) || (load != () && load != "C") {
        refuse("invalid", "stainless steel (M) exists for HG15C, HG20C and HG25C only (model number note 5, p.23)");
    }
    true
}

fn rail_checks(f, stainless) {
    size_check(f);
    let lim = if stainless { param("max_len_stainless") } else { param("max_len") };
    if f.length > lim.to_float() {
        let why = if stainless { " for stainless HGR15/20/25 (Table 2-1-27 note 4)" } else { "" };
        refuse("invalid", `rail length ${g(f.length)} mm above the maximum ${g(lim)} mm${why}`);
    }
    let r = table("rails", f.size);
    let two_es = 2.0 * r.Es.to_float();
    if f.length < two_es {
        refuse("invalid", `rail length ${g(f.length)} mm below 2 x Es = ${g(two_es)} mm`);
    }
}

// L = (n-1)P + 2E (Eq. 2.1, p.37): the most holes with Es <= E <= P/2
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
        refuse("invalid", `rail length ${gl} leaves end distance ${e2} mm, above P/2 = ${half} mm (unstable rail end, p.37)`);
    }
    #{ n: n, e: e }
}

// the block of the row
fn block_of(f) {
    if f.kind == "L" {
        refuse("not_modelled", "HGL (low square type) is valid HIWIN grammar; its table (2) is not drawn here");
    }
    if f.kind == "H" && f.mount != "A" {
        refuse("invalid", `HGH is mounted from the top only: HGH${f.size}${f.load}A (the catalogue lists HGH-CA / HGH-HA)`);
    }
    let b = table("blocks", `HG${f.kind}-${f.load}${f.mount}-${f.size}`);
    if b == () {
        refuse("invalid", `HG${f.kind}${f.size}${f.load}${f.mount} is not in the catalogue table (HG15 has the heavy load C block only)`);
    }
    b
}

// what the Python generator says for a block code its regular expression does not accept (preload ZB, accuracy SP / UP on a block alone)
fn block_generic(f) {
    let code = `HG${f.kind}${f.size}${f.load}${f.mount}`;
    if f.eblock { code += "E"; }
    if "preload" in f { code += f.preload; }
    if "prec" in f { code += f.prec; }
    if "mat" in f { code += "M"; }
    if "opt" in f { code += "+" + f.opt; }
    refuse("invalid", `'${code}': expected a set HG<H|W><size><C|H><A|B|C><n>R<length>[Z0|ZA|ZB][C|H|P], e.g. HGH20CA2R1000ZAH, a rail HGR<size>R<length>, e.g. HGR25R1600, or a block HGW25CC`);
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

fn resolve_set(f) {                                 // HG<kind><size><load><mount>[E]<n><R|T><length>...
    size_check(f);
    let b = block_of(f);
    let stainless = stainless_check(f, f.load);
    rail_checks(f, stainless);
    holes(f.length, table("rails", f.size));
    if f.n < 1 {
        refuse("invalid", "a set has at least one block (the digit before R is the number of blocks per rail)");
    }
    fit_check(f, b);
    let row = `HG${f.kind}-${f.load}${f.mount}-${f.size}-${f.rm}`;
    let len = `${g(f.length)} mm`;
    #{ configuration: row, parameters: #{ length: len, blocks: `${f.n}` } }
}

fn resolve_block(f) {                               // a block alone
    if ("preload" in f && f.preload == "ZB") || ("prec" in f && (f.prec == "SP" || f.prec == "UP")) { block_generic(f); }
    size_check(f);
    block_of(f);
    stainless_check(f, f.load);
    let row = `HG${f.kind}-${f.load}${f.mount}-${f.size}-block`;
    #{ configuration: row, parameters: #{} }
}

fn resolve_rail(f) {                                // HGR<size><R|T><length>...
    let stainless = stainless_check(f, ());
    rail_checks(f, stainless);
    holes(f.length, table("rails", f.size));
    let len = `${g(f.length)} mm`;
    #{ configuration: `HGR-${f.size}-${f.rm}`, parameters: #{ length: len } }
}

fn resolve(f) {
    if "n" in f { resolve_set(f) } else if "kind" in f { resolve_block(f) } else { resolve_rail(f) }
}

fn describe(f) {
    let rail = table("rails", f.size);
    if "kind" in f && !("length" in f) { return `HG${f.kind}${f.size}${f.load}${f.mount} block`; }
    let h = holes(f.length, rail);
    let blocks = if "n" in f { `; ${f.n} HG${f.kind}${f.size}${f.load}${f.mount} block(s)` } else { "" };
    `HGR${f.size}${f.rm} rail of ${g(f.length)} mm: ${h.n} holes at pitch ${g(rail.P)} mm, end distance ${g(h.e)} mm${blocks}`
}
