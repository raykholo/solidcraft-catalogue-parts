// MISUMI Economy Series shaft collars (C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW, C-SCSBNAW, E-[P|S]SCD, E-[P|S]SCDJ, E-[P|S]SCSPD): ordering-code logic as plain Rhai.
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
fn param(name) { table("params", name, "value") }
fn fix2(x) {                      // Python's {:.2f}
    let n = (x.to_float() * 100.0).round().to_int();
    let f = n % 100; let fs = f.to_string();
    if f < 10 { fs = "0" + fs; }
    `${n / 100}.${fs}`
}
fn is_digits(s, lo, hi) {         // the regular expression \d{lo,hi}
    let n = s.len();
    if n < lo || n > hi { return false; }
    for i in 0..n {
        let ch = s.sub_string(i, 1);
        let ok = "0123456789".contains(ch);
        if !ok { return false; }
    }
    true
}
fn has_num(s) { s != () && s != "" }
fn appx() { "(appearance, approximate)" }
fn bore_tol(family) {             // [upper, lower] printed before cutting
    if family == "split-compact" || family == "" { return [param("bore_tol_upper"), param("bore_tol_lower")]; }
    [param("bore_tol_slit_urethane_upper"), param("bore_tol_slit_urethane_lower")]
}
fn tol_text(tol) {
    let u = fix2(tol[0]); let l = fix2(tol[1]);
    `(+${u}/+${l} is the tolerance before cutting; drawn at the nominal diameter)`
}

fn shape_error(raw) {
    refuse("invalid", `'${raw}': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms`);
}
fn ring_page(typ) { if typ == "C-SCSMAW" || typ == "C-SCSGAW" { "545" } else { "544" } }

// ---- the aluminium rings -------------------------------------------------------------------------------
fn fix_text(typ, r) {
    let s = `, 2 fixing holes on pitch P=${g(r.P)} mm`;
    if typ == "C-SCSMAW" { return s + `, through holes diameter ${g(r.S)} mm`; }
    s + `, through diameter ${g(r.d1)} mm, counterbore diameter ${g(r.d2)} mm depth ${g(r.t)} mm`
}
fn describe_ring(typ, d, b, r, t) {
    let tt = tol_text(bore_tol(""));
    let s = `MISUMI Economy Series shaft collar ${typ}${d}-${b} (${t.kind}), I.D. D=${d} mm ${tt}, `;
    s += `width B=${b} mm, O.D. D1=${g(r.D1)} mm, clamp screw ${r.M}, ${t.material}, ${t.surface.to_lower()}`;
    if has_num(r.P) { s += fix_text(typ, r); }
    let a = appx();
    s + `. Generated from the published catalogue dimensions; slit, clamp screw position and chamfers are ${a}.`
}
fn check_ring(typ, d, b) {         // -> the sizes row; refuses
    let ds = bar(param("ds_" + typ));
    let pg = ring_page(typ);
    if !(d.to_string() in ds) {
        let dl = join(ds, ", ");
        refuse("invalid", `${typ} is offered for I.D. D in ${dl} mm, not ${d} (p.${pg} table)`);
    }
    let r = table("sizes", `${typ}-${d}-${b}`);
    if r == () {
        let bn = `bs_${typ}_${d}`; let bv = bar(param(bn)); let bl = join(bv, ", ");
        refuse("invalid", `${typ}${d} is offered in width B = ${bl} mm, not ${b} (p.${pg} table)`);
    }
    r
}
fn result(configuration, typ, c, desc, t) {
    let props = #{ part_number: c, description: desc, material: t.material, surface: t.surface, type_name: typ };
    #{ configuration: configuration, parameters: #{ part_type: typ }, properties: props }
}
fn resolve_ring(fields, c) {
    let typ = "C-" + fields.type;
    let d = fields.d; let b = fields.b;
    let r = check_ring(typ, d, b);
    let t = table("types", typ);
    let row = `${typ}-${d}-${b}`;
    // Slit rings with the same bore, outside diameter and screw share geometry
    // except for width. Keep the table-derived width as both height parameters.
    if typ == "C-SCSAW" {
        let widths = bar(param(`bs_${typ}_${d}`));
        for candidate in widths {
            let base = table("sizes", `${typ}-${d}-${candidate}`);
            if base.D1 == r.D1 && base.M == r.M {
                row = `${typ}-${d}-${candidate}`;
                break;
            }
        }
    }
    let out = result(row, typ, c, describe_ring(typ, d, b, r, t), t);
    out.parameters.ring_h = `${g(b)} mm`;
    out.parameters.ht = `${g(b)} mm`;
    out
}

// ---- the bearing inner mount collar --------------------------------------------------------------------
fn describe_bearing(c, d, ds, r, t) {
    let tt = tol_text(bore_tol(""));
    let s = `MISUMI Economy Series shaft collar ${c} (${t.kind}), I.D. D=${d} mm ${tt}, boss diameter Ds=${ds} mm, `;
    s += `ring width b=${g(r.b)} mm, total width B=${g(r.B)} mm, O.D. D1=${g(r.D1)} mm, clamp screw ${r.M}, ${t.material}, ${t.surface.to_lower()}. `;
    let a = appx();
    s + `Generated from the published catalogue dimensions; slit, clamp screw position and chamfers are ${a}.`
}
fn resolve_bearing(fields, c) {
    let typ = "C-SCSBNAW";
    let d = fields.d; let ds = fields.ds;
    let dl = bar(param("ds_bearing"));
    if !(d.to_string() in dl) {
        let dj = join(dl, ", ");
        refuse("invalid", `${typ} is offered for I.D. D in ${dj} mm, not ${d} (p.546 table)`);
    }
    let r = table("bearing", `${typ}-${d}`);
    if ds != r.Ds { refuse("invalid", `${typ}${d} is offered with selection Ds = ${r.Ds} mm only, not ${ds} (p.546 table; the ordering example is C-SCSBNAW12-16)`); }
    let t = table("types", typ);
    result(`${typ}-${d}`, typ, c, describe_bearing(c, d, ds, r, t), t)
}

// ---- the collars with urethane -------------------------------------------------------------------------
fn family_of(fam) { if fam == "SCSPD" { "split-compact" } else if fam == "SCDJ" { "slit-compact" } else { "slit" } }
fn page_of(family) { if family == "slit" { "p.547 standard type" } else if family == "slit-compact" { "p.547 compact type" } else { "p.546" } }
fn describe_ure(c, typ, family, r, t) {
    let tt = tol_text(bore_tol(family));
    let s = `MISUMI Economy Series shaft collar ${c} (${t.kind}), I.D. D=${r.D} mm ${tt}, width B=${g(r.B)} mm `;
    s += `(steel B1=${g(r.B1)} mm plus urethane damper t=${g(r.t)} mm), O.D. D1=${g(r.D1)} mm (printed +-0.1), `;
    s += `clamp screw ${r.M} (clearance hole d=${g(r.d)} mm in the other half, head seat 2xR=${g(2.0 * r.R.to_float())} mm wide from Y=${g(r.Y)} mm, slit/gap W=${g(r.W)} mm), `;
    let screws = "1 screw"; if family == "split-compact" { screws = "2 screws"; }
    s += `${screws} at X=${g(r.X)} mm from the axis, ${t.material}, ${t.surface.to_lower()}; `;
    let a = appx();
    s + `damper: ${t.damper}; accessories: ${t.accessory}. Generated from the published catalogue dimensions; the damper's look, chamfers, the screws and the (Z) reference notch are ${a}.`
}
fn check_ure(typ, family, d, b) {   // -> the urethane row; refuses
    let dl = bar(param("ds_" + family));
    let pg = page_of(family);
    if !(d.to_string() in dl) {
        let dj = join(dl, ", ");
        refuse("invalid", `${typ} is offered for D in ${dj} mm, not ${d} (${pg} table)`);
    }
    let r = table("urethane", `${family}-${d}`);
    if family == "slit-compact" && b != r.B {
        refuse("invalid", `${typ}${d} is offered in width B = ${g(r.B)} mm only, not ${b} (${pg} table, B selection)`);
    }
    if typ.starts_with("E-SS") && r.stainless == 0 {
        let sd = join(bar(param("stainless_" + family)), ", ");
        refuse("invalid", `${typ} (stainless steel) is only available for D in ${sd} mm, not ${d} (${pg} note)`);
    }
    if family == "slit" && d == 4 && typ != "E-PSCD" { refuse("invalid", `${typ}4: for D = 4 only the electroless nickel plated E-PSCD4 is available (p.547 note)`); }
    r
}
fn ure_numbers(fields, c) {         // -> [D, B or ()]; refuses with the Python message when the compact slit has no width
    if fields.fam == "SCDJ" && fields.b == () {
        refuse("invalid", `'${c}': the compact slit type needs the width selection, <type><D>-<B>, e.g. E-SCDJ12-10 (p.547)`);
    }
    [fields.d, fields.b]
}
fn resolve_ure(fields, c) {
    let plat = ""; if fields.plat != () { plat = fields.plat; }
    let typ = "E-" + plat + fields.fam;
    let family = family_of(fields.fam);
    let nb = ure_numbers(fields, c);
    let d = nb[0];
    let r = check_ure(typ, family, d, nb[1]);
    let t = table("types", typ);
    result(`${family}-${d}`, typ, c, describe_ure(c, typ, family, r, t), t)
}

fn resolve(fields) {
    if fields.raw != () { shape_error(fields.raw); }
    let c = code_template(fields);
    if fields.type != () { return resolve_ring(fields, c); }
    if fields.kind != () { return resolve_bearing(fields, c); }
    resolve_ure(fields, c)
}

// parameters -> fields (generator.code): the type is the text parameter part_type, the bore comes from the row and ring width may be overridden
fn stem_of(rest) {
    if rest.ends_with("SCSPD") { return "SCSPD"; }
    if rest.ends_with("SCDJ") { return "SCDJ"; }
    "SCD"
}
fn ure_fields(configuration, typ) {
    let rest = typ.sub_string(2, typ.len() - 2);
    let stem = stem_of(rest);
    let plat = rest.sub_string(0, rest.len() - stem.len());
    let bits = configuration.split("-");
    let d = bits[bits.len() - 1];
    let f = #{ fam: stem, d: parse_int(d), b: (), plat: () };
    if stem == "SCDJ" { f.b = table("urethane", configuration, "B"); }
    if plat != "" { f.plat = plat; }
    f
}
fn bearing_fields(configuration, bits) {
    #{ kind: "SCSBNAW", d: parse_int(bits[2]), ds: table("bearing", configuration, "Ds") }
}
fn fields(configuration, parameters) {
    let typ = parameters.part_type;
    if typ.starts_with("E-") { return ure_fields(configuration, typ); }
    let bits = configuration.split("-");
    if typ == "C-SCSBNAW" { return bearing_fields(configuration, bits); }
    #{ type: typ.sub_string(2, typ.len() - 2), d: parse_int(bits[2]), b: if parameters.ring_h == () { parse_int(bits[3]) } else { parse_int(parameters.ring_h.split(" ")[0]) } }
}
