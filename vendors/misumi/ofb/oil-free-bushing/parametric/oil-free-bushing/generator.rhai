// MISUMI Economy oil free bushings (copper alloy C-MU.., special brass E-SH.., thrust E-MUGZ): ordering-code logic as plain Rhai.
// Interface: docs/formats/generator.md (SolidCraft generator interface v2): resolve(fields) -> #{configuration, parameters, properties} or refuse(kind, message).
// Everything numeric comes from tables/*.csv (generated from data/*.csv, each row cites its source id and page); this script only reads them.
// The control flow and every message follow the Python generator's parse() word for word. Small functions: the sandbox allows an expression depth of 16.

// ---- helpers -------------------------------------------------------------------------------------
fn g(x) {                         // Python's {:g}
    let f = x.to_float();
    if f == f.floor() && f.abs() < 1000000000.0 { f.to_int().to_string() } else { f.to_string() }
}
fn cat(a) { let s = ""; for x in a { s += x.to_string(); } s }
fn join(a, sep) {
    let s = "";
    for i in 0..a.len() { if i > 0 { s += sep; } s += a[i]; }
    s
}
fn pylist(a) { "[" + join(a, ", ") + "]" }                      // Python's repr of a list of ints
fn lst(name) { pylist(table("lists", name, "value").to_string().split("|")) }
fn sgn(x, nd) {                   // Python's {:+.<nd>f}
    let f = x.to_float();
    let m = if nd == 1 { 10 } else if nd == 2 { 100 } else { 1000 };
    let n = (f.abs() * m.to_float()).round().to_int();
    let fs = (n % m).to_string();
    while fs.len() < nd { fs = "0" + fs; }
    (if f < 0.0 { "-" } else { "+" }) + (n / m).to_string() + "." + fs
}
fn nul(x) { if x == "" { () } else { x } }
fn has(x) { x != () && x != "" && x != 0 }                      // Python truthiness of a table cell
fn page_of(tab) {                                                // the page of each table, as the Python generator prints it
    if tab == "copper_straight" || tab == "copper_shouldered" { "p.514" }
    else if tab == "copper_flanged" { "p.515" }
    else if tab == "thrust" { "p.516" }
    else if tab == "brass_straight" || tab == "brass_shouldered" { "p.519" }
    else { "p.520" }
}
fn param(key) { table("params", key, "value") }

// the L values a row offers: (n) is printed in brackets for the standard wall type only (straight, shouldered) or for the round and
// compact flanges only (flanged); n* for the thin wall type only
fn offered_lengths(tokens, thin, square) {
    let out = [];
    for t in tokens.to_string().split(" ") {
        if t == "" { continue; }
        if t.starts_with("(") { if thin || square { continue; } }
        else if t.ends_with("*") { if !thin { continue; } }
        let n = t;
        n.replace("(", ""); n.replace(")", ""); n.replace("*", "");
        out.push(parse_int(n));
    }
    out
}

// ---- the part (mirrors the Python Part) ----------------------------------------------------------
fn mkp(name, typ, t, d, L, D, r, page) {
    #{ code: name, typ: typ, family: t.family, wall: t.wall, material: t.material, d: d, L: L, D: D, bore_class: t.bore_class, od_class: t.od_class,
       bore_tol: [r.bore_tol_upper, r.bore_tol_lower], L_tol: [param("L_tol_upper"), param("L_tol_lower")], page: page, N: (), flange: () }
}
fn flanged_flange(r, fam) {
    let f = #{ H: r.H, T: r.T, t: r.t, d1: r.d1, d2: r.d2, pcd: nul(r.pcd), A: nul(r.A), F: nul(r.F) };
    if fam == "square" { f.W = r.W; }
    if fam == "compact" { f.width = r.D + param("compact_flat_extra"); }
    f
}
fn shouldered_part(b, r, thin) {
    b.N = if thin { r.N_thin } else { r.N };
    b.flange = if thin { #{ H: r.H_thin, t: r.t_thin } } else { #{ H: r.H, t: r.t } };
    b
}
fn part_of(name, typ, t, d, L, r, pg) {
    let thin = t.wall == "thin";
    let fam = t.family;
    let D = if thin { r.D_thin } else { r.D };
    let b = mkp(name, typ, t, d, L, D, r, pg);
    if fam == "straight" { b.N = if thin { r.N_thin } else { r.N }; return b; }
    if fam == "shouldered" { return shouldered_part(b, r, thin); }
    if fam == "thrust" { b.flange = #{ H: r.H, t: r.t }; return b; }
    b.flange = flanged_flange(r, fam);
    b
}

fn thin_msg(name, typ, d, tab, pg) {
    cat([name, ": the thin wall type ", typ, " is not offered for d ", d, "; thin wall d is ", lst(tab + "-thin"), " (", pg, ")"])
}
fn lengths_msg(name, typ, d, L, ok, why, pg) { cat([name, ": ", typ, d, " is offered in L ", pylist(ok), why, " (", pg, ")"]) }
fn why_not(fam, thin, L, tokens) {
    if fam == "square" && L in offered_lengths(tokens, false, false) {
        return cat([" (L ", L, " is printed in brackets: round and compact flanges only, not the square flange)"]);
    }
    let other = if thin { "standard" } else { "thin" };
    if (fam == "straight" || fam == "shouldered") && L in offered_lengths(tokens, !thin, false) {
        return cat([" (L ", L, " is printed for the ", other, " wall type only)"]);
    }
    ""
}

// ---- the description (the Python Part.description) -------------------------------------------------
fn hole_count(b) {
    if b.family == "square" { return 4; }
    if b.flange.F == () { 2 } else { 4 }
}
fn thrust_tol() {
    let v = sgn(param("thrust_t_tol_lower"), 2);
    cat([" (0/", v, " mm)"])
}
fn shoulder_text(b) {
    let f = b.flange;
    let d = cat([", flange H ", g(f.H), " mm x t ", g(f.t), " mm"]);
    if b.family == "thrust" { d += thrust_tol(); }
    d
}
fn flange_text(b) {
    let f = b.flange;
    if b.family == "shouldered" || b.family == "thrust" {
        return shoulder_text(b);
    }
    let n = hole_count(b);
    let tl = sgn(param("T_tol_lower"), 1);
    let d = cat([", ", b.family, " flange H ", g(f.H), " mm, T ", g(f.T), " mm (0/", tl, " mm)"]);
    if b.family == "square" { d += cat([", W ", g(f.W), " mm across flats"]); }
    if b.family == "compact" { d += cat([", ", g(f.width), " mm across two flats (D + 6)"]); }
    d += cat([", ", n, " counterbored holes d1 ", g(f.d1), " / d2 ", g(f.d2), " x ", g(f.t), " deep"]);
    if b.family != "compact" { return d + cat([" on P.C.D. ", g(f.pcd), " mm"]); }
    return d + compact_tail(f);
}
fn compact_tail(f) {
    let d = cat([", A ", g(f.A), " mm apart along H"]);
    if f.F != () { d += cat([" and F ", g(f.F), " mm across"]); }
    d
}
fn fam_text(b) {
    let m = #{ straight: "straight", shouldered: "shouldered", round: "round flanged", square: "square flanged", compact: "compact flanged", thrust: "thrust type" };
    m[b.family] + (if b.wall == "thin" { ", thin wall" } else { "" })
}
fn part_description(b) {
    let d = cat(["MISUMI Economy oil free bushing ", b.code, ", ", fam_text(b), ", I.D. d ", b.d, " mm "]);
    d += cat(["(", b.bore_class, " ", sgn(b.bore_tol[0], 3), "/", sgn(b.bore_tol[1], 3), " mm, drawn at nominal), O.D. D ", g(b.D), " mm "]);
    d += cat(["(", b.od_class, "), overall length L ", g(b.L), " mm (", sgn(b.L_tol[0], 1), "/", sgn(b.L_tol[1], 1), " mm)"]);
    if has(b.N) { d += cat([", wall N ", g(b.N), " mm"]); }
    if b.flange != () { d += flange_text(b); }
    d += cat([". ", b.material, ". Solid lubricant plugs, chamfers and rotation stopper screw ", table("appearance", "appx", "value"), ": not drawn."]);
    d + " Generated from the published catalogue dimensions."
}

// ---- entry points ---------------------------------------------------------------------------------
fn unmodelled(s) {                // the Python KNOWN_UNMODELLED pattern, as prefix tests
    if s.starts_with("E-MU") {
        let r = s.sub_string(4);
        if r.starts_with("SZ") || r.starts_with("KZ") || r.starts_with("CZ") || r.starts_with("CTZ") || r.starts_with("IZ") || r.starts_with("ITZ") { return true; }
    }
    if s.starts_with("C-MUIZ") { return true; }
    s.len() >= 7 && s.starts_with("E-M") && "JGX".contains(s.sub_string(3, 1)) && "BF".contains(s.sub_string(4, 1)) && s.sub_string(5, 1) == "Z"
}
fn refuse_raw(raw) {              // a code the strict template does not read: the Python parse()'s two shape errors
    if unmodelled(raw.to_upper()) {
        let m = cat(["'", raw, "': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the "]);
        m += "resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520)";
        refuse("invalid", m);
    }
    let m = cat(["'", raw, "': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, "]);
    m += "E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35";
    refuse("invalid", m);
}
fn no_row(name, typ, d, thin, tab, pg) {
    let key = if thin { tab + "-thin" } else { tab };
    let m = cat([name, ": ", typ, " is offered for I.D. d ", lst(key), " (", pg, ")"]);
    refuse("invalid", m);
}
fn bad_length(name, typ, d, L, thin, r, pg, fam) {
    let ok = offered_lengths(r.lengths, thin, fam == "square");
    let why = why_not(fam, thin, L, r.lengths);
    refuse("invalid", lengths_msg(name, typ, d, L, ok, why, pg));
}
fn row_of(name, typ, t, d, L, thin, tab, pg) {
    let r = table(tab, d);
    if r == () { no_row(name, typ, d, thin, tab, pg); }
    if thin && !has(r.D_thin) { refuse("invalid", thin_msg(name, typ, d, tab, pg)); }
    let ok = offered_lengths(r.lengths, thin, t.family == "square");
    if !(L in ok) { bad_length(name, typ, d, L, thin, r, pg, t.family); }
    r
}

fn resolve(fields) {
    if fields.raw != () { refuse_raw(fields.raw); }
    let typ = fields.otype;
    let d = parse_int(fields.d);
    let L = parse_int(fields.l);
    let t = table("types", typ);
    let tab = t.table;
    let pg = page_of(tab);
    let name = cat([typ, d, "-", L]);
    let r = row_of(name, typ, t, d, L, t.wall == "thin", tab, pg);
    let b = part_of(name, typ, t, d, L, r, pg);
    let props = #{ part_number: name, description: part_description(b), material: t.material, facts: b };
    #{ configuration: cat([typ, "-", d]), parameters: #{ blen: g(L) + " mm" }, properties: props }
}

// the inverse, for code printing (a bill of materials): configuration row + parameters -> the fields of the first template
fn fields(configuration, parameters) {
    let r = table("rows", configuration);
    #{ otype: r.type, d: r.dr.to_string(), l: parse_int(parameters.blen.split(" ")[0]).to_string() }
}
