// MISUMI aluminium extrusions (HFS5 / HFS6 families): ordering-code logic as plain Rhai.
// Interface: docs/formats/generator.md (SolidCraft generator interface v2): resolve(fields) -> #{configuration, parameters} or refuse(kind, message).
// Everything numeric comes from tables/*.csv (generated from data/*.csv, each row cites its source id and page); this script only reads them.
// Written in small functions: the documented sandbox allows an expression depth of 16 inside a function.

// ---- helpers -------------------------------------------------------------------------------------
fn g(x) {                         // Python's {:g}
    let f = x.to_float();
    if f == f.floor() && f.abs() < 1000000000.0 { f.to_int().to_string() } else { f.to_string() }
}
fn join(a, sep) {
    let s = "";
    for i in 0..a.len() { if i > 0 { s += sep; } s += a[i]; }
    s
}
fn pylist(a) {                    // Python's repr of a list of strings
    let q = [];
    for s in a { q.push(`'${s}'`); }
    "[" + join(q, ", ") + "]"
}
fn strs(a) { let o = []; for x in a { o.push(x.to_string()); } o }
fn ints(a) { let o = []; for x in a { o.push(parse_int(x.to_string())); } o }
fn nonempty(a) { let o = []; for x in a { if x != "" { o.push(x); } } o }
fn lo_of(a) { let m = a[0]; for x in a { if x < m { m = x; } } m }
fn hi_of(a) { let m = a[0]; for x in a { if x > m { m = x; } } m }
fn sorted_list(a) { let b = a; b.sort(); b }
fn split_bar(s) { if s == () { [] } else { s.to_string().split("|") } }
fn num(x) { if type_of(x) == "string" { parse_float(x) } else { x.to_float() } }
fn side_name(side) { if side == "L" { "left" } else { "right" } }
fn mm(x) { g(x) + " mm" }
fn param(name) { table("params", name, "value") }
fn ch(a, i) { a.sub_string(i, 1) }

// ---- the type and profile -----------------------------------------------------------------------
fn check_type(fields) {           // -> series ("5" | "6"); refuses
    let typ = fields.part_type.to_upper();
    let last = ch(typ, typ.len() - 1);
    if last != "5" && last != "6" {
        let shown = code_template(fields);
        refuse("invalid", `'${shown}': expected [K]<type>5|6-<profile>-<length>[-<alteration>...], e.g. HFS5-2040-800-LTP-RTP`);
    }
    let types_here = sorted_list(split_bar(param("types" + last)));
    let other = split_bar(param("other_types"));
    if typ in other {
        let tl = pylist(types_here);
        refuse("not_modelled", `${typ}: valid ${last} series type, but only ${tl} are drawn`);
    }
    if !(typ in types_here) {
        let known = pylist(sorted_list(split_bar(param("types5")) + split_bar(param("types6")) + other));
        refuse("invalid", `unknown ${last} series type '${typ}'; known: ${known}`);
    }
    last
}
fn check_profile(typ, prof, series) {
    let profs = sorted_list(split_bar(param("profiles" + series)));
    if !(prof in profs) {
        let pl = pylist(profs);
        refuse("invalid", `profile '${prof}' not available for ${typ} here; verified for the ${series} series: ${pl}`);
    }
    if typ == "HFSY5" && (prof == "2040" || prof == "4040") {
        refuse("invalid", `HFSY5 is listed for 2020 only (S1 p.530 type table has no HFSY5 for ${prof})`);
    }
}
fn check_length(fields) {         // -> length (float); refuses
    if fields.length == () { refuse("invalid", "a length is required: the last number before the alterations, in mm"); }
    let length = fields.length.to_float();
    let gl = g(length);
    if fields.fixed {
        let fl = ints(split_bar(param("fixed_lengths")));
        if !(length.to_int() in fl) || length != length.floor() {
            let fs = join(strs(fl), ", ");
            refuse("invalid", `fixed-length (K) extrusions come only in [${fs}] mm, not ${gl}`);
        }
        return length;
    }
    let gmin = g(num(param("l_min"))); let gmax = g(num(param("l_max")));
    if length < num(param("l_min")) || length > num(param("l_max")) { refuse("invalid", `length ${gl} mm outside ${gmin}-${gmax} mm`); }
    let step = num(param("l_step"));
    let q = length / step;
    if (q - q.round()).abs() > 0.000000001 { refuse("invalid", `length ${gl} mm is not a multiple of ${step} mm`); }
    length
}

// ---- the alterations --------------------------------------------------------------------------------
fn is_wrench(a) {
    a.len() == 3 && (ch(a, 0) in ["L", "R"]) && (ch(a, 1) in ["C", "W", "E"]) && (ch(a, 2) in ["H", "V", "P"])
}
fn parse_alts(alts, length, fixed) {     // -> #{tap_l, tap_r, wrench, xdia, tolerance, notes, seen}
    if alts.len() > 0 && fixed {
        refuse("invalid", "alterations apply to configurable-length extrusions only (fixed-length K types have none)");
    }
    let r = #{ tap_l: false, tap_r: false, wrench: #{}, xdia: (), tolerance: 0.5, notes: [], seen: [] };
    for a in alts {
        if a in r.seen { refuse("invalid", `alteration ${a} given twice`); }
        r.seen.push(a);
        r = parse_one(a, r, length);
    }
    r
}
fn parse_one(a, r, length) {              // early returns keep the if-chain flat (sandbox: expression depth 16 per function)
    if a == "LTP" || a == "RTP" || a == "TPW" { return tap(a, r); }
    if a == "LHP" || a == "RHP" || a == "HPW" { refuse("not_modelled", `${a}: heli-coil end tapping: parsed, not modelled`); }
    if is_wrench(a) { return wrench_option(a, r); }
    if a.len() == 2 && ch(a, 0) == "X" && (ch(a, 1) in ["5", "8"]) { r.xdia = parse_float(ch(a, 1)); return r; }
    if a == "FL" || a == "FR" { return r; }
    if a == "SC" { return high_precision(r, length); }
    if a == "CW" { refuse("not_modelled", "CW: End face C chamfer (thread chamfer C0.2-0.3): not modelled"); }
    refuse("invalid", `unknown or unsupported alteration '${a}'`);
}
fn tap(a, r) {
    let wl = a == "LTP" || a == "TPW"; let wr = a == "RTP" || a == "TPW";
    if (wl && r.tap_l) || (wr && r.tap_r) { refuse("invalid", `end tapping given twice for the same end (${a})`); }
    if wl { r.tap_l = true; }
    if wr { r.tap_r = true; }
    r
}
fn wrench_option(a, r) {
    let side = ch(a, 0); let rows = ch(a, 1); let orient = ch(a, 2);
    if orient == "P" { refuse("not_modelled", `${a}: crisscross (P) layout is ambiguous in the catalogue text; use H or V`); }
    if side in r.wrench { let sn = side_name(side); refuse("invalid", `two wrench-hole options for the ${sn} end`); }
    r.wrench[side] = #{ rows: if rows == "C" { 1 } else if rows == "W" { 2 } else { 3 }, dir: if orient == "H" { 0 } else { 1 }, shift: 0.0,
                        axis_name: if orient == "H" { "horizontal" } else { "vertical" } };
    r
}
fn high_precision(r, length) {
    if length > 1500.0 { refuse("invalid", "SC (high precision cut) applies to L <= 1500 mm only"); }
    r.tolerance = 0.2;
    r.notes.push("SC: tolerance L+-0.2 (no geometry change)");
    r
}
fn wrench_diameter(r, wrench_d) {        // 5 series: one value; 6 series: -X5 / -X8 must be given
    if r.wrench.len() == 0 {
        if r.xdia != () { refuse("invalid", "X5/X8 sets the wrench hole diameter; there is no wrench hole alteration in this code"); }
        return 0.0;
    }
    if wrench_d.len() == 1 {
        if r.xdia != () { refuse("invalid", "X5/X8 (wrench hole diameter) applies to the 6 series; the 5 series hole is d7.35"); }
        return num(wrench_d[0]);
    }
    if r.xdia == () { refuse("invalid", "the 6 series wrench hole diameter is selectable: add -X5 or -X8 (S3 p.759 footnote)"); }
    r.xdia
}
fn shifts(r) {                           // FL / FR move that end's holes 3 mm toward the end (S3 p.760)
    for a in ["FL", "FR"] {
        if a in r.seen { r = shift_one(a, r); }
    }
    r
}
fn shift_one(a, r) {
    let side = ch(a, 1);
    if !(side in r.wrench) { let sn = side_name(side); refuse("invalid", `${a} shifts a wrench hole on the ${sn} end, but there is none`); }
    r.wrench[side].shift = 3.0;
    r.notes.push(`${a}: the p.760 table lists 6 and 8 series only; availability on the 5 series is unverified`);
    r
}
fn hole_positions(w, side, wh, length) {
    let h = wh[0] - w.shift;
    let offs = [h, h + wh[1], h + wh[1] + wh[2]];
    let xs = [];
    for i in 0..w.rows {
        let x = offs[i];
        if side == "R" { x = length - x; }
        xs.push(x);
    }
    xs
}
fn check_fit(r, wh, d, length) {
    for side in r.wrench.keys() {
        let xs = hole_positions(r.wrench[side], side, wh, length);
        let lo = lo_of(xs); let hi = hi_of(xs);
        if lo - d / 2.0 < 0.0 || hi + d / 2.0 > length {
            let xl = join(strs(xs), ", "); let gl = g(length);
            refuse("invalid", `wrench holes at [${xl}] do not fit in a ${gl} mm length`);
        }
    }
}
fn describe_part(ptype, prof, surface, material, length, r, d, tap_thread, tap_depth) {
    let sl = surface.to_lower(); let gl = g(length);
    let desc = `MISUMI aluminium extrusion ${ptype}-${prof} ${sl}, ${material}, L=${gl} mm`;
    if r.tap_l || r.tap_r {
        let which = if r.tap_l && r.tap_r { "both ends" } else if r.tap_l { "left end" } else { "right end" };
        let gd = g(tap_depth);
        desc += `, end tapped ${tap_thread} depth ${gd} (${which})`;
    }
    for side in ["L", "R"] {
        if side in r.wrench {
            let w = r.wrench[side]; let sn = side_name(side); let gdd = g(d);
            desc += `, ${sn} wrench access holes x${w.rows} ${w.axis_name} d${gdd}`;
        }
    }
    desc + ". Generated from the published catalogue dimensions."
}

// ---- resolve: fields -> the configuration row and the parameter values -----------------------------------------
fn resolve(fields) {
    let typ = fields.part_type.to_upper();
    let prof = fields.profile;
    let series = check_type(fields);
    check_profile(typ, prof, series);
    let length = check_length(fields);
    // material and surface: a (type, profile) row where the catalogue differs by profile (NFS), else the type's row
    let material = table("types", `${typ}:${prof}`, "material");
    let surface = table("types", `${typ}:${prof}`, "surface");
    if material == () { material = table("types", typ, "material"); surface = table("types", typ, "surface"); }
    let tap_thread = table("sections", prof, "tap_thread");
    let tap_depth = num(table("sections", prof, "tap_depth"));
    let wrench_d = split_bar(table("sections", prof, "wrench_d"));
    let wh = [num(table("sections", prof, "wrench_h")), num(table("sections", prof, "wrench_j")), num(table("sections", prof, "wrench_k"))];

    let alts = [];
    if fields.alts != () { let raw_alts = fields.alts.to_upper(); alts = nonempty(raw_alts.split("-")); }
    let r = parse_alts(alts, length, fields.fixed);
    let d = wrench_diameter(r, wrench_d);
    r = shifts(r);
    if (r.tap_l || r.tap_r) && 2.0 * tap_depth > length { refuse("invalid", "tapped holes overlap"); }
    check_fit(r, wh, d, length);

    let params = make_parameters(typ, prof, length, fields.fixed, r, d);
    let ptype = (if fields.fixed { "K" } else { "" }) + typ;
    let desc = describe_part(ptype, prof, surface, material, length, r, d, tap_thread, tap_depth);
    let pn = code_template(fields);
    #{ configuration: prof, parameters: params,
       properties: #{ part_number: pn, description: desc, material: material, surface: surface, tolerance: r.tolerance, notes: r.notes, type_name: ptype } }
}
fn end_values(r, side) {
    if side in r.wrench { return r.wrench[side]; }
    #{ rows: 0, dir: 0, shift: 0.0 }
}
fn make_parameters(typ, prof, length, fixed, r, d) {    // the values the configuration row needs beyond what the row holds
    let wl = end_values(r, "L"); let wr = end_values(r, "R");
    let p = #{ part_type: typ, profile: prof, length: mm(length), fixed: if fixed { "1" } else { "0" } };
    p.tap_l = if r.tap_l { "1" } else { "0" };
    p.tap_r = if r.tap_r { "1" } else { "0" };
    p.wl_rows = wl.rows.to_string(); p.wl_dir = wl.dir.to_string(); p.wl_shift = mm(wl.shift);
    p.wr_rows = wr.rows.to_string(); p.wr_dir = wr.dir.to_string(); p.wr_shift = mm(wr.shift);
    if r.wrench.len() > 0 { p.wh_d = mm(d); }
    p
}

// parameters -> fields (generator.code, bill of materials): canonical order of the alterations
fn wrench_letters(parameters, s) {
    let p = "wl"; if s == "R" { p = "wr"; }
    let rows = parse_int(parameters[p + "_rows"]);
    if rows == 0 { return ""; }
    let n = "E"; if rows == 1 { n = "C"; } if rows == 2 { n = "W"; }
    let o = "H"; if parameters[p + "_dir"] != "0" { o = "V"; }
    s + n + o
}
fn fields(configuration, parameters) {
    let alts = [];
    let tl = parameters.tap_l == "1"; let tr = parameters.tap_r == "1";
    if tl && tr { alts.push("TPW"); }
    if tl && !tr { alts.push("LTP"); }
    if tr && !tl { alts.push("RTP"); }
    for s in ["L", "R"] { let w = wrench_letters(parameters, s); if w != "" { alts.push(w); } }
    if "wh_d" in parameters && configuration == "3030" { let dd = parse_float(parameters.wh_d.split(" ")[0]); alts.push("X" + g(dd)); }
    if parameters.wl_shift != "0 mm" { alts.push("FL"); }
    if parameters.wr_shift != "0 mm" { alts.push("FR"); }
    let f = #{ fixed: parameters.fixed == "1", part_type: parameters.part_type, profile: configuration, length: parse_float(parameters.length.split(" ")[0]), alts: () };
    if alts.len() > 0 { f.alts = join(alts, "-"); }
    f
}
