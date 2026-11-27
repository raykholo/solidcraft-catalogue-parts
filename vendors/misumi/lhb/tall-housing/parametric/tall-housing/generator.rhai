// MISUMI Economy linear bushing housing units, tall blocks (E-LBHS single / medium / medium long / long, E-LBHSW double, -P dowel holes):
// ordering-code logic as plain Rhai. Interface: docs/formats/generator.md (SolidCraft generator interface v2):
// resolve(fields) -> #{configuration, parameters, properties} or refuse(kind, message).
// Every number comes from tables/*.csv (generated from data/*.csv, each row cites its source id and page); this script only reads them.
// Small functions: the documented sandbox allows an expression depth of 16 inside a function.

fn g(x) {                         // Python's {:g}
    let f = x.to_float();
    if f == f.floor() && f.abs() < 1000000000.0 { f.to_int().to_string() } else { f.to_string() }
}
fn sgn3(x) {                      // Python's {:+.3f}
    let f = x.to_float();
    let n = (f.abs() * 1000.0).round().to_int();
    let fp = (n % 1000).to_string();
    while fp.len() < 3 { fp = "0" + fp; }
    let sign = if f < 0.0 { "-" } else { "+" };
    sign + (n / 1000).to_string() + "." + fp
}
fn join(a, sep) {
    let s = "";
    for i in 0..a.len() { if i > 0 { s += sep; } s += a[i]; }
    s
}
fn strs(a) { let o = []; for x in a { o.push(x.to_string()); } o }
fn ints(a) { let o = []; for x in a { o.push(parse_int(x.to_string())); } o }
fn split_bar(s) { s.to_string().split("|") }
fn pyrepr(s) { if s.contains("'") && !s.contains("\"") { "\"" + s + "\"" } else { "'" + s + "'" } }
fn pylist(a) { "[" + join(strs(a), ", ") + "]" }       // Python's repr of a list of ints
fn offered(series) { pylist(ints(split_bar(table("params", "drs_" + series, "value")))) }
fn label(series) { if series == "medlong" { "medium long" } else { series } }

fn shape_error(raw) {
    let shown = pyrepr(raw);
    refuse("invalid", `${shown}: expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P`);
}
fn series_of(fields, ln) {
    if fields.double {
        if ln != "" { let shown = pyrepr(code_template(fields)); refuse("invalid", `${shown}: the double housing E-LBHSW has no length suffix (p.489)`); }
        return "double";
    }
    if ln == "D" { "medium" } else if ln == "S" { "medlong" } else if ln == "L" { "long" } else { "single" }
}
fn what_is(series) {
    if series == "single" { return "the tall single housing E-LBHS (p.488)"; }
    if series == "double" { return "the tall double housing E-LBHSW (p.489)"; }
    if series == "medium" { return "the medium housing E-LBHS..D (p.490)"; }
    if series == "medlong" { return "the medium long housing E-LBHS..S (p.490)"; }
    "the long housing E-LBHS..L (p.490)"
}
fn dowel_start(series) {
    if series == "single" { "dr 8 and up (p.488)" } else if series == "double" { "dr 8 and up (p.489)" } else { "dr 16 and up (p.490)" }
}
fn check_dowel(code, series, dr, key) {      // -> the dowel table row; refuses
    if series == "medium" || series == "medlong" {
        let lb = label(series);
        refuse("invalid", `${code}: dowel holes are available on the long type only (p.490), not on the ${lb} housing`);
    }
    let dw = table("dowel", key);
    if dw == () {
        let lb = label(series); let lo = dowel_start(series);
        refuse("invalid", `${code}: no dowel hole version for dr ${dr}: the ${lb} housing has dowel holes for ${lo}`);
    }
    dw
}

fn describe_part(code, series, dr, d, dw) {
    let n2 = if series == "long" { 3 } else { 2 };
    let s = `MISUMI Economy linear bushing housing unit ${code}, tall block with dowel holes, ${label(series)}, shaft diameter dr ${dr} mm `;
    let t0 = sgn3(d.dr_tol_upper); let t1 = sgn3(d.dr_tol_lower); let gl = g(d.L); let gl1 = g(d.L1);
    s += `(${t0}/${t1} mm as printed, bore drawn empty at nominal), L ${gl} mm, L1 ${gl1} mm, `;
    let gl2 = g(d.L2); let gw = g(d.W); let gh = g(d.H); let gb = g(d.h);
    s += `L2 ${gl2} mm (+-0.5), W ${gw} mm, H ${gh} mm, h ${gb} mm (+-0.05), `;
    let e1 = g(d.M1_eff); let e2 = g(d.M2_eff);
    s += `2 x ${d.M1} (effective length ${e1} mm) and ${n2} x ${d.M2} (effective length ${e2} mm) tapped holes, `;
    let gd1 = g(d.d1); let gt = g(d.t);
    s += `counterbore ${gd1} x ${gt} mm`;
    if dw != () {
        let gp = g(dw.P); let g2 = g(dw.l2);
        s += `, 2 dowel holes P ${gp} mm x ${g2} deep (positions (appearance, approximate))`;
    }
    s + ". Housing aluminium alloy, clear anodized. The built-in bushing, grease nipple and edge chamfers are not drawn. Generated from the published catalogue dimensions."
}

// ---- resolve: fields -> the configuration row and the parameter values ---------------------------------------------
fn resolve(fields) {
    if fields.raw != () { shape_error(fields.raw); }
    let typ = if fields.double { "E-LBHSW" } else { "E-LBHS" };
    let dr = parse_int(fields.dr);
    let ln = if fields.length == () { "" } else { fields.length };
    let dowel = fields.dowel;
    let code = typ + fields.dr + ln;
    if dowel { code += "-P"; }
    let series = series_of(fields, ln);
    let key = `${series}-${dr}`;
    let d = table("blocks", key);
    if d == () { let o = offered(series); let w = what_is(series); refuse("invalid", `${code}: ${w} is offered for dr ${o} only`); }
    let dw = if dowel { check_dowel(code, series, dr, key) } else { () };
    #{ configuration: key, parameters: #{ dowel: if dowel { "1" } else { "0" } },
       properties: #{ part_number: code, description: describe_part(code, series, dr, d, dw), material: "Aluminum alloy; clear anodized",
                      series: series, dr: dr, dowel: dowel, type: typ } }
}

// ---- the inverse: configuration row + parameters -> fields (for a bill of materials) -----------------------------------
fn fields(configuration, parameters) {
    let series = configuration.sub_string(0, configuration.index_of("-"));
    let dr = configuration.sub_string(configuration.index_of("-") + 1);
    let ln = if series == "medium" { "D" } else if series == "medlong" { "S" } else if series == "long" { "L" } else { () };
    #{ double: series == "double", dr: dr, length: ln, dowel: parameters.dowel == "1" }
}
