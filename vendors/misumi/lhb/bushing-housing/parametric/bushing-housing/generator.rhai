// MISUMI Economy linear bushing housing units, wide blocks (E-LBHN single / medium, E-LBHNW double / medium long / long, -P dowel holes):
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

fn shape_error(raw) {
    let shown = pyrepr(raw);
    refuse("invalid", `${shown}: expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L`);
}

// ---- which housing: the series, with the Python refusals --------------------------------------------------------
fn single_series(dr, ln) {        // E-LBHN: single (no suffix) or medium (D)
    if ln == "L" { refuse("invalid", "E-LBHN has Single (no suffix) and Medium (D) only; the Long length L belongs to E-LBHNW (p.485)"); }
    let r = table("single", dr);
    if r == () { let o = offered("single"); refuse("invalid", `E-LBHN${dr}: the wide single housing is offered for dr ${o} (p.485)`); }
    if ln == "D" {
        if (r.L_medium == () || r.L_medium == "") {
            let o = offered("medium");
            refuse("invalid", `E-LBHN${dr}D: the medium housing is offered for dr ${o} only; dr 13, 35, 40 and 50 are single only (p.485)`);
        }
        return "medium";
    }
    "single"
}
fn double_series(dr, ln) {        // E-LBHNW: double (no suffix), medium long (D) or long (L)
    let r = table("double", dr);
    if r == () { let o = offered("double"); refuse("invalid", `E-LBHNW${dr}: the wide double housing is offered for dr ${o} (p.487)`); }
    if ln == "D" {
        if (r.L_medlong == () || r.L_medlong == "") { let o = offered("medlong"); refuse("invalid", `E-LBHNW${dr}D: the medium long housing is offered for dr ${o} (p.487)`); }
        return "medlong";
    }
    if ln == "L" {
        if (r.L_long == () || r.L_long == "") { let o = offered("long"); refuse("invalid", `E-LBHNW${dr}L: the long housing is offered for dr ${o} (p.487)`); }
        return "long";
    }
    "double"
}
fn dims(series, r) {              // the columns of this series: L, L1 and the dr tolerance (upper, lower)
    if series == "single" { return #{ L: r.L_single, L1: r.L1_single, tu: r.dr_tol_single_upper, tl: r.dr_tol_single_lower }; }
    if series == "medium" { return #{ L: r.L_medium, L1: r.L1_medium, tu: r.dr_tol_medium_upper, tl: r.dr_tol_medium_lower }; }
    if series == "double" { return #{ L: r.L_double, L1: r.L1_double, tu: 0, tl: r.dr_tol_double }; }
    if series == "medlong" { return #{ L: r.L_medlong, L1: r.L1_medlong, tu: 0, tl: r.dr_tol_medlong }; }
    #{ L: r.L_long, L1: r.L1_long, tu: 0, tl: r.dr_tol_long }
}
fn label(series) {
    if series == "medlong" { "medium long" } else { series }
}

fn describe_part(code, series, dr, r, dowel) {
    let d = dims(series, r);
    let n = if series == "long" { 6 } else { 4 };
    let s = `MISUMI Economy linear bushing housing unit ${code}, wide block, ${label(series)}, shaft diameter dr ${dr} mm `;
    let t0 = sgn3(d.tu); let t1 = sgn3(d.tl); let gl = g(d.L); let gt = g(r.L_tol);
    s += `(${t0}/${t1} mm as printed, bore drawn empty at nominal), L ${gl} mm (+-${gt}), `;
    let gl1 = g(d.L1); let gw = g(r.W); let gh = g(r.H); let gb = g(r.h); let gbt = g(r.h_tol);
    s += `L1 ${gl1} mm, W ${gw} mm, H ${gh} mm, h ${gb} mm (+-${gbt}), ${n} mounting holes `;
    let gd = g(r.d); let gtl = g(r.l);
    s += `${r.M} (pilot d ${gd} mm, thread depth ${gtl} mm)`;
    if dowel {
        let gp = g(r.P); let g2 = g(r.l2);
        s += `, 2 dowel holes P ${gp} mm x ${g2} deep (positions (appearance, approximate))`;
    }
    s + ". Housing aluminium alloy, clear anodized. The built-in bushing, grease nipple hole and edge chamfers are not drawn. Generated from the published catalogue dimensions."
}

// ---- resolve: fields -> the configuration row and the parameter values ---------------------------------------------
fn resolve(fields) {
    if fields.raw != () { shape_error(fields.raw); }
    let double = fields.double;
    let typ = if double { "E-LBHNW" } else { "E-LBHN" };
    let dr = parse_int(fields.dr.to_string());
    let ln = if fields.length == () { "" } else { fields.length };
    let dowel = fields.dowel;
    let code = typ + fields.dr + ln;
    if dowel { code += "-P"; }
    let series = if double { double_series(dr, ln) } else { single_series(dr, ln) };
    let r = table(if double { "double" } else { "single" }, dr);
    if dowel && (r.P == () || r.P == "") {
        refuse("invalid", `${typ}${dr}: dr ${dr} has no dowel hole version, the dowel hole table starts at dr 8 (p.485 / p.487)`);
    }
    #{ configuration: `${series}-${dr}`, parameters: #{ dowel: if dowel { "1" } else { "0" } },
       properties: #{ part_number: code, description: describe_part(code, series, dr, r, dowel), material: "Aluminum alloy; clear anodized",
                      series: series, dr: dr, dowel: dowel, type: typ } }
}

// ---- the inverse: configuration row + parameters -> fields (for a bill of materials) -----------------------------------
fn fields(configuration, parameters) {
    let series = configuration.sub_string(0, configuration.index_of("-"));
    let dr = configuration.sub_string(configuration.index_of("-") + 1);
    let double = series == "double" || series == "medlong" || series == "long";
    let ln = if series == "medium" || series == "medlong" { "D" } else if series == "long" { "L" } else { () };
    #{ double: double, dr: parse_int(dr), length: ln, dowel: parameters.dowel == "1" }
}
