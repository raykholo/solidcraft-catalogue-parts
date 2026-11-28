// MISUMI Economy Series linear shafts (E-SFJ ... E-PFPGH): ordering-code logic as plain Rhai.
// Interface: docs/formats/generator.md (SolidCraft generator interface v2): resolve(fields) -> #{configuration, parameters} or refuse(kind, message).
// Everything numeric comes from tables/*.csv (copied from data/*.csv, each row cites its source id and page); this script only reads them.
// The options come as `fields.opts`, the ordered list of [name, argument text] the option bag read (name "?" = a token no option takes, raw text).
// Written in small functions: the documented sandbox allows an expression depth of 16 inside a function.

// ---- helpers --------------------------------------------------------------------------------------
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
fn nums(s) { let o = []; for x in split_bar(s) { o.push(parse_float(x)); } o }
fn param(name) { table("params", name, "value") }
fn pn(name) { param(name).to_float() }
fn ch(a, i) { a.sub_string(i, 1) }
fn is_digit(c) { c >= "0" && c <= "9" }
fn is_letter(c) { c >= "A" && c <= "Z" }
fn to_i(s) { parse_int(s) }
fn mlist(ms, pre) { let o = []; for m in ms { o.push(pre + g(m)); } join(o, ", ") }
fn has(a, x) { for y in a { if y == x { return true; } } false }
fn lead_letters(t) {
    let k = ""; let i = 0;
    while i < t.len() && is_letter(ch(t, i)) { k += ch(t, i); i += 1; }
    k
}
// `rest` preserves token order and repeats on the native host too.
fn numeric_arg(name, arg) {
    if arg == "" || name == "LKC" { return false; }
    let dots = 0;
    for ch in arg.chars() {
        if ch == '.' { dots += 1; }
        else if !"0123456789".contains(ch) { return false; }
    }
    if dots == 0 { return true; }
    if dots != 1 { return false; }
    if !(name in ["M", "N", "MD"]) { return false; }
    if arg.starts_with(".") || arg.ends_with(".") { return false; }
    arg.split(".")[1].len() == 1
}
fn option_pair(token) {
    let names = ["WSC", "WFC", "LFC", "LKC", "MD", "SC", "SX", "FC", "M", "N", "F", "P", "T", "X", "A", "E"];
    for name in names {
        if !token.starts_with(name) { continue; }
        let arg = token.sub_string(name.len());
        if name == "LKC" && arg == "" { return [name, ()]; }
        if numeric_arg(name, arg) { return [name, arg]; }
    }
    ["?", token]
}
fn option_tokens(text) {
    let out = [];
    if text == () || text == "" { return out; }
    if !text.starts_with("-") { return [["?", text]]; }
    for token in text.sub_string(1).split("-") { out.push(option_pair(token)); }
    out
}
fn option_text(tokens) {
    if tokens.len() == 0 { return (); }
    let text = "";
    for t in tokens { text += "-" + raw(#{ n: t[0], a: t[1] }); }
    text
}
fn raw(t) { if t.n == "?" { t.a } else if t.a == () { t.n } else { t.n + t.a } }
fn fmt3(x) {                      // Python's {:+.3f}
    let v = (x.to_float().abs() * 1000.0).round().to_int();
    let s = v.to_string();
    while s.len() < 4 { s = "0" + s; }
    let sign = "+"; if x.to_float() < 0.0 { sign = "-"; }
    sign + s.sub_string(0, s.len() - 3) + "." + s.sub_string(s.len() - 3, 3)
}
fn key_min(a) { let m = a[0]; for x in a { if x < m { m = x; } } m }
fn key_max(a) { let m = a[0]; for x in a { if x > m { m = x; } } m }
fn page_of(fam) { table("params", "page_" + fam, "value") }

// ---- the code -------------------------------------------------------------------------------------
fn usage(shown) {
    refuse("invalid", `'${shown}': expected <type><D>-<L>[-<option>...], e.g. E-PSFJ6-20 (straight), E-PSFJT6-30-M3 (one end tapped), E-PSFJC6-40-M3-SC0, E-PSFJZ6-50-M3-N3-SC0, E-PSFJW6-50-M3-N3, E-PSFPG8-200-F4-P6-M3-SC0, E-PSFPH8-200-F5-P6-M3-T5-SC0`);
}
fn alt_union() { ["LKC", "SC", "WSC", "FC", "WFC", "SX", "LFC"] }
fn alts_of(fam) {                 // the alterations offered per family (the pages' alteration tables)
    if fam == "C" { return ["LKC", "SC", "FC", "WFC", "SX"]; }
    if fam == "PG" { return ["LKC", "SC", "FC", "WFC", "SX", "LFC"]; }
    if fam == "PH" { return ["SC"]; }
    ["LKC", "SC", "WSC", "FC", "WFC"]
}
fn sorted_list(a) { let b = a; b.sort(); b }

fn resolve_type(name) {           // -> #{typ, tflag}
    if table("types", name) != () { return #{ typ: name, tflag: false }; }
    if name.ends_with("T") {
        let base = name.sub_string(0, name.len() - 1);
        let row = table("types", base);
        if row != () && row.family == "straight" { return #{ typ: base, tflag: true }; }
    }
    refuse("invalid", `'${name}' is not a type of the catalogue: E-SFJ, E-SSFJ, E-PSFJ, E-PSSFJ, E-PSFG (+ T, C, Z, W) and the stepped E-SFPG, E-SSFPG, E-PSFPG, E-PSSFPG, E-SFPH, E-SSFPH, E-PSFPH, E-PSSFPH, E-PFPGH`);
}
fn new_state(name, typ, tflag, fields) {
    let row = table("types", typ);
    let fam = if tflag { "T" } else { row.family };
    let D = fields.d;
    let dl = []; for x in split_bar(param("d_list")) { dl.push(to_i(x)); }
    if !has(dl, D) { let l = join(dl, ", "); refuse("invalid", `diameter ${D}: catalogue sizes are [${l}]`); }
    let dr = table("diameters", D);
    let f8 = dr.f8_upper != () && dr.f8_upper != "";
    let s = #{ name: name, typ: typ, tt: if tflag { "T" } else { "" }, D: D, L: fields.length.to_float(), fam: fam, base: row.base, page: page_of(fam),
               cls: row.tolerance_class, material: row.material, hardness: row.hardness, surface: row.surface,
               tapped: false, M: 0.0, lkc: false, length_tol: 0.0, F: 0, P: 0, T: 0, ymax: 0, md: false, taps: [], flats: [], notes: [], toks: [], sc: (), sx: (), wsc: (),
               fc: (), wfc: (), lfc: (), ext: #{}, lrange: [0, 0] };
    let sfx = if fam == "straight" || fam == "PG" || fam == "PH" { "" } else { fam };
    s.sfx = sfx;
    if s.cls == "f8" {
        if !f8 { refuse("invalid", `${typ} has no D${D}: the f8 type is listed for D 6-30 (p.432 note: D3, 4, 5 not applicable, 35/40/50 only E-PSFJ)`); }
        s.tol = [dr.f8_upper.to_float(), dr.f8_lower.to_float()]; s.lrange = [dr.f8_lmin, dr.f8_lmax];
    } else {
        s.tol = [dr.g7_upper.to_float(), dr.g7_lower.to_float()]; s.lrange = [dr.g7_lmin, dr.g7_lmax];
    }
    if (D == 35 || D == 40 || D == 50) && s.base != "E-PSFJ" && fam != "PG" && fam != "PH" {
        refuse("invalid", `O.D. ${D} is applicable only to E-PSFJ${sfx} (p.${s.page} note)`);
    }
    s.toks = option_tokens(fields.opts);
    s
}
// the positional first token: M / N / F / P / T / MD with its argument
fn take_tok(name) {               // method on the state: the argument text (and removes the token) or ()
    if this.toks.len() > 0 && this.toks[0][0] == name && this.toks[0][1] != () {
        let a = this.toks[0][1]; this.toks.remove(0); return a;
    }
    ()
}
fn peek_tok(s, name) { s.toks.len() > 0 && s.toks[0][0] == name && s.toks[0][1] != () }
fn tuple_to_tok(t) { #{ n: t[0], a: t[1] } }
fn tap_hint(fam, typ, D, L, ms) {
    let m = g(ms[ms.len() - 1]); let li = L.to_int();
    if fam == "T" { return `${typ}T${D}-${li}-M${m}`; }
    if fam == "C" { return `${typ}${D}-${li}-M${m}-SC0`; }
    if fam == "Z" { return `${typ}${D}-${li}-M${m}-N${m}-SC0`; }
    `${typ}${D}-${li}-M${m}-N${m}`
}
fn second_tap(s, ms, tail, M) {   // Z, W: the thread N of the right end
    let D = s.D; let page = s.page; let L = s.L;
    let na = s.take_tok("N");
    if na == () { let l = mlist(ms, "N"); refuse("invalid", `both ends tapped: the second thread N follows M, e.g. ${tail} (choices for D${D}: ${l})`); }
    let N = parse_float(na);
    if !has(ms, N) { let l = mlist(ms, "N"); refuse("invalid", `N${g(N)} is not offered for D${D} (coarse selection p.${page}: ${l})`); }
    s.taps.push(#{ M: N, face: L, dir: -1, depth: 2.0 * N, label: "right" });
    if 2.0 * M + 2.0 * N > L { let t = g(2.0 * M + 2.0 * N); let gl = g(L); refuse("invalid", `overall length L = ${gl} requires M x 2 + N x 2 <= L = ${t} (p.${page} note)`); }
    if 2.5 * M + 4.0 + 2.5 * N + 4.0 >= L { s.notes.push("M x 2.5 + 4 + N x 2.5 + 4 >= L: the catalogue says the tap pilot holes may go through"); }
    s
}
fn tap_family(s) {                // T, C, Z, W: M (and N) after the length
    let fam = s.fam; let typ = s.typ; let D = s.D; let page = s.page; let L = s.L;
    let tname = if fam == "T" { "tap" } else { "tap_j" + fam.to_lower() };
    let keys = []; for x in split_bar(table("params", "keys_" + tname, "value")) { keys.push(to_i(x)); }
    if !has(keys, D) {
        let extra = if fam == "C" || fam == "Z" { "; D3 and D4/D5 are only on p.432-433/436" } else { "" };
        let lo = key_min(keys); let hi = key_max(keys);
        refuse("invalid", `${typ}${s.tt}${D}: no such version of D${D} in the p.${page} table (D ${lo}-${hi}${extra})`);
    }
    if s.cls == "f8" && (D == 4 || D == 5) { refuse("invalid", `${typ}${s.tt}${D}: no tapped version of D${D} in the p.${page} table`); }
    let row = table(tname, D);
    s.lrange = [row.lmin, row.lmax];
    let ms = nums(row.m_options);
    let tail = tap_hint(fam, typ, D, L, ms);
    let ma = s.take_tok("M");
    if ma == () { let l = mlist(ms, "M"); refuse("invalid", `a tapped shaft needs its thread after the length, e.g. ${tail} (choices for D${D}: ${l})`); }
    let M = parse_float(ma);
    if !has(ms, M) { let l = mlist(ms, "M"); refuse("invalid", `M${g(M)} is not offered for D${D} (coarse selection p.${page}: ${l})`); }
    s.tapped = true; s.M = M;
    s.taps.push(#{ M: M, face: 0.0, dir: 1, depth: 2.0 * M, label: "left" });
    if fam == "Z" || fam == "W" { s = second_tap(s, ms, tail, M); }
    s
}
fn md_checks(fam, D, M, L) {      // MD: effective tap length M x 3 (p.437); -> the tap depth
    if fam != "PG" { refuse("invalid", "MD (effective tap length M x 3) is an alteration of p.437 only"); }
    let d_ok = pn("md_d_min") <= D && D <= pn("md_d_max");
    let m_ok = pn("md_m_min") <= M && M <= pn("md_m_max");
    if !(d_ok && m_ok) { let gm = g(M); refuse("invalid", `MD applies to D = 12-30 and M = 6-20 (p.437), not D${D} M${gm}`); }
    let t = 3.5 * M + 4.0;
    if t > L { let gt = g(t); let gl = g(L); refuse("invalid", `MD x 3.5 + 4 = ${gt} exceeds L = ${gl} (p.437)`); }
    pn("md_tap_factor") * M
}
fn stepped_family(s) {            // PG, PH: F, P, M (MD) [, T] after the length
    let fam = s.fam; let typ = s.typ; let D = s.D; let page = s.page; let L = s.L;
    let tname = if fam == "PG" { "stepped_pg" } else { "stepped_ph" };
    let keys = []; for x in split_bar(table("params", "keys_" + tname, "value")) { keys.push(to_i(x)); }
    if !has(keys, D) {
        let lo = key_min(keys); let hi = key_max(keys);
        refuse("invalid", `${typ}${D}: the stepped shafts of p.${page} are listed for D ${lo}-${hi} only (D 8, 10, 12, 13, 15, 16, 20, 25, 30)`);
    }
    let row = table(tname, D);
    s.lrange = [row.lmin, row.lmax];
    let ms = nums(row.m_options);
    let ex = `${typ}${D}-200-F4-P${g(row.pmin)}-M${g(ms[0])}` + (if fam == "PH" { "-T4" } else { "" }) + "-SC0";
    let ft = s.take_tok("F"); let pt = s.take_tok("P");
    if ft == () || pt == () { refuse("invalid", `a stepped shaft needs the step length F and diameter P after L, e.g. ${ex}`); }
    let F = to_i(ft); let P = to_i(pt);
    if !(row.pmin <= P && P <= row.pmax) { refuse("invalid", `P${P} is outside P ${g(row.pmin)}-${g(row.pmax)} for D${D} (p.${page} table)`); }
    let fmax = pn("step_f_max_factor") * P;
    if !(pn("step_f_min") <= F && F <= fmax) { let t = g(fmax); refuse("invalid", `F${F} is outside 2 <= F <= P x 4 = ${t} (p.${page})`); }
    let md = false; let M = 0.0;
    if peek_tok(s, "MD") { md = true; M = parse_float(s.take_tok("MD")); }
    else if peek_tok(s, "M") { M = parse_float(s.take_tok("M")); }
    else { let l = mlist(ms, "M"); refuse("invalid", `a stepped shaft needs its thread M after P, e.g. ${ex} (choices for D${D}: ${l})`); }
    if !has(ms, M) { let l = mlist(ms, "M"); refuse("invalid", `M${g(M)} is not offered for D${D} (coarse selection p.${page}: ${l})`); }
    if M >= P.to_float() { refuse("invalid", `M${g(M)} does not fit into the step P${P}`); }
    let depth = 2.0 * M;
    if md { depth = md_checks(fam, D, M, L); }
    let T = 0;
    if fam == "PH" {
        let tt = s.take_tok("T");
        if tt == () { refuse("invalid", `both ends stepped: the right step length T follows M, e.g. ${ex}`); }
        T = to_i(tt);
        if !(pn("step_f_min") <= T && T <= fmax) { let t = g(fmax); refuse("invalid", `T${T} is outside 2 <= T <= P x 4 = ${t} (p.${page})`); }
    }
    s.F = F; s.P = P; s.T = T; s.ymax = row.ymax;
    let total = L + F + T;
    if total > row.ymax.to_float() { let gt = g(total); let gy = g(row.ymax); refuse("invalid", `overall length (Y) = ${gt} mm exceeds the maximum ${gy} mm for D${D} (p.${page} table)`); }
    s.tapped = true; s.M = M;
    s.taps.push(#{ M: M, face: -F.to_float(), dir: 1, depth: depth, label: "left" });
    if fam == "PH" { s.taps.push(#{ M: M, face: L + T, dir: -1, depth: depth, label: "right" }); }
    s.md = md;
    s
}
// ---- alterations ------------------------------------------------------------------------------------
fn tok_is(t, name) { t != () && t[0] == name && t[1] != () }
fn tok_int(t) { to_i(t[1]) }
fn check_token(s, rt, key, allowed, union, seen, al) {
    if key == "A" || key == "E" || key == "X" || !has(union, key) { refuse("invalid", `unknown or unsupported alteration '${rt}' (supported here: ${al})`); }
    let who = s.typ + s.tt; let pg = s.page;
    if !has(allowed, key) { refuse("invalid", `alteration ${key} is not offered for ${who} (p.${pg}); offered: ${al}`); }
    if has(seen, key) { refuse("invalid", `alteration ${key} given twice`); }
}
fn alterations(s) {
    let allowed = alts_of(s.fam); let union = alt_union();
    let al = join(sorted_list(allowed), ", ");
    let seen = [];
    let toks = s.toks; let i = 0;
    while i < toks.len() {
        let t = toks[i]; i += 1;
        let rt = raw(#{ n: t[0], a: t[1] });
        let key = lead_letters(rt);
        check_token(s, rt, key, allowed, union, seen, al);
        let r = alteration_one(s, t, rt, key, toks, i, al);
        s = r.s; i = r.i;
        seen.push(key);
    }
    s.seen = seen;
    s
}
fn alteration_one(s, t, rt, key, toks, i, al) {   // -> #{ s, i }: the option and the tokens it takes along
    let nxt = if i < toks.len() { toks[i] } else { () };
    let nxt2 = if i + 1 < toks.len() { toks[i + 1] } else { () };
    if rt == "LKC" { s.lkc = true; return #{ s: s, i: i }; }
    if key == "SC" && tok_is(t, "SC") { s.sc = tok_int(t); return #{ s: s, i: i }; }
    if key == "SX" && tok_is(t, "SX") { s.sx = tok_int(t); return #{ s: s, i: i }; }
    if key == "WSC" && tok_is(t, "WSC") { return alt_wsc(s, t, nxt, i); }
    if key == "FC" && tok_is(t, "FC") { return alt_fc(s, t, nxt, i); }
    if key == "WFC" && tok_is(t, "WFC") { return alt_wfc(s, t, nxt, nxt2, i); }
    if key == "LFC" && tok_is(t, "LFC") { return alt_lfc(s, t, nxt, i); }
    refuse("invalid", `unknown or unsupported alteration '${rt}' (supported: ${al})`);
}
fn alt_wsc(s, t, nxt, i) {
    s.wsc = tok_int(t);
    if !tok_is(nxt, "X") { refuse("invalid", "WSC needs the distance between the two flats: WSC12-X8"); }
    s.ext.X = tok_int(nxt);
    #{ s: s, i: i + 1 }
}
fn alt_fc(s, t, nxt, i) {
    s.fc = tok_int(t);
    if !(tok_is(nxt, "A") || tok_is(nxt, "E")) { refuse("invalid", "FC needs its position from an end: FC10-A8 (from the left end) or FC10-E8 (from the right end)"); }
    s.ext.FC = [nxt[0], tok_int(nxt)];
    if s.fam == "PG" && nxt[0] != "E" { refuse("invalid", "FC on a stepped shaft is given from the right end only: FC10-E8 (p.437)"); }
    #{ s: s, i: i + 1 }
}
fn alt_wfc(s, t, nxt, nxt2, i) {
    s.wfc = tok_int(t);
    if !(tok_is(nxt, "A") && tok_is(nxt2, "E")) { refuse("invalid", "WFC needs both positions: WFC10-A8-E20"); }
    s.ext.WFC = [tok_int(nxt), tok_int(nxt2)];
    #{ s: s, i: i + 2 }
}
fn alt_lfc(s, t, nxt, i) {
    s.lfc = tok_int(t);
    if !tok_is(nxt, "A") { refuse("invalid", "LFC needs its distance from the step end: LFC10-A0 (p.437)"); }
    s.ext.LFC = tok_int(nxt);
    #{ s: s, i: i + 1 }
}
fn wrench_checks(s) {
    let D = s.D; let L = s.L; let page = s.page; let gl = g(L);
    let fam = s.fam;
    if s.sc != () {
        let l1 = table("wrench", D, "l1");
        let t = s.sc + l1;
        if s.sc != 0 && s.sc < 1 { refuse("invalid", "SC = 0 or SC >= 1"); }
        if t.to_float() > L { refuse("invalid", `SC + l1 = ${t} exceeds L = ${gl} (p.${page}: SC + l1 <= L)`); }
        s.flats.push(#{ kind: "sc", x0: s.sc, x1: t, axis: "Y", across: table("wrench", D, "W"), r: D.to_float() / 2.0 });
    }
    if s.sx != () {
        let W = table("wrench", D, "W"); let l1 = table("wrench", D, "l1");
        if s.sc == () { refuse("invalid", "SX adds a second set of wrench flats and needs SC"); }
        let t = s.sc + s.sx + 2 * l1;
        if t.to_float() >= L { refuse("invalid", `SC + SX + 2 x l1 = ${t} must be less than L = ${gl} (p.${page})`); }
        s.flats.push(#{ kind: "sc", x0: s.sc + l1 + s.sx, x1: s.sc + 2 * l1 + s.sx, axis: "Z", across: W, r: D.to_float() / 2.0 });
        s.notes.push("SX: the catalogue says the second set of flats is not coplanar with the first; drawn turned 90 degrees (angle not given)");
    }
    if s.wsc != () {
        let W = table("wrench", D, "W"); let l1 = table("wrench", D, "l1"); let X = s.ext.X;
        if (s.wsc != 0 && s.wsc < 1) || (X != 0 && X < 1) { refuse("invalid", "WSC(X) = 0 or WSC(X) >= 1"); }
        let t = s.wsc + X + 2 * l1;
        if t.to_float() >= L { refuse("invalid", `WSC + X + 2 x l1 = ${t} must be less than L = ${gl} (p.${page})`); }
        s.flats.push(#{ kind: "sc", x0: s.wsc, x1: s.wsc + l1, axis: "Y", across: W, r: D.to_float() / 2.0 });
        s.flats.push(#{ kind: "sc", x0: s.wsc + l1 + X, x1: s.wsc + 2 * l1 + X, axis: "Z", across: W, r: D.to_float() / 2.0 });
        s.notes.push("WSC: the catalogue says the two flats are not coplanar; the second is turned 90 degrees (angle not given)");
    }
    s
}
fn flat_depth(D) {
    if D <= 5 { pn("flat_depth_le_5") } else if D <= 16 { pn("flat_depth_le_16") } else if D <= 40 { pn("flat_depth_le_40") } else { pn("flat_depth_gt_40") }
}
fn fc_len_ok(s, n, doubled) {
    let D = s.D; let L = s.L; let page = s.page;
    if D <= 30 && n > 5 * D { let t = 5 * D; refuse("invalid", `FC / WFC = ${n} exceeds 5 x D = ${t} (D <= 30, p.${page})`); }
    if D >= 35 && n < 3 * D { let t = 3 * D; refuse("invalid", `FC / WFC = ${n} below 3 x D = ${t} (D >= 35, as printed on p.${page})`); }
    let nn = if doubled { 2 * n } else { n };
    if 1.5 * D < n && nn.to_float() > L / 2.0 { refuse("invalid", `FC / WFC = ${n}: when 1.5 x D < FC, FC <= L/2 (WFC: 2 x WFC <= L/2) (p.${page})`); }
}
fn flat_surfaces(s) {
    let D = s.D; let L = s.L; let H = flat_depth(D); let r = D.to_float() / 2.0;
    if s.fc != () {
        fc_len_ok(s, s.fc, false);
        let side = s.ext.FC[0]; let a = s.ext.FC[1];
        if a != 0 && a < 2 { refuse("invalid", "A(E) = 0 or A(E) >= 2"); }
        let x0 = if side == "A" { a.to_float() } else { L - a - s.fc };
        if x0 < 0.0 || x0 + s.fc > L { refuse("invalid", "the flat does not fit in the length"); }
        s.flats.push(#{ kind: "fc", x0: x0, x1: x0 + s.fc, axis: "Y", depth: H, r: r });
    }
    if s.wfc != () {
        fc_len_ok(s, s.wfc, true);
        let a = s.ext.WFC[0]; let e = s.ext.WFC[1];
        if (a != 0 && a < 2) || (e != 0 && e < 2) { refuse("invalid", "A(E) = 0 or A(E) >= 2"); }
        let x0 = a; let x1 = L - e - s.wfc;
        if (x0 + s.wfc).to_float() > x1 { refuse("invalid", "the two flats overlap"); }
        s.flats.push(#{ kind: "fc", x0: x0, x1: x0 + s.wfc, axis: "Y", depth: H, r: r });
        s.flats.push(#{ kind: "fc", x0: x1, x1: x1 + s.wfc, axis: "Z", depth: H, r: r });
        s.notes.push("WFC: the catalogue says the two flats are not coplanar; the second is turned 90 degrees (angle not given)");
    }
    if s.lfc != () {
        let a = s.ext.LFC;
        if s.lfc < 1 { refuse("invalid", "LFC must be at least 1 mm"); }
        if s.lfc + a > s.F { let t = s.lfc + a; let gf = g(s.F); refuse("invalid", `LFC + A = ${t} exceeds the step length F = ${gf} (p.437: LFC + A <= F)`); }
        if s.P.to_float() - s.M < 1.0 { let gp = g(s.P); let gm = g(s.M); refuse("invalid", `LFC needs P - M >= 1 (p.437), got P${gp} M${gm}`); }
        let depth = if s.P <= 16 { pn("lfc_depth_le_16") } else { pn("lfc_depth_gt_16") };
        s.flats.push(#{ kind: "lfc", x0: -s.F + a, x1: -s.F + a + s.lfc, axis: "Y", depth: depth, r: s.P.to_float() / 2.0 });
    }
    s
}
fn cmp_span(a, b) {
    if a[0] != b[0] { return if a[0] < b[0] { -1 } else { 1 }; }
    if a[1] != b[1] { return if a[1] < b[1] { -1 } else { 1 }; }
    if a[2] == b[2] { return 0; }
    if a[2] < b[2] { -1 } else { 1 }
}
fn span_list(s) {                 // (x0, x1, kind) of every machined part but the set screw flat on the step
    let base_flats = s.fam == "C" || s.fam == "Z" || s.fam == "PG" || s.fam == "PH";
    let spans = [];
    for k in 0..s.flats.len() {
        let f = s.flats[k];
        if f.kind == "lfc" { continue; }
        let tag = "alt";
        if base_flats && f.kind == "sc" && k == 0 { tag = "base"; }
        spans.push([f.x0.to_float(), f.x1.to_float(), tag]);
    }
    for t in s.taps {
        let e = t.face + t.dir * t.depth;
        let a0 = e; let a1 = t.face;
        if t.face < e { a0 = t.face; a1 = e; }
        if a0 < 0.0 { a0 = 0.0; }
        if a1 > s.L { a1 = s.L; }
        if a1 > a0 { spans.push([a0, a1, "tap"]); }
    }
    spans
}
fn spacing(s) {                   // machined parts spaced by more than 2 mm (p.432 note)
    let spans = span_list(s);
    spans.sort(|a, b| cmp_span(a, b));
    let page = s.page;
    for i in 0..(spans.len() - 1) {
        let a = spans[i]; let b = spans[i + 1];
        let both_tap = a[2] == "tap" && b[2] == "tap";
        let tap_base = (a[2] == "tap" && b[2] == "base") || (a[2] == "base" && b[2] == "tap");
        if both_tap || tap_base { continue; }
        if b[0] - a[1] <= 2.0 { refuse("invalid", `machined parts need more than 2 mm between them (p.${page} note)`); }
    }
}
fn required_flat(s) {             // the wrench flat the ordering code of C, Z, PG, PH requires
    let fam = s.fam; let typ = s.typ; let D = s.D; let page = s.page;
    if fam == "Z" && s.sc == () && s.wsc == () {
        refuse("invalid", `${typ}${D} needs its wrench flat after N: SC<n> (one set) or WSC<n>-X<m> (two sets) (p.${page})`);
    }
    if (fam == "C" || fam == "PG" || fam == "PH") && s.sc == () {
        refuse("invalid", `${typ}${D} needs its wrench flat position SC after the thread, e.g. ...-SC0 (p.${page} ordering example)`);
    }
}
fn lkc_check(s) {                 // -> s with the length tolerance of LKC, or the 1 mm step check
    let D = s.D; let L = s.L; let gl = g(L);
    if !s.lkc {
        if (L - L.round()).abs() > 0.000000001 { refuse("invalid", `length ${gl} mm: lengths are in 1 mm steps; 0.1 mm steps need the LKC alteration`); }
        return s;
    }
    if s.fam == "PG" && (D - s.P) <= pn("lkc_min_d_minus_p") { let gp = g(s.P); refuse("invalid", `LKC is not applicable when D - P <= 2 (D${D}, P${gp}; p.437)`); }
    if (L * 10.0 - (L * 10.0).round()).abs() > 0.000000001 { refuse("invalid", `length ${gl} is not a multiple of 0.1 mm`); }
    s.length_tol = if L < 200.0 { pn("lkc_tol_lt_200") } else if L < 500.0 { pn("lkc_tol_lt_500") } else { pn("lkc_tol_ge_500") };
    s
}
fn length_checks(s) {             // -> s (the length tolerance of LKC)
    required_flat(s);
    s = lkc_check(s);
    let D = s.D; let L = s.L; let fam = s.fam; let page = s.page; let gl = g(L);
    if !(s.lrange[0] <= L && L <= s.lrange[1]) { let a = s.lrange[0]; let b = s.lrange[1]; refuse("invalid", `length ${gl} mm outside ${a}-${b} mm for ${s.typ}${s.tt}${D} (p.${page} table)`); }
    if (fam == "T" || fam == "C") && 2.0 * s.M > L { refuse("invalid", "thread depth exceeds the length"); }
    if has(s.seen, "SC") && has(s.seen, "WSC") { refuse("invalid", `SC cannot be combined with WSC (p.${page})`); }
    if has(s.seen, "FC") && has(s.seen, "WFC") { refuse("invalid", `FC cannot be combined with WFC (p.${page})`); }
    if (has(s.seen, "SC") || has(s.seen, "WSC")) && D < 6 { refuse("invalid", "SC / WSC apply to D = 6 or more (p.432)"); }
    s
}
fn parse_code(fields) {
    let name = "E-" + fields.type;
    let r = resolve_type(name);
    let s = new_state(name, r.typ, r.tflag, fields);
    if s.fam == "T" || s.fam == "C" || s.fam == "Z" || s.fam == "W" { s = tap_family(s); }
    else if s.fam == "PG" || s.fam == "PH" { s = stepped_family(s); }
    else if peek_tok(s, "M") { let t = s.typ; refuse("invalid", `${t} is the plain shaft; a thread needs the tapped type ${t}T (or C, Z, W)`); }
    s = alterations(s);
    s = length_checks(s);
    s = wrench_checks(s);
    s = flat_surfaces(s);
    spacing(s);
    s
}

// ---- resolve: fields -> the configuration row and the parameter values -------------------------------------
fn mm(x) { g(x) + " mm" }
fn flag(b) { if b { "1" } else { "0" } }
fn make_parameters(s) {
    let pp = s.D; if s.F > 0 || s.T > 0 { pp = s.P; }
    let p = #{ part_type: s.name, L: mm(s.L), lkc: flag(s.lkc), F: mm(s.F), P: mm(pp), T: mm(s.T), m_left: "0 mm", m_right: "0 mm", md: flag(s.md),
               sc: "-1 mm", sx: "-1 mm", wsc: "-1 mm", xw: "0 mm", fc: "-1 mm", fa: "-1 mm", fe: "-1 mm", wfc: "-1 mm", wa: "-1 mm", we: "-1 mm",
               lfc: "-1 mm", la: "-1 mm", lfd: "1 mm" };
    for t in s.taps { if t.label == "left" { p.m_left = mm(t.M); } else { p.m_right = mm(t.M); } }
    flat_parameters(s, p)
}
fn flat_parameters(s, p) {
    if s.sc != () { p.sc = mm(s.sc); }
    if s.sx != () { p.sx = mm(s.sx); }
    if s.wsc != () { p.wsc = mm(s.wsc); p.xw = mm(s.ext.X); }
    let ext = s.ext;
    if s.fc != () {
        let side = ext.FC[0]; let a = mm(ext.FC[1]);
        p.fc = mm(s.fc);
        if side == "A" { p.fa = a; } else { p.fe = a; }
    }
    if s.wfc != () { let w = ext.WFC; p.wfc = mm(s.wfc); p.wa = mm(w[0]); p.we = mm(w[1]); }
    if s.lfc != () {
        p.lfc = mm(s.lfc); p.la = mm(s.ext.LFC);
        let d = pn("lfc_depth_gt_16"); if s.P <= 16 { d = pn("lfc_depth_le_16"); }
        p.lfd = mm(d);
    }
    p
}
fn describe(s) {
    let nm = s.typ + s.tt + s.D;
    let t0 = fmt3(s.tol[0]); let t1 = fmt3(s.tol[1]);
    let d = `MISUMI linear shaft ${nm}, L=${g(s.L)} mm, D tolerance ${s.cls} (${t0}/${t1} mm, drawn at the nominal diameter), `;
    d += s.material + ", " + s.hardness;
    if s.surface != "-" { d += ", " + s.surface; }
    let gp = g(s.P);
    if s.F > 0 { d += `, left end stepped F=${g(s.F)} mm to P${gp} g7`; }
    if s.T > 0 { d += `, right end stepped T=${g(s.T)} mm to P${gp} g7`; }
    for t in s.taps { d += `, ${t.label} end tapped M${g(t.M)} depth ${g(t.depth)}`; }
    if s.length_tol > 0.0 { d += `, length tolerance L+-${g(s.length_tol)} (LKC)`; }
    d + ". Generated from the published catalogue dimensions; no end chamfer (not given in the catalogue)."
}
fn resolve(fields) {
    if fields.raw != () { usage(fields.raw); }
    let s = parse_code(fields);
    let desc = describe(s);
    let material = `${s.material}; ${s.hardness}`;
    if s.surface != "-" { material += `; ${s.surface}`; }
    let pnum = code_template(fields);
    #{ configuration: s.D.to_string(), parameters: make_parameters(s),
       properties: #{ part_number: pnum, description: desc, material: material, type: s.typ, type_name: s.name, family: s.fam, tolerance_class: s.cls, tol: s.tol,
                      hardness: s.hardness, surface: s.surface, base_material: s.material, tapped: s.tapped, M: s.M, lkc: s.lkc, length_tol: s.length_tol,
                      F: s.F, P: s.P, T: s.T, ymax: s.ymax, md: s.md, taps: s.taps, flats: s.flats, notes: s.notes } }
}

// parameters -> fields (generator.code, bill of materials): canonical order of the options
fn val(p) { parse_float(p.split(" ")[0]) }
fn ival(p) { val(p).to_int().to_string() }
fn gv(p) { g(val(p)) }
fn positional_opts(p, fam) {      // F P M|MD [N] [T]
    let o = [];
    if fam == "PG" || fam == "PH" { o.push(["F", ival(p.F)]); o.push(["P", ival(p.P)]); }
    if fam == "straight" { return o; }
    let mname = "M"; if p.md == "1" { mname = "MD"; }
    o.push([mname, gv(p.m_left)]);
    if fam == "Z" || fam == "W" { o.push(["N", gv(p.m_right)]); }
    if fam == "PH" { o.push(["T", ival(p.T)]); }
    o
}
fn opt(o, cond, name, arg) { if cond { o.push([name, arg]); } o }
fn flat_opts(p) {                 // flat: the sandbox allows only a few nesting levels per function
    let o = [];
    let has_fc = val(p.fc) >= 0.0;
    o = opt(o, p.lkc == "1", "LKC", ());
    o = opt(o, val(p.sc) >= 0.0, "SC", ival(p.sc));
    o = opt(o, val(p.sx) >= 0.0, "SX", ival(p.sx));
    o = opt(o, val(p.wsc) >= 0.0, "WSC", ival(p.wsc));
    o = opt(o, val(p.wsc) >= 0.0, "X", ival(p.xw));
    o = opt(o, has_fc, "FC", ival(p.fc));
    o = opt(o, has_fc && val(p.fa) >= 0.0, "A", ival(p.fa));
    o = opt(o, has_fc && val(p.fa) < 0.0, "E", ival(p.fe));
    o = opt(o, val(p.wfc) >= 0.0, "WFC", ival(p.wfc));
    o = opt(o, val(p.wfc) >= 0.0, "A", ival(p.wa));
    o = opt(o, val(p.wfc) >= 0.0, "E", ival(p.we));
    o = opt(o, val(p.lfc) >= 0.0, "LFC", ival(p.lfc));
    o = opt(o, val(p.lfc) >= 0.0, "A", ival(p.la));
    o
}
fn fields(configuration, parameters) {
    let p = parameters; let name = p.part_type;
    let row = table("types", name);
    let fam = "T"; if row != () { fam = row.family; }
    let o = positional_opts(p, fam);
    for x in flat_opts(p) { o.push(x); }
    #{ type: name.sub_string(2), d: to_i(configuration), length: val(p.L), opts: option_text(o) }
}
