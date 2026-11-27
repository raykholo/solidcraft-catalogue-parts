//! Evaluates a generator package's generator.rhai the way docs/formats/generator.md section 5 describes it, as a
//! stand-in for SolidCraft's sandbox until it ships: rhai-resolve PACKAGE_DIR resolve|describe < JSON arguments > JSON result.
//! Registered: table(name, key) / table(name, key, column) over tables/<name>.csv (unknown key -> ()), refuse(kind, message).
//! Limits as the doc: operations 100_000, call levels 16, expression depth 32 (functions 16), string 4096, array 1024, map 256.
use rhai::{Dynamic, Engine, EvalAltResult, Map, Scope, AST};
use std::{cell::RefCell, collections::HashMap, io::Read, rc::Rc};

type Tables = Rc<HashMap<String, Vec<(String, Map)>>>;

fn cell(v: &str) -> Dynamic {
    if let Ok(i) = v.parse::<i64>() { return i.into(); }
    if let Ok(f) = v.parse::<f64>() { return f.into(); }
    v.to_string().into()
}

fn load_tables(dir: &std::path::Path) -> HashMap<String, Vec<(String, Map)>> {
    let mut out = HashMap::new();
    if let Ok(rd) = std::fs::read_dir(dir.join("tables")) {
        for e in rd.flatten() {
            let p = e.path();
            if p.extension().and_then(|x| x.to_str()) != Some("csv") { continue; }
            let name = p.file_stem().unwrap().to_string_lossy().to_string();
            let mut rdr = csv::Reader::from_path(&p).expect("csv");
            let head: Vec<String> = rdr.headers().unwrap().iter().map(|s| s.to_string()).collect();
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

fn find(t: &Tables, name: &str, key: &str, head: &str) -> Option<Map> {
    let _ = head;
    t.get(name)?.iter().find(|(k, _)| k == key).map(|(_, m)| m.clone())
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let dir = std::path::PathBuf::from(&args[1]);
    let func = args.get(2).map(String::as_str).unwrap_or("resolve");
    let mut input = String::new();
    std::io::stdin().read_to_string(&mut input).unwrap();
    let arg: serde_json::Value = serde_json::from_str(&input).unwrap();
    let tables: Tables = Rc::new(load_tables(&dir));
    let mut engine = Engine::new();
    engine.set_max_operations(100_000);
    engine.set_max_call_levels(16);
    engine.set_max_expr_depths(32, 16);
    engine.set_max_string_size(4096);
    engine.set_max_array_size(1024);
    engine.set_max_map_size(256);
    let t1 = tables.clone();
    engine.register_fn("table", move |name: &str, key: &str| -> Dynamic {
        find(&t1, name, key, "").map(Dynamic::from_map).unwrap_or(Dynamic::UNIT)
    });
    let t2 = tables.clone();
    engine.register_fn("table", move |name: &str, key: &str, col: &str| -> Dynamic {
        find(&t2, name, key, "").and_then(|m| m.get(col).cloned()).unwrap_or(Dynamic::UNIT)
    });
    // table keys given as numbers (table("rails", 12))
    let t3 = tables.clone();
    engine.register_fn("table", move |name: &str, key: i64| -> Dynamic {
        find(&t3, name, &key.to_string(), "").map(Dynamic::from_map).unwrap_or(Dynamic::UNIT)
    });
    engine.register_fn("refuse", |kind: &str, message: &str| -> Result<(), Box<EvalAltResult>> {
        let mut m = Map::new();
        m.insert("kind".into(), kind.to_string().into());
        m.insert("message".into(), message.to_string().into());
        Err(Box::new(EvalAltResult::ErrorRuntime(Dynamic::from_map(m), rhai::Position::NONE)))
    });
    let ast: AST = engine.compile(std::fs::read_to_string(dir.join("generator.rhai")).unwrap()).unwrap_or_else(|e| { println!("{}", serde_json::json!({"ok": false, "reason": "script_error", "message": e.to_string()})); std::process::exit(0) });
    let dynarg: Dynamic = rhai::serde::to_dynamic(&arg).unwrap();
    let res: Result<Dynamic, _> = engine.call_fn(&mut Scope::new(), &ast, func, (dynarg,));
    let _ = RefCell::new(0);
    match res {
        Ok(v) => {
            let j: serde_json::Value = rhai::serde::from_dynamic(&v).unwrap();
            println!("{}", serde_json::json!({"ok": true, "value": j}));
        }
        Err(e) => match *e {
            EvalAltResult::ErrorRuntime(d, _) if d.is_map() => {
                let j: serde_json::Value = rhai::serde::from_dynamic(&d).unwrap();
                println!("{}", serde_json::json!({"ok": false, "reason": j["kind"], "message": j["message"]}));
            }
            other => println!("{}", serde_json::json!({"ok": false, "reason": "script_error", "message": other.to_string()})),
        },
    }
}
