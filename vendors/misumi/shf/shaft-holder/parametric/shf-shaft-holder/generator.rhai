// MISUMI Economy shaft supports (E-SHST.., E-SHWT.., E-SHSTBN/MN.., C-SHA): ordering-code logic as plain Rhai.
// Interface: docs/formats/generator.md (SolidCraft generator interface v2): resolve(fields) -> #{configuration, parameters, properties} or refuse(kind, message).
// Every number comes from tables/*.csv (generated from data/*.csv, each row cites its source id and page); this script only reads them.
// Written in small functions: the documented sandbox allows an expression depth of 16 inside a function.

fn g(x) {                         // Python's {:g}
    let f = x.to_float();
    if f == f.floor() && f.abs() < 1000000000.0 { f.to_int().to_string() } else { f.to_string() }
}
fn join(a, sep) {
    let s = "";
    for i in 0..a.len() { if i > 0 { s += sep; } s += a[i]; }
    s
}
fn bar(s) { if s == () || s == "" { [] } else { s.to_string().split("|") } }
fn ints(s) { let o = []; for x in bar(s) { o.push(parse_int(x)); } o }
fn pylist(a) { let q = []; for x in a { q.push(x.to_string()); } "[" + join(q, ", ") + "]" }
fn has(a, x) { for y in a { if y == x { return true; } } false }
fn param(name) { table("params", name, "value") }
fn page_of(fam) { if fam == "thick" { 542 } else { 541 } }
fn plus3(x) {                     // Python's {:+.3f}
    let n = (x.to_float().abs() * 1000.0).round().to_int();
    let frac = n % 1000; let fs = frac.to_string();
    if frac < 10 { fs = "00" + fs; } else if frac < 100 { fs = "0" + fs; }
    let sign = "+"; if x < 0 { sign = "-"; }
    `${sign}${n / 1000}.${fs}`
}

fn shape_error(raw) {
    refuse("invalid", `'${raw}': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10)`);
}
fn check_csha(fields, d) {         // -> the csha row; refuses
    if fields.h != () { refuse("invalid", "C-SHA has one fixed height per hole diameter (no H in the part number): C-SHA10"); }
    let sizes = ints(param("sizes_csha"));
    if !has(sizes, d) {
        let sl = pylist(sizes);
        refuse("invalid", `C-SHA is listed for hole D ${sl}, not ${d} (p.540)`);
    }
    table("csha", `csha-${d}`)
}
fn check_height(typ, fam, d, h, row) {
    let page = page_of(fam);
    let all = ints(row.h_all);
    let al = pylist(all);
    if h == () { refuse("invalid", `${typ}${d} needs its height: ${typ}${d}-<H> with H from ${al} (p.${page})`); }
    if !has(all, h) { refuse("invalid", `height ${h} is not offered for ${typ}${d}: H = ${al} (p.${page})`); }
    if typ == "E-SHSTB" && d == 15 && h == 25 { refuse("invalid", "E-SHSTB15 is not available with H = 25 (p.541 note)"); }
    if typ == "E-SHSTMN" && row.mn_ok == 0 { refuse("invalid", `E-SHSTMN is not applicable to the * marked D${d} (p.542 note)`); }
    if typ == "E-SHSTA" || typ == "E-SHWTA" { check_alu(typ, d, h, row); }
}
fn alu_text(alu) {
    if alu.len() == 0 { return "no height"; }
    let ls = pylist(alu);
    `only H = ${ls}`
}
fn check_alu(typ, d, h, row) {
    let alu = ints(row.h_alu);
    if has(alu, h) { return; }
    let ok = alu_text(alu);
    refuse("invalid", `the aluminium type ${typ} is applicable only to * marked dimensions: for D${d} ${ok} (p.541)`);
}
fn check_family(typ, fam, d) {      // -> the dims row; refuses when (family, D) is not listed
    let row = table("dims", `${fam}-${d}`);
    if row == () {
        let sizes = ints(param("sizes_" + fam));
        let sl = pylist(sizes); let page = page_of(fam);
        refuse("invalid", `${typ} is not listed for D${d}: catalogue sizes are ${sl} (p.${page})`);
    }
    row
}

fn describe_csha(typ, d, row, t) {
    let r = row;
    `MISUMI Economy shaft support ${typ}${d}, hole D${d} tolerance H7, height H=${g(r.H)} mm, T=${g(r.T)}, hole pitch L1=${g(r.L1)}, M${r.M} clamp screw, ${t.material}, ${t.surface}. Overall H1, S, L, B, W are catalogue reference values (+-0.5 mm). Corners are not rounded here (not dimensioned); slit and screw hole are approximate.`
}
fn describe_other(typ, fam, d, h, row, t) {
    let kind = "T-shaped with slit";
    if fam == "side" { kind = "T-shaped with side slit"; }
    if fam == "thick" { kind = "thickened T-shaped with slit"; }
    let tol = table("tolerance", d);
    let tu = plus3(tol.upper); let tl = plus3(tol.lower);
    let ht = g(param("h_tol"));
    let depth = "through";
    if row.m_depth != 0 { depth = "depth " + row.m_depth.to_string(); }
    let s = `MISUMI Economy shaft support ${typ}${d}-${h} (${kind}), hole D${d} H8 (${tu}/${tl} mm), `;
    s += `height H=${h} mm (+-${ht}), ${t.material}, ${t.surface}, M${row.M} clamp screw (${depth}). `;
    s + `Slit width C=${g(row.C)}. Generated from the published catalogue dimensions.`
}

fn result(configuration, h, alu, typ, c, desc, t) {
    let p = #{ h: `${h} mm`, alu: alu, part_type: typ };
    let props = #{ part_number: c, description: desc, material: t.material, surface: t.surface, type_name: typ };
    #{ configuration: configuration, parameters: p, properties: props }
}
fn resolve_csha(fields, typ, d, t) {
    let row = check_csha(fields, d);
    let desc = describe_csha(typ, d, row, t);
    let c = code_template(fields);
    result(`csha-${d}`, row.H, "0", typ, c, desc, t)
}
fn resolve(fields) {
    if fields.raw != () { shape_error(fields.raw); }
    let typ = fields.pfx + "-SH" + fields.fam;
    let t = table("types", typ);
    if t == () { let c = code_template(fields); shape_error(c); }
    let d = fields.d;
    if t.family == "csha" { return resolve_csha(fields, typ, d, t); }
    let h = fields.h;
    let row = check_family(typ, t.family, d);
    check_height(typ, t.family, d, h, row);
    let desc = describe_other(typ, t.family, d, h, row, t);
    let alu = "0"; if typ == "E-SHSTA" || typ == "E-SHWTA" { alu = "1"; }
    let c = code_template(fields);
    result(`${t.family}-${d}`, h, alu, typ, c, desc, t)
}

// parameters -> fields (generator.code): the type is the text parameter part_type, D comes from the row, H from the parameter
fn fields(configuration, parameters) {
    let typ = parameters.part_type;
    let d = parse_int(configuration.split("-")[1]);
    let f = #{ pfx: typ.sub_string(0, 1), fam: typ.sub_string(4, typ.len() - 4), d: d, h: () };
    if typ != "C-SHA" { f.h = parse_int(parameters.h.split(" ")[0]); }
    f
}
