// MISUMI Economy flanged shaft supports (standard, thickened, end mounting, with slit, compact collar; long sleeve types): ordering-code logic as plain Rhai.
// Interface: docs/formats/generator.md (SolidCraft generator interface v2): resolve(fields) -> #{configuration, parameters, properties} or refuse(kind, message).
// Every number comes from tables/*.csv (copies of data/*.csv, each row cites its source id and page); this script only reads them.
// Every refusal of the Python generator (src/support.py) is a refuse() here with the Python message word for word.

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
fn dlist(name) {                  // Python's repr of a sorted list of ints (the keys are written sorted)
    let s = "";
    for k in param(name).to_string().split("|") { if s != "" { s += ", "; } s += k; }
    "[" + s + "]"
}
fn family_name(f) {
    if f == "round" { return "round flanged"; }
    if f == "square" { return "square flanged"; }
    if f == "compact" { return "compact flanged"; }
    "compact clamp"
}
fn series_name(s) {
    if s == "std" { return "standard sleeve"; }
    if s == "thick" { return "thickened"; }
    if s == "xend" { return "end mounting"; }
    if s == "slit" { return "flanged with slit"; }
    "compact"
}
fn table_name(series, long) {
    if series == "std" { return "dims"; }
    if series == "slit" && long { return "slit_long"; }
    series
}
fn expected(shown) {
    let ft = param("families_text");
    `'${shown}': expected <type><D>, e.g. E-STHRB8, with type one of ${ft}`
}
// a code that matches no template: the Python message of a code that is not <type><D> (the stand-in asks for it, see the README)
fn no_match(raw) { expected(raw) }

fn typ_of(fields) {               // the type text the code names
    if fields.type != () { return "E-" + fields.type.to_upper(); }
    let st = ""; if fields.stainless { st = "S"; }
    let se = ""; if fields.series == "xend" { se = "X"; } if fields.series == "slit" { se = "W"; } if fields.series == "mr" { se = "M"; }
    let sh = "C"; if fields.shape == "round" { sh = "R"; } if fields.shape == "square" { sh = "S"; }
    let bl = ""; if fields.black { bl = "B"; }
    let th = ""; if fields.thick { th = "N"; }
    let lo = ""; if fields.long { lo = "L"; }
    "E-" + st + "STH" + se + sh + bl + th + lo
}
fn stations(long, D) {            // set screw stations of the standard and thickened series
    if !long { return 1; }
    if D == 12 { 1 } else { 2 }
}
fn body_text(series, long, D, d, nst) {
    let L = d.L; if long && d.L1 != () && (d.L1 != () && d.L1 != "") { L = d.L1; }
    if series == "std" || series == "thick" {
        let sc = nst * 2;
        return `sleeve O${g(d.D1)} x L=${g(L)}, flange T=${g(d.T)}, ${sc} x M${g(d.M)} set screw holes (l from the flange back face), `;
    }
    if series == "xend" {
        let a = `sleeve O${g(d.D1)} x L=${g(d.L)}, flange T=${g(d.T)}, blind hole to l1=${g(d.l1)}, `;
        return a + `mounting screw M${g(d.M)} through O${g(d.d2)} / counterbore O${g(d.d1)} depth l=${g(d.l)}, `;
    }
    if series == "slit" {
        let a = `sleeve O${g(d.D1)} x L=${g(d.L)}, flange T=${g(d.T)}, clamp groove S1=${g(d.S1)}, slit ${g(d.S)}, clamp screw M${g(d.M)} `;
        return a + "(one hex socket head cap screw supplied; two for the long sleeve, which has two clamp screws at B / 4 and 3 B / 4), ";
    }
    let a = `body O${g(d.H)} x L=${g(L)}, clamp groove S=${g(d.S)}, clamp screw M${g(d.M)} (one hex socket head cap screw supplied), `;
    a + `2 mounting holes O${g(d.d1)} on P=${g(d.P)}, `
}
fn describe(typ, D, d, series, family, long, nst, material, surface) {
    let tol = signed3(d.tol_upper) + "/" + signed3(d.tol_lower) + " mm";
    let kind = family_name(family) + ", " + series_name(series);
    if long { kind += ", long sleeve"; }
    let head = `MISUMI Economy shaft support ${typ}${D} (${kind}), hole D${D} H8 (${tol}), `;
    head + body_text(series, long, D, d, nst) + `${material}, ${surface}. Generated from the published catalogue dimensions.`
}

fn resolve(fields) {
    if fields.raw != () { refuse("invalid", no_match(fields.raw)); }
    let typ = typ_of(fields);
    let digits = fields.d.to_string();
    let t = table("types", typ);
    if t == () { refuse("invalid", expected(typ + digits)); }
    let D = parse_int(digits);
    let series = t.series; let long = t.long == 1;
    let tname = table_name(series, long); let page = param("page_" + series);
    let d = table(tname, D);
    if d == () {
        let dl = dlist("dkeys_" + tname);
        refuse("invalid", `${typ}${D}: hole diameter D must be one of ${dl} (${page})`);
    }
    if long && series != "slit" && (d.L1 == () || d.L1 == "") {
        let ok = dlist("long_ok_" + tname);
        refuse("invalid", `${typ}${D}: the long sleeve type is only applicable to the D marked * in the table: ${ok} (${page})`);
    }
    let na = t.not_applicable_d.to_string().split("|");
    if (t.not_applicable_d != () && t.not_applicable_d != "") && (D.to_string() in na) {
        refuse("invalid", `${typ} is not applicable when D = ${D} (${page} note)`);
    }
    let key = `${series}-${t.family}-${if long { "long-" } else { "" }}${D}`;
    let nst = stations(long, D);
    let desc = describe(typ, D, d, series, t.family, long, nst, t.material, t.surface);
    #{ configuration: key, parameters: #{},
       properties: #{ part_number: typ + digits, description: desc, material: t.material, surface: t.surface,
                      type_name: typ, series: series, family: t.family, long: long, D: D, table: tname } }
}
