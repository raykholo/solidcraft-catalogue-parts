// MISUMI 5 series extruded brackets (HBLTS5 ... HBLTHB5): ordering-code logic as plain Rhai.
// Interface: docs/formats/generator.md (SolidCraft generator interface v2): resolve(fields) -> #{configuration, parameters, properties} or refuse(kind, message).
// Every number comes from tables/*.csv (generated from data/*.csv, each row cites its source id and page); this script only reads them.
// The code is <type>[-<alteration>] with the type's own "-4" (HBLTS5-4): the configuration row is the type, the alteration is accessory text only.

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
fn is_str(x) { type_of(x) == "string" }

fn refuse_type(c, base) {         // the code names no drawn type
    let dl = bar(param("drawn")); let drawn = join(dl, ", ");
    let ol = bar(param("other_types"));
    if base in ol {
        refuse("not_modelled", `${c}: a valid MISUMI 5 series bracket, not drawn here; drawn: ${drawn}`);
    }
    if table("types", base) != () {
        refuse("invalid", `${c}: ${base} has no -4 version (an M4 screw version exists for HBLTS5 only; the plain code is the M5 one)`);
    }
    if base.ends_with("6") || base.ends_with("8") {
        refuse("invalid", `${c}: only the 5 series (slot width 6 mm) brackets are drawn, e.g. HBLTS5`);
    }
    refuse("invalid", `'${c}': expected a bracket code such as HBLTS5 or HBKUS5; drawn: ${drawn}`);
}
fn check_alteration(c, key, rest) {   // -> the alteration ("" for none); refuses
    if rest.len() == 0 { return ""; }
    let al = ["C"] + bar(param("alterations")); let all = join(al, ", ");
    if rest.len() > 1 {
        refuse("invalid", `${c}: one alteration at most (${all}); the catalogue lists them as alternatives`);
    }
    let alt = rest[0];
    if alt == "C" {
        if table("types", key, "alt_c") != 1 {
            let okl = bar(param("alt_c_types")); let ok = join(okl, ", ");
            refuse("invalid", `${c}: alteration C (M5 taps for cover mounting) is not offered for ${key} on the catalogue page; offered for: ${ok}`);
        }
        return alt;
    }
    if table("alterations", alt) == () {
        let cl = bar(param("alterations")); let ca = join(cl, ", ");
        refuse("invalid", `${c}: unknown alteration '${alt}'; the catalogue lists C, ${ca} (no -5 or other suffix exists)`);
    }
    alt
}
fn alteration_text(key, alt, r) {
    if alt == "" { return ""; }
    if alt == "C" { return " Alteration C: M5 taps on both sides for cover mounting (not drawn; mounting screw HCBM)."; }
    let a = table("alterations", alt);
    let d = ` Alteration ${alt}: ${a.name} supplied in a set with the bracket (accessory, not drawn).`;
    if key == "HBLTS5" { d += ` For HBLTS5 the set is screw ${a.screw} and nut ${a.nut}.`; }
    else { d += " The catalogue lists the set contents for HBLTS5 only; check the applicable screws and nuts for this bracket."; }
    if r.surface.contains("Black") { d += " Screws for black anodized brackets are HCBMTB (Trivalent Chromate Black)."; }
    d
}
fn describe_part(key, alt, r) {
    let n = bar(r.foot_holes).len() + bar(r.wall_holes).len();
    let d = `MISUMI extruded bracket ${key} for 5 series (slot width 6 mm) extrusions (${r.family}), ${g(r.square)} square, `;
    d += `${g(r.width)} wide, ${g(r.foot_t)} thick, arms ${g(r.foot)} x ${g(r.wall)} mm, `;
    d += `${n} holes O${g(r.hole_d)}, ${r.material}, ${r.surface}, `;
    d += `catalogue mass ${g(r.mass_g)} g, screw ${r.screw}, T nut ${r.nut}, allowable load ${g(r.allowable_n)} N.`;
    if !is_str(r.hole_x) {
        let other = r.width - r.hole_x;
        d += ` Eccentric: the holes are ${g(r.hole_x)} from one side and ${g(other)} from the other.`;
    }
    if r.tab_w != 0 {
        d += ` Perpendicularly machined, perpendicularity K ${r.perp_k}; tabs ${g(r.tab_w)} wide and ${g(r.tab_h)} high `;
        d += "on the bottom of the arms fit the 6 mm slot (length not dimensioned in the catalogue).";
    }
    d += alteration_text(key, alt, r);
    d + " Generated from the published catalogue dimensions; the inner-corner web with its ribs is not drawn."
}

fn resolve(fields) {
    let c = fields.raw;                         // a code the first template does not take (a dangling `-`, `--`): the text as typed
    if c == () { c = code_template(fields); }
    resolve_code(c)
}
fn resolve_code(c) {
    let toks = c.split("-");
    let base = toks[0];
    let rest = [];
    for i in 1..toks.len() { rest.push(toks[i]); }
    let key = base;
    if rest.len() > 0 && rest[0] == "4" { key = base + "-4"; rest.remove(0); }
    if table("types", key) == () { refuse_type(c, base); }
    let alt = check_alteration(c, key, rest);
    let r = table("types", key);
    let desc = describe_part(key, alt, r);
    #{ configuration: key, parameters: #{},
       properties: #{ part_number: c, description: desc, material: r.material, surface: r.surface, alteration: alt } }
}

// parameters -> fields (generator.code): the type's own spelling; the alteration is accessory text, not a parameter
fn fields(configuration, parameters) {
    if configuration.ends_with("-4") {
        return #{ base: configuration.sub_string(0, configuration.len() - 2), rest: "4" };
    }
    #{ base: configuration, rest: () }
}
