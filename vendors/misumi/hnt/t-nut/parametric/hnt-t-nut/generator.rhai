// MISUMI 5 series pre-assembly T-nuts (HNTT family): ordering-code logic as plain Rhai.
// Interface: docs/formats/generator.md (SolidCraft generator interface v2): resolve(fields) -> #{configuration, parameters} or refuse(kind, message).
// Everything numeric comes from tables/*.csv (copied from data/*.csv, every row cites its source id and page); this script only reads them.

fn g(x) {                         // Python's {:g}
    let f = x.to_float();
    if f == f.floor() && f.abs() < 1000000000.0 { f.to_int().to_string() } else { f.to_string() }
}
fn join(a, sep) {
    let s = "";
    for i in 0..a.len() { if i > 0 { s += sep; } s += a[i]; }
    s
}
fn split_bar(s) { s.to_string().split("|") }
fn param(name) { table("params", name, "value") }
fn ch(a, i) { a.sub_string(i, 1) }
fn is_digit(c) { c >= "0" && c <= "9" }
fn is_upper(c) { c >= "A" && c <= "Z" }

// the Python pattern ^(S?HNT[A-Z]*5)(?:-(\d+(?:\.\d)?))?$ , one part at a time
fn valid_type(t) {
    let i = 0;
    if t.starts_with("S") { i = 1; }
    if t.sub_string(i, 3) != "HNT" { return false; }
    let n = t.len();
    if n < i + 4 || ch(t, n - 1) != "5" { return false; }
    for k in (i + 3)..(n - 1) { if !is_upper(ch(t, k)) { return false; } }
    true
}
fn valid_m(s) {
    let n = s.len();
    if n == 0 { return false; }
    let dot = s.index_of(".");
    if dot < 0 {
        for k in 0..n { if !is_digit(ch(s, k)) { return false; } }
        return true;
    }
    if dot == 0 || dot != n - 2 || !is_digit(ch(s, n - 1)) { return false; }
    for k in 0..dot { if !is_digit(ch(s, k)) { return false; } }
    true
}

fn describe(typ, kind, material, surface, m, e, t) {
    let d = `MISUMI pre-assembly insertion nut ${typ} (${kind}) for 5 series (slot width 6 mm) extrusions, M${m}, ${g(param("plan"))} x ${g(param("plan"))} mm plan, E=${g(e)}, T=${g(t)}, ${material}`;
    if surface != "-" { d += `, ${surface}`; }
    if m == 5 { let tq = g(param("torque_m5")); d += `, reference tightening torque ${tq} N m`; }
    d + ". Generated from the published catalogue dimensions; the flank profile and the edge rounds are measured from the drawing; the tap drill is the ISO coarse one."
}

fn resolve(fields) {
    let typ = fields.type.to_upper();
    let ms = fields.m;
    let types = split_bar(param("types"));
    let shown = typ; if ms != () { shown += "-" + ms; }
    if !valid_type(typ) || (ms != () && !valid_m(ms)) {
        let tl = join(types, ", ");
        refuse("invalid", `'${shown}': expected <type>-<M>, e.g. HNTT5-4 (types: ${tl})`);
    }
    if !(typ in types) {
        let tl = join(types, ", ");
        if typ in split_bar(param("other_types")) { refuse("not_modelled", `${typ}: a valid 5 series nut, not drawn here; drawn: ${tl}`); }
        refuse("invalid", `unknown nut type '${typ}'; drawn: ${tl}`);
    }
    let row = table("types", typ);
    let allowed = []; for x in split_bar(row.allowed_m) { allowed.push(parse_int(x)); }
    let m = 0;
    if ms == () { m = param("default_m").to_int(); }
    else {
        if ms.index_of(".") >= 0 || !(parse_int(ms) in allowed) {
            let offered = ""; for i in 0..allowed.len() { if i > 0 { offered += ", "; } offered += "M" + allowed[i]; }
            refuse("invalid", `${typ} is offered in ${offered}, not M${ms}`);
        }
        m = parse_int(ms);
    }
    let pn = code_template(#{ type: typ, m: m.to_string() });
    let material = row.material;
    if row.surface != "-" { material += "; " + row.surface; }
    #{ configuration: `${typ}-${m}`, parameters: #{},
       properties: #{ part_number: pn, description: describe(typ, row.kind, row.material, row.surface, m, row.E, row.T), material: material } }
}

// parameters -> fields (generator.code, bill of materials): the canonical code always names the thread
fn fields(configuration, parameters) {
    let a = configuration.split("-");
    #{ type: a[0], m: a[1] }
}
