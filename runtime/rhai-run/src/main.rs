// Stand-in host for a generator's generator.rhai until SolidCraft ships generator.parse (docs/formats/generator.md, section 5):
// the real Rhai engine with the documented sandbox limits and the three registered functions
//   table(name, key[, column])   one row (map) / cell (text) of tables/<name>.csv by first-column key; unknown key -> ()
//   refuse(kind, message)        stop with a refusal
//   code_template(fields)        the printed code: asks `python3 runtime/fieldtemplate.py print` (the template printer stand-in)
// usage: rhai-run <generator dir> <function> ['<json argument>' ...]   (no argument on the command line: one JSON argument is read from stdin)
// prints {"ok": true, "value": ...} or {"ok": false, "reason": "invalid" | "not_modelled" | ..., "message": ...} (reason script_error for a script fault)
// Shared by every generator's harness (MISUMI HFS, HIWIN MG). Limits as the document: operations 100_000, call levels 16, expression depth 32
// (functions 16), string 4096, array 1024, map 256. Table cells are typed: whole numbers, decimals, else text.
use rhai::{serde::{from_dynamic, to_dynamic}, Dynamic, Engine, EvalAltResult, Map, Position, Scope};
use std::{collections::HashMap, io::Read, path::Path, process::Command, rc::Rc};

type Tables = Rc<HashMap<String, Vec<(String, Map)>>>;

fn cell(v: &str) -> Dynamic {
    if let Ok(i) = v.parse::<i64>() { return i.into(); }
    if let Ok(f) = v.parse::<f64>() { return f.into(); }
    v.to_string().into()
}

fn load_tables(dir: &Path) -> HashMap<String, Vec<(String, Map)>> {
    let mut out = HashMap::new();
    if let Ok(rd) = std::fs::read_dir(dir.join("tables")) {
        for e in rd.flatten() {
            let p = e.path();
            if p.extension().and_then(|x| x.to_str()) != Some("csv") { continue; }
            let name = p.file_stem().unwrap().to_string_lossy().to_string();
            let mut rdr = csv::Reader::from_path(&p).expect("csv");
            let head: Vec<String> = rdr.headers().unwrap().iter().map(String::from).collect();
            let mut rows = vec![];
            for rec in rdr.records().flatten() {
                let mut m = Map::new();
                for (h, v) in head.iter().zip(rec.iter()) { m.insert(h.as_str().into(), cell(v)); }
                rows.push((rec.get(0).unwrap_or("").to_string(), m));
            }
            out.insert(name, rows);
        }
    }
    out
}

fn find(t: &Tables, name: &str, key: &str) -> Option<Map> {
    t.get(name)?.iter().find(|(k, _)| k == key).map(|(_, m)| m.clone())
}

fn fail(reason: &str, message: String) -> ! {
    println!("{}", serde_json::json!({"ok": false, "reason": reason, "message": message}));
    std::process::exit(0)
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let dir = Path::new(&a[1]).to_path_buf();
    let func = a.get(2).map(String::as_str).unwrap_or("resolve").to_string();
    let json_args: Vec<String> = if a.len() > 3 { a[3..].to_vec() } else {
        let mut input = String::new();
        std::io::stdin().read_to_string(&mut input).unwrap();
        vec![input]
    };
    let tables: Tables = Rc::new(load_tables(&dir));
    let mut engine = Engine::new();
    engine.set_max_operations(100_000);
    engine.set_max_call_levels(16);
    engine.set_max_expr_depths(32, 16);
    engine.set_max_string_size(4096);
    engine.set_max_array_size(1024);
    engine.set_max_map_size(256);
    engine.disable_symbol("eval");
    engine.set_module_resolver(rhai::module_resolvers::DummyModuleResolver::new());
    let t1 = tables.clone();
    engine.register_fn("table", move |name: &str, key: &str| -> Dynamic {
        find(&t1, name, key).map(Dynamic::from_map).unwrap_or(Dynamic::UNIT)
    });
    let t2 = tables.clone();
    engine.register_fn("table", move |name: &str, key: &str, col: &str| -> Dynamic {
        find(&t2, name, key).and_then(|m| m.get(col).cloned()).unwrap_or(Dynamic::UNIT)
    });
    let t3 = tables.clone();
    engine.register_fn("table", move |name: &str, key: i64| -> Dynamic {
        find(&t3, name, &key.to_string()).map(Dynamic::from_map).unwrap_or(Dynamic::UNIT)
    });
    let t4 = tables.clone();
    engine.register_fn("table", move |name: &str, key: i64, col: &str| -> Dynamic {
        find(&t4, name, &key.to_string()).and_then(|m| m.get(col).cloned()).unwrap_or(Dynamic::UNIT)
    });
    engine.register_fn("refuse", |kind: &str, msg: &str| -> Result<Dynamic, Box<EvalAltResult>> {
        let mut m = Map::new();
        m.insert("kind".into(), Dynamic::from(kind.to_string()));
        m.insert("message".into(), Dynamic::from(msg.to_string()));
        Err(Box::new(EvalAltResult::ErrorRuntime(Dynamic::from_map(m), Position::NONE)))
    });
    let printer_dir = dir.clone();
    engine.register_fn("code_template", move |fields: Map| -> Result<String, Box<EvalAltResult>> {
        let json: serde_json::Value = from_dynamic(&Dynamic::from_map(fields))?;
        let root = std::env::var("FT_ROOT").unwrap_or_else(|_| ".".into());
        let out = Command::new("python3").args(["-I", &format!("{root}/runtime/fieldtemplate.py"), "print", printer_dir.to_str().unwrap(), &json.to_string()]).output()
            .map_err(|e| e.to_string())?;
        Ok(String::from_utf8_lossy(&out.stdout).trim().to_string())
    });
    let src = std::fs::read_to_string(dir.join("generator.rhai")).unwrap();
    let ast = match engine.compile(src) { Ok(x) => x, Err(e) => fail("script_error", e.to_string()) };
    let args: Vec<Dynamic> = json_args.iter().map(|s| to_dynamic(serde_json::from_str::<serde_json::Value>(s).unwrap()).unwrap()).collect();
    let mut scope = Scope::new();
    #[allow(deprecated)]
    let r: Result<Dynamic, Box<EvalAltResult>> = engine.call_fn_raw(&mut scope, &ast, true, true, &func, None, args);
    match r {
        Ok(v) => { let j: serde_json::Value = from_dynamic(&v).unwrap(); println!("{}", serde_json::json!({"ok": true, "value": j})); }
        Err(mut e) => loop {
            match *e {
                EvalAltResult::ErrorInFunctionCall(_, _, inner, _) => e = inner,
                EvalAltResult::ErrorRuntime(d, _) if d.is_map() => {
                    let j: serde_json::Value = from_dynamic(&d).unwrap();
                    fail(j["kind"].as_str().unwrap_or("invalid"), j["message"].as_str().unwrap_or("").to_string());
                }
                other => fail("script_error", other.to_string()),
            }
        },
    }
}
