// Stand-in host for a generator's generator.rhai until SolidCraft ships generator.parse (docs/formats/generator.md, section 5):
// the real Rhai engine with the documented sandbox limits and the three registered functions
//   table(name, key[, column])   one row (map) / cell (text) of tables/<name>.csv by first-column key; unknown key -> ()
//   refuse(kind, message)        stop with a refusal
//   code_template(fields)        the printed code: asks `python3 runtime/fieldtemplate.py print` (the template printer stand-in)
// usage: rhai-run <generator dir> <function> '<json argument>' ...   prints {"ok": <value>} or {"refusal": {kind, message}}
use rhai::{serde::{from_dynamic, to_dynamic}, Dynamic, Engine, EvalAltResult, Map, Position, Scope};
use std::{collections::HashMap, path::Path, process::Command, rc::Rc};

fn load_tables(dir: &Path) -> HashMap<String, Vec<HashMap<String, String>>> {
    let mut out = HashMap::new();
    if let Ok(rd) = std::fs::read_dir(dir.join("tables")) {
        for e in rd.flatten() {
            let p = e.path();
            if p.extension().map(|x| x == "csv").unwrap_or(false) {
                let mut r = csv::Reader::from_path(&p).expect("csv");
                let head: Vec<String> = r.headers().unwrap().iter().map(String::from).collect();
                let rows = r.records().map(|rec| {
                    let rec = rec.unwrap();
                    head.iter().cloned().zip(rec.iter().map(String::from)).collect::<HashMap<_, _>>()
                }).collect();
                out.insert(p.file_stem().unwrap().to_string_lossy().to_string(), rows);
            }
        }
    }
    out
}

fn find<'a>(t: &'a HashMap<String, Vec<HashMap<String, String>>>, name: &str, key: &str) -> Option<(&'a HashMap<String, String>, String)> {
    let rows = t.get(name)?;
    // the first column of the file is the key
    for r in rows {
        let k = r.get("key").or_else(|| r.get("name"))?;
        if k == key { return Some((r, k.clone())); }
    }
    None
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let dir = Path::new(&a[1]).to_path_buf();
    let tables = Rc::new(load_tables(&dir));
    let mut engine = Engine::new();
    engine.set_max_operations(100_000);
    engine.set_max_call_levels(16);
    engine.set_max_expr_depths(32, 16);
    engine.set_max_string_size(4096);
    engine.set_max_array_size(1024);
    engine.set_max_map_size(256);
    engine.disable_symbol("eval");
    engine.set_module_resolver(rhai::module_resolvers::DummyModuleResolver::new());
    let t2 = tables.clone();
    engine.register_fn("table", move |name: &str, key: &str, col: &str| -> Dynamic {
        match find(&t2, name, key).and_then(|(r, _)| r.get(col).cloned()) {
            Some(v) if !v.is_empty() => Dynamic::from(v),
            _ => Dynamic::UNIT,
        }
    });
    let t3 = tables.clone();
    engine.register_fn("table", move |name: &str, key: &str| -> Dynamic {
        match find(&t3, name, key) {
            Some((r, _)) => { let mut m = Map::new(); for (k, v) in r { m.insert(k.as_str().into(), Dynamic::from(v.clone())); } Dynamic::from_map(m) }
            None => Dynamic::UNIT,
        }
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
    let ast = engine.compile_file(dir.join("generator.rhai")).expect("compile generator.rhai");
    let mut scope = Scope::new();
    let args: Vec<Dynamic> = a[3..].iter().map(|s| to_dynamic(serde_json::from_str::<serde_json::Value>(s).unwrap()).unwrap()).collect();
    let r: Result<Dynamic, Box<EvalAltResult>> = engine.call_fn_raw(&mut scope, &ast, true, true, &a[2], None, args);
    match r {
        Ok(v) => { let j: serde_json::Value = from_dynamic(&v).unwrap(); println!("{}", serde_json::json!({"ok": j})); }
        Err(mut e) => {
            loop {
                match *e {
                    EvalAltResult::ErrorInFunctionCall(_, _, inner, _) => e = inner,
                    EvalAltResult::ErrorRuntime(d, _) if d.is_map() => {
                        let j: serde_json::Value = from_dynamic(&d).unwrap();
                        println!("{}", serde_json::json!({"refusal": j})); return;
                    }
                    other => { println!("{}", serde_json::json!({"script_error": other.to_string()})); std::process::exit(2); }
                }
            }
        }
    }
}
