// MISUMI Economy linear bushing housing units, center hole height optional (E-LBHG single, E-LBHGW double): ordering-code logic as plain Rhai.
// Interface: docs/formats/generator.md (SolidCraft generator interface v2): resolve(fields) -> #{configuration, parameters, properties} or refuse(kind, message).
// Every number comes from tables/*.csv (generated from data/*.csv, each row cites its source id and page); this script only reads them.
// Small functions: the documented sandbox allows an expression depth of 16 inside a function.

fn g(x) {                         // Python's {:g}
    let f = x.to_float();
    if f == f.floor() && f.abs() < 1000000000.0 { f.to_int().to_string() } else { f.to_string() }
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

fn shape_error(raw) {
    let shown = pyrepr(raw);
    refuse("invalid", `${shown}: expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40`);
}
fn check(typ, dr, hv) {          // -> the table row; refuses
    let row = table("housing_g", dr);
    if row == () {
        let offered = pylist(ints(split_bar(table("params", "drs", "value"))));
        refuse("invalid", `${typ}${dr}-${hv}: dr ${dr} is not a catalogue size; E-LBHG / E-LBHGW are offered for dr ${offered} (p.491)`);
    }
    let choices = ints(split_bar(row.H_choices));
    if !(hv in choices) {
        let cl = pylist(choices);
        refuse("invalid", `${typ}${dr}-${hv}: centre height H ${hv} is not offered for dr ${dr}; the choices are ${cl} (p.491)`);
    }
    row
}
fn describe_part(code, series, dr, hv, row, t, t1) {
    let h1 = g(hv.to_float() + row.H1_offset.to_float());
    let s = `MISUMI Economy linear bushing housing unit ${code}, centre hole height optional, ${series}, shaft diameter dr ${dr} mm `;
    s += `(bore drawn empty at nominal), centre height H ${hv} mm (+-0.05), total height H1 ${h1} mm (0/-0.5), `;
    let gl = g(row.L); let gt = g(t);
    s += `flange width L ${gl} mm (centre at L/2 +-0.05), length T ${gt} mm, `;
    let gs = g(row.S); let gw = g(row.W); let gd = g(row.d);
    s += `flange thickness S ${gs} mm, body width W ${gw} mm, 4 mounting holes d ${gd} mm `;
    let gl1 = g(row.L1); let gt1 = g(t1); let gc = g(row.C1);
    s += `on L1 ${gl1} x T1 ${gt1} mm. Housing aluminium alloy, clear anodized. The built-in bushing and edge chamfers are not drawn; the `;
    s += `upper corner chamfers C1 ${gc} mm are (appearance, approximate). Generated from the published catalogue dimensions.`;
    s
}

// ---- resolve: fields -> the configuration row and the parameter values ---------------------------------------------
fn resolve(fields) {
    if fields.raw != () { shape_error(fields.raw); }
    let double = fields.double;
    let typ = if double { "E-LBHGW" } else { "E-LBHG" };
    let dr = parse_int(fields.dr.to_string());
    let hv = parse_int(fields.h.to_string());
    let row = check(typ, dr, hv);
    let code = `${typ}${dr}-${hv}`;
    let series = if double { "double" } else { "single" };
    let t = if double { row.T_double } else { row.T_single };
    let t1 = if double { row.T1_double } else { row.T1_single };
    let cfg = (if double { "GW-" } else { "G-" }) + dr;
    #{ configuration: cfg, parameters: #{ hc: `${hv} mm` },
       properties: #{ part_number: code, description: describe_part(code, series, dr, hv, row, t, t1), material: "Aluminum alloy; clear anodized",
                      series: series, dr: dr, h: hv, type: typ } }
}

// ---- the inverse: configuration row + parameters -> fields (for a bill of materials) -----------------------------------
fn fields(configuration, parameters) {
    let double = configuration.starts_with("GW-");
    let dr = configuration.sub_string(configuration.index_of("-") + 1);
    let hv = parse_int(parameters.hc.split(" ")[0]);
    #{ double: double, dr: parse_int(dr), h: hv }
}
