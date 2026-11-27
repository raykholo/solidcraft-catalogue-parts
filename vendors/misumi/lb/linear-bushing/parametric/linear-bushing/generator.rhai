// MISUMI Economy linear bushings (E-LB, E-LBF/K/H and their Z, M, P, C types): ordering-code logic as plain Rhai.
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
fn lst(name) {                    // Python's repr of a sorted list of ints, from tables/lists.csv
    let v = table("lists", name, "value").to_string();
    "[" + join(v.split("|"), ", ") + "]"
}
fn pages(name) { table("lists", name, "value").to_string() }
fn sgn3(x) {                      // Python's {:+.3f}
    let f = x.to_float();
    let n = (f.abs() * 1000.0).round().to_int();
    let fs = (n % 1000).to_string();
    while fs.len() < 3 { fs = "0" + fs; }
    (if f < 0.0 { "-" } else { "+" }) + (n / 1000).to_string() + "." + fs
}
fn sg2(x) {                       // Python's {:+.2g} for the tolerances printed here (at most two significant digits)
    let f = x.to_float();
    (if f < 0.0 { "-" } else { "+" }) + g(f.abs())
}
fn nul(x) { if x == "" { () } else { x } }
fn cut1(s) { s.sub_string(0, s.len() - 1) }
fn first_tok(s) { s.to_string().split(" ")[0] }
fn is_digit(c) { "0123456789".contains(c) }

// ---- the part (mirrors the Python Bushing) -------------------------------------------------------
fn mkb(code, typ, fam, series, dr, D, D_tol, L, L_tol, dr_tol, cfg) {
    #{ code: code, typ: typ, family: fam, series: series, dr: dr, D: D, D_tol: D_tol, L: L, L_tol: L_tol, dr_tol: dr_tol,
       plated: false, double: false, counterbore: "-", layout: "standard", x0: 0, page: "", grooves: (), flange: (), cfg: cfg }
}
fn flange_of(r, fam) {
    let f = #{ H: r.H, T: r.T, d: r.d, d1: r.d1, t: r.t };
    if fam == "compact" {
        f.A = r.A; f.F = nul(r.F); f.width = r.width;
    } else {
        f.pcd = r.pcd;
        if fam == "square" { f.W = r.W; }
    }
    f
}
fn flange_plain(r) { #{ H: r.H, T: r.T, d: r.d, d1: r.d1, t: r.t, pcd: r.pcd, W: r.W } }

fn offered(head, lname, tail) { refuse("invalid", head + lst(lname) + tail); }

fn short_part(code, typ, dr) {
    let r = table("short", dr);
    let head = cat([typ, dr, "TUU: the short straight bushing is offered for dr "]);
    if r == () { offered(head, "short", " (p.464)"); }
    mkb(code, typ, "straight", "short", dr, r.D, r.D_tol, r.L, [0, r.L_tol], [0, r.dr_tol], cat(["short-", dr]))
}
fn medium_part(code, typ, dr, suf, plated) {
    let r = table("medium", dr);
    let head = cat([typ, dr, suf, ": the medium straight bushing is offered for dr "]);
    if r == () { offered(head, "medium", " (p.465)"); }
    let tol = if plated { r.D_tol_ni } else { r.D_tol };
    let b = mkb(code, typ, "straight", "medium", dr, r.D, tol, r.L, [0, r.L_tol], [0, r.dr_tol], cat(["medium-", dr]));
    b.plated = plated;
    b.grooves = #{ B: r.B, B_tol: r.B_tol, W: r.W, D1: r.D1 };
    b
}
fn parse_straight(code, typ, dr, suf, plated) {
    if suf == "UU" || suf == "LUU" {
        refuse("invalid", cat([typ, " is the straight bushing: its suffix is TUU (short), DUU or DMUU (medium), not ", suf]));
    }
    if suf == "TUU" { return short_part(code, typ, dr); }
    medium_part(code, typ, dr, suf, plated)
}

fn flanged_long_part(code, typ, dr, suf, fam, plated, cb) {
    let r = table("flanged_long", dr);
    let head = cat([typ, dr, suf, ": flanged bushings are offered for dr "]);
    if r == () { offered(head, "flanged_long", " (p.466 / p.468)"); }
    let stem = cut1(typ);
    if dr > 30 && typ.ends_with("Z") {
        let m = cat([typ, dr, ": the opposite-counterbore type ", typ, " is offered for dr 6-30; dr 35, 40, 50 only as ", stem, " and ", stem, "M (p.466 / p.468)"]);
        refuse("invalid", m);
    }
    let dbl = suf == "LUU";
    let tol = if plated { if dbl { r.D_tol_double_ni } else { r.D_tol_single_ni } } else { if dbl { r.D_tol_double } else { r.D_tol_single } };
    let len = if dbl { r.L_double } else { r.L_single };
    let b = mkb(code, typ, fam, "long", dr, r.D, tol, len, [r.L_tol, -r.L_tol], [r.dr_tol_upper, r.dr_tol_lower], cat(["flanged_long-", fam, "-", dr]));
    b.plated = plated; b.double = dbl; b.counterbore = cb; b.flange = flange_plain(r);
    b
}
fn flanged_medium_part(code, typ, dr, suf, fam, plated, cb) {
    let stem = cut1(typ);
    if typ.ends_with("Z") || typ.ends_with("M") {
        let m = cat([typ, ": the medium flanged bushing is ordered as ", stem, "<dr>DUU, or ", stem, "<dr>DMUU for electroless nickel plating (p.467 / p.469); the Z and M type letters belong to the UU / LUU bushings"]);
        refuse("invalid", m);
    }
    let r = table("flanged_medium", dr);
    let head = cat([typ, dr, suf, ": the medium flanged bushing is offered for dr "]);
    if r == () { offered(head, "flanged_medium", " (p.467 / p.469)"); }
    let tol = if plated { r.D_tol_ni } else { r.D_tol };
    let b = mkb(code, typ, fam, "medium", dr, r.D, tol, r.L, [r.L_tol, -r.L_tol], [0, r.dr_tol], cat(["flanged_medium-", fam, "-", dr]));
    b.plated = plated; b.counterbore = cb; b.flange = flange_plain(r);
    b
}
fn parse_flanged(code, typ, dr, suf, fam, plated, cb) {
    if suf == "TUU" {
        refuse("invalid", cat([typ, " has no short (TUU) version: flanged bushings end in UU / LUU (long) or DUU / DMUU (medium)"]));
    }
    if suf == "UU" || suf == "LUU" { return flanged_long_part(code, typ, dr, suf, fam, plated, cb); }
    flanged_medium_part(code, typ, dr, suf, fam, plated, cb)
}

fn compact_long_part(code, typ, dr, suf, plated, cb) {
    let name = cat([typ, dr, suf]);
    let r = table("compact_long", dr);
    if r == () { offered(name + ": compact flanged bushings are offered for dr ", "compact_long", " (p.470)"); }
    if typ == "E-LBHZ" && dr > 30 { refuse("invalid", name + ": the opposite-counterbore type E-LBHZ is offered for dr 6-30 (p.470)"); }
    if dr == 5 && typ != "E-LBH" { refuse("invalid", name + ": dr 5 is offered only as the plain E-LBH5UU (p.470)"); }
    let dbl = suf == "LUU";
    if dbl && r.L_double == "" { refuse("invalid", name + ": dr 5 is offered as a single bushing (UU) only (p.470)"); }
    let tol = if plated { if dbl { r.D_tol_double_ni } else { r.D_tol_single_ni } } else { if dbl { r.D_tol_double } else { r.D_tol_single } };
    let len = if dbl { r.L_double } else { r.L_single };
    let b = mkb(code, typ, "compact", "long", dr, r.D, tol, len, [r.L_tol, -r.L_tol], [r.dr_tol_upper, r.dr_tol_lower], cat(["compact_long-compact-", dr]));
    b.plated = plated; b.double = dbl; b.counterbore = cb; b.flange = flange_of(r, "compact"); b.page = "p.470";
    b
}
fn compact_medium_part(code, typ, dr, suf, plated, cb) {
    let name = cat([typ, dr, suf]);
    if typ != "E-LBH" {
        let m = cat([typ, ": the medium compact flanged bushing is ordered as E-LBH<dr>DUU, or E-LBH<dr>DMUU for electroless nickel plating (p.471); the Z and M type letters belong to the UU / LUU bushings"]);
        refuse("invalid", m);
    }
    let r = table("compact_medium", dr);
    if r == () { offered(name + ": the medium compact flanged bushing is offered for dr ", "compact_medium", " (p.471)"); }
    let tol = if plated { r.D_tol_ni } else { r.D_tol };
    let b = mkb(code, typ, "compact", "medium", dr, r.D, tol, r.L, [r.L_tol, -r.L_tol], [0, r.dr_tol], cat(["compact_medium-compact-", dr]));
    b.plated = plated; b.counterbore = cb; b.flange = flange_of(r, "compact"); b.page = "p.471";
    b
}
fn parse_compact(code, typ, dr, suf, plated, cb) {
    if suf == "UU" || suf == "LUU" { return compact_long_part(code, typ, dr, suf, plated, cb); }
    compact_medium_part(code, typ, dr, suf, plated, cb)
}

fn pilot_long_part(code, typ, dr, suf, fam, plated, cb) {
    let name = cat([typ, dr, suf]);
    let r = table("pilot_long", fam + "-" + dr);
    let tail = cat([" (", pages("pilot_long-" + fam + "-pages"), ")"]);
    if r == () { offered(name + ": flanged bushings with pilot are offered for dr ", "pilot_long-" + fam, tail); }
    let dbl = suf == "LUU";
    let tol = if plated { r.D_tol_ni } else { r.D_tol };
    let len = if dbl { r.L_double } else { r.L_single };
    let drt = if dbl { r.dr_tol_double } else { r.dr_tol_single };
    let b = mkb(code, typ, fam, "long", dr, r.D, tol, len, [r.L_tol, -r.L_tol], [0, drt], cat(["pilot_long-", fam, "-", dr]));
    b.plated = plated; b.double = dbl; b.counterbore = cb; b.flange = flange_of(r, fam);
    b.layout = "pilot"; b.x0 = r.l; b.page = first_tok(r.page);
    b
}
fn pilot_medium_part(code, typ, dr, suf, fam, cb) {
    let name = cat([typ, dr, suf]);
    let stem = if typ.ends_with("M") { cut1(typ) } else { typ };
    if suf == "DUU" || (suf == "DMUU" && typ.ends_with("M")) {
        let m = cat([typ, ": the medium bushing with pilot is ordered as ", stem, "<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series)"]);
        refuse("invalid", m);
    }
    let r = table("pilot_medium", fam + "-" + dr);
    let tail = cat([" (", pages("pilot_medium-" + fam + "-pages"), ")"]);
    if r == () { offered(name + ": the medium bushing with pilot is offered for dr ", "pilot_medium-" + fam, tail); }
    let b = mkb(code, typ, fam, "medium", dr, r.D, r.D_tol_ni, r.L, [r.L_tol, -r.L_tol], [0, r.dr_tol], cat(["pilot_medium-", fam, "-", dr]));
    b.plated = true; b.counterbore = cb; b.flange = flange_of(r, fam);
    b.layout = "pilot"; b.x0 = r.l; b.page = first_tok(r.page);
    b
}
fn parse_pilot(code, typ, dr, suf, fam, plated, cb) {
    if suf == "UU" || suf == "LUU" { return pilot_long_part(code, typ, dr, suf, fam, plated, cb); }
    pilot_medium_part(code, typ, dr, suf, fam, cb)
}

fn center_long_part(code, typ, dr, suf, fam, plated, cb) {
    let name = cat([typ, dr, suf]);
    let r = table("center_long", fam + "-" + dr);
    let tail = cat([" (", pages("center_long-" + fam + "-pages"), ")"]);
    if r == () { offered(name + ": centre flanged bushings are offered for dr ", "center_long-" + fam, tail); }
    let tol = if plated { r.D_tol_ni } else { r.D_tol };
    let b = mkb(code, typ, fam, "long", dr, r.D, tol, r.L, [r.L_tol, -r.L_tol], [0, r.dr_tol], cat(["center_long-", fam, "-", dr]));
    b.plated = plated; b.double = true; b.counterbore = cb; b.flange = flange_of(r, fam);
    b.layout = "center"; b.x0 = r.l; b.page = first_tok(r.page);
    b
}
fn center_medium_part(code, typ, dr, suf, fam, cb) {
    let name = cat([typ, dr, suf]);
    let stem = if typ.ends_with("M") { cut1(typ) } else { typ };
    if typ.ends_with("M") {
        let m = cat([typ, ": the medium centre flanged bushing is ordered as ", stem, "<dr>DMUU (nickel plated by the DMUU suffix), not with the M type letter"]);
        refuse("invalid", m);
    }
    let r = table("center_medium", fam + "-" + dr);
    let tail = cat([" (", pages("center_medium-" + fam + "-pages"), ")"]);
    if r == () { offered(name + ": the medium centre flanged bushing is offered for dr ", "center_medium-" + fam, tail); }
    let b = mkb(code, typ, fam, "medium", dr, r.D, r.D_tol_ni, r.L, [r.L_tol, -r.L_tol], [0, r.dr_tol], cat(["center_medium-", fam, "-", dr]));
    b.plated = true; b.counterbore = cb; b.flange = flange_of(r, fam);
    b.layout = "center"; b.x0 = r.l; b.page = first_tok(r.page);
    b
}
fn parse_center(code, typ, dr, suf, fam, plated, cb) {
    if suf == "UU" || suf == "DUU" {
        let stem = if typ.ends_with("M") { cut1(typ) } else { typ };
        let m = cat([typ, ": the centre flanged bushing is a double bushing: LUU (long) or DMUU (medium, plain type ", stem, " only), not ", suf]);
        refuse("invalid", m);
    }
    if suf == "LUU" { return center_long_part(code, typ, dr, suf, fam, plated, cb); }
    center_medium_part(code, typ, dr, suf, fam, cb)
}

fn parse_ext(code, typ, dr, suf, fam, layout, plated, cb) {
    if suf == "TUU" { refuse("invalid", typ + " has no short (TUU) version"); }
    if layout == "standard" { return parse_compact(code, typ, dr, suf, plated, cb); }
    if layout == "pilot" { return parse_pilot(code, typ, dr, suf, fam, plated, cb); }
    parse_center(code, typ, dr, suf, fam, plated, cb)
}

// ---- the description (the Python Bushing.description) ----------------------------------------------
fn compact_text(b) {
    let f = b.flange;
    let n = if f.F == () { 2 } else { 4 };
    let holes = cat([n, " counterbored holes d ", g(f.d), " / d1 ", g(f.d1), " x ", g(f.t), " deep, A ", g(f.A), " mm apart along H"]);
    if f.F != () { holes += cat([" and F ", g(f.F), " mm across"]); }
    let d = cat([", compact flange H ", g(f.H), " mm long, ", g(f.width), " mm across two flats, T ", g(f.T), " mm, "]);
    d + holes
}
fn plain_text(b) {
    let f = b.flange;
    let d = cat([", ", b.family, " flange H ", g(f.H), " mm"]);
    if b.family == "square" { d += cat([" (W ", g(f.W), " mm across flats)"]); }
    d + cat([", T ", g(f.T), " mm, 4 counterbored holes d ", g(f.d), " / d1 ", g(f.d1), " x ", g(f.t), " deep on P.C.D. ", g(f.pcd), " mm"])
}
fn describe_flange(b) {
    let d = if b.family == "compact" { compact_text(b) } else { plain_text(b) };
    if b.layout == "pilot" { d += cat([", pilot l ", g(b.x0), " mm from the end to the flange"]); }
    else if b.layout == "center" { d += cat([", flange centred, l ", g(b.x0), " mm from each end to the flange"]); }
    d
}
fn part_description(b) {
    let suffix = b.code.sub_string(b.typ.len() + b.dr.to_string().len());
    let d = cat(["MISUMI Economy linear bushing ", b.typ, b.dr, suffix, ", shaft diameter dr ", b.dr, " mm "]);
    d += cat(["(", sgn3(b.dr_tol[0]), "/", sgn3(b.dr_tol[1]), " mm, drawn at nominal), outside diameter D ", g(b.D), " mm "]);
    d += cat(["(0/", sgn3(b.D_tol), " mm), overall length L ", g(b.L), " mm (", sg2(b.L_tol[0]), "/", sg2(b.L_tol[1]), " mm)"]);
    if b.grooves != () {
        let gr = b.grooves;
        d += cat([", two ring grooves W ", g(gr.W), " mm wide on D1 ", g(gr.D1), " mm, B ", g(gr.B), " mm apart"]);
    }
    if b.flange != () { d += describe_flange(b); }
    d += ". Case equivalent to SUJ2, 58HRC~";
    if b.plated { d += ", electroless nickel plated"; }
    d + cat([". Balls, retainer and seals ", param("appx"), ": not drawn. Generated from the published catalogue dimensions."])
}
fn param(key) { table("params", key, "value") }

// ---- entry points ---------------------------------------------------------------------------------
fn stainless_at(rest) { rest.len() >= 2 && rest.sub_string(0, 1) == "S" && is_digit(rest.sub_string(1, 1)) }
fn refuse_raw(raw) {              // a code the strict template does not read: the Python parse()'s two shape errors
    let s = raw.to_upper();
    let st = false;
    if s.starts_with("E-LB") {
        let rest = s.sub_string(4);
        st = stainless_at(rest) || (rest.len() >= 1 && "FKH".contains(rest.sub_string(0, 1)) && stainless_at(rest.sub_string(1)));
    }
    if st {
        refuse("invalid", cat(["'", raw, "': stainless steel linear bushings (representative type E-LBHS) are only mentioned on p.470; the catalogue prints no dimension table for them, so they are not covered"]));
    }
    let m = cat(["'", raw, "': expected <type><dr><suffix>, type E-LB, E-LBF, E-LBFZ, E-LBFM, E-LBK, E-LBKZ or E-LBKM, "]);
    m += "suffix TUU (short), DUU / DMUU (medium) or UU / LUU (flanged single / double), e.g. E-LB10TUU, E-LBF20LUU; ";
    m += "the compact, pilot and centre types add H, P and C: E-LBH, E-LBHZ, E-LBHM, E-LBFP, E-LBKPM, E-LBHC, ...";
    refuse("invalid", m);
}

fn resolve(fields) {
    if fields.raw != () { refuse_raw(fields.raw); }
    let shape = if fields.shape == () { "" } else { fields.shape };
    let variant = if fields.variant == () { "" } else { fields.variant };
    let typ = "E-LB" + shape + variant;
    let drs = fields.dr;
    let suf = fields.suffix;
    let dr = parse_int(drs);
    let t = table("types", typ);
    let code = typ + drs + suf;
    let fam = t.family;
    let layout = t.layout;
    let cb = t.counterbore;
    let plated = t.plated == "yes" || suf == "DMUU";
    let b = if fam == "compact" || layout != "standard" { parse_ext(code, typ, dr, suf, fam, layout, plated, cb) }
            else if fam == "straight" { parse_straight(code, typ, dr, suf, plated) }
            else { parse_flanged(code, typ, dr, suf, fam, plated, cb) };
    let params = #{ blen: g(b.L) + " mm", opp: if b.counterbore == "opposite" { "1" } else { "0" }, plated: if b.plated { "1" } else { "0" } };
    let material = "Case equivalent to SUJ2, 58HRC~" + (if b.plated { "; electroless nickel plating" } else { "" });
    let facts = b;
    let props = #{ part_number: code, description: part_description(b), material: material, facts: facts };
    #{ configuration: b.cfg, parameters: params, properties: props }
}

// the inverse, for code printing (a bill of materials): configuration row + parameters -> the fields of the first template
fn fields(configuration, parameters) {
    let r = table("rows", configuration);
    let plated = parameters.plated == "1";
    let opp = parameters.opp == "1";
    let len = parse_float(parameters.blen.split(" ")[0]);
    let shape = if r.shape == "round" { "F" } else if r.shape == "square" { "K" } else if r.shape == "compact" { "H" } else { () };
    let lay = if r.kind == "pilot" { "P" } else if r.kind == "center" { "C" } else { "" };
    let dbl = r.L2 != "" && len == r.L2.to_float();
    let suffix = "UU";
    if r.kind == "straight" && r.series == "short" { suffix = "TUU"; }
    else if r.series == "medium" { suffix = if plated { "DMUU" } else { "DUU" }; }
    else if dbl || r.kind == "center" { suffix = "LUU"; }
    let variant = lay;
    if opp { variant += "Z"; }
    if plated && r.series == "long" && r.kind != "straight" { variant += "M"; }
    #{ shape: shape, variant: if variant == "" { () } else { variant }, dr: r.dr.to_string(), suffix: suffix }
}
