// MISUMI Economy flanged shaft supports with slit and positioning (dowel) holes E-STHWRBK / E-STHWRK / E-SSTHWRK (round), E-STHWCBK / E-SSTHWCK (compact): ordering-code logic as plain Rhai.
// Interface: docs/formats/generator.md (SolidCraft generator interface v2): resolve(fields) -> #{configuration, parameters, properties} or refuse(kind, message).
// Every number comes from tables/*.csv (copies of data/*.csv, each row cites its source id and page); this script only reads them.
// Every refusal of the Python generator (src/dowel.py) is a refuse() here with the Python message word for word.

fn g(x) {                         // Python's {:g}
    let f = x.to_float();
    if f == f.floor() && f.abs() < 1000000000.0 { f.to_int().to_string() } else { f.to_string() }
}
fn signed3(x) {                   // Python's {:+.3f}
    let n = (x.to_float().abs() * 1000.0).round().to_int();
    let frac = (n % 1000).to_string();
    while frac.len() < 3 { frac = "0" + frac; }
    let sign = "+"; if x.to_float() < 0.0 { sign = "-"; }
    sign + (n / 1000).to_string() + "." + frac
}
fn param(name) { table("params", name, "value") }
fn dlist() {                      // Python's repr of sorted(TABLE)
    let s = "";
    for k in param("dkeys").split("|") { if s != "" { s += ", "; } s += k; }
    "[" + s + "]"
}
fn family_name(family) { if family == "round" { "round flanged" } else { "compact flanged" } }

fn typ_of(fields) {              // the type text the code names: "E-" + letters
    if fields.type != () { return "E-" + fields.type.to_upper(); }
    let letter = "R"; if fields.shape == "compact" { letter = "C"; }
    let st = ""; if fields.stainless { st = "S"; }
    let bl = ""; if fields.black { bl = "B"; }
    "E-" + st + "STHW" + letter + bl + "K"
}
fn describe(typ, D, d, family, material, surface) {
    let tol = signed3(d.tol_upper) + "/" + signed3(d.tol_lower) + " mm";
    let head = `MISUMI Economy shaft support ${typ}${D} (flanged with slit, positioning hole, ${family_name(family)}), `;
    let body = `hole D${D} H8 (${tol}), sleeve O${g(d.D1)}, overall length L=${g(d.L)}, flange T=${g(d.T)}, `;
    let clamp = `2 positioning (dowel) holes Q${g(d.Q)} H8, clamp groove S1=${g(d.S1)}, slit ${g(d.S)}, clamp screw M${g(d.M)} `;
    head + body + clamp + `(one hex socket head cap screw supplied), ${material}, ${surface}. Generated from the published catalogue dimensions.`
}

// a code that matches no template: the Python message of a code that is not <type><D> (the stand-in asks for it, see the README)
fn no_match(raw) {
    let tt = param("types_text");
    `'${raw}': expected <type><D>, e.g. E-STHWRBK12, with type one of ${tt}`
}

fn resolve(fields) {
    if fields.raw != () { refuse("invalid", no_match(fields.raw)); }
    let typ = typ_of(fields);
    let digits = fields.d.to_string();
    let t = table("types", typ);
    if t == () {
        let tt = param("types_text"); let shown = typ + digits;
        refuse("invalid", `'${shown}': expected <type><D>, e.g. E-STHWRBK12, with type one of ${tt}`);
    }
    let D = parse_int(digits);
    let d = table("dims", D);
    if d == () {
        let dl = dlist(); let pg = param("page");
        refuse("invalid", `${typ}${D}: hole diameter D must be one of ${dl} (${pg} table)`);
    }
    let code = typ + digits;
    #{ configuration: `${t.family}-${D}`, parameters: #{},
       properties: #{ part_number: code, description: describe(typ, D, d, t.family, t.material, t.surface), material: t.material, surface: t.surface,
                      type_name: typ, family: t.family, D: D } }
}
