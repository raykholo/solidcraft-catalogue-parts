"""Optional link-parameter proof, run after the legacy harness and conversion.

Only command-catalogue support enables this proof. Existing release results are
left untouched. Fixtures select ordering codes; all geometry comes from the
package and the Python generator, never from a CAD reference.
"""
import json
import re
import tempfile
import tomllib
from pathlib import Path

from runtime import fieldtemplate, registry, sc
from runtime.parametric import cli, measure, rhai, supports_link_parameters


def resolve(package, code):
    """Resolve a fixture through the same field templates and Rhai as the harness."""
    matched = fieldtemplate.load(package).match(code.strip().upper())
    if matched is None:
        raise ValueError(f"link fixture matches no template: {code}")
    result = rhai(package, "resolve", {k: v for k, v in matched[1].items() if v is not None})
    if not result.get("ok"):
        raise ValueError(f"link fixture refused: {code}: {result}")
    return result["value"]


def direct(generator, code, work, tag, options=None):
    """Build and measure the reference code directly with the Python generator."""
    _, commands = generator.build(code, **(options or {}))
    path, _ = sc.run_script(commands, str(work), tag)
    return measure(path, work, tag + ".measure", threads=False, include_threads=False)


def link_rows(generator, package, model, fixture, work):
    """Insert overrides, edit that saved link, and require a parameter-naming refusal."""
    parameter = fixture["parameter"]
    insert_code, change_code = fixture["insert"], fixture["change"]
    inserted, changed = resolve(package, insert_code), resolve(package, change_code)
    initial = inserted["parameters"][parameter]
    updated = changed["parameters"][parameter]
    if initial == updated:
        raise ValueError(f"link fixture must change {parameter}")
    if inserted["configuration"] != changed["configuration"]:
        raise ValueError("link fixture must keep its configuration row")
    host, edited = work / "insert.sc", work / "edited.sc"
    rows = []
    insert_row = {"label": f"link: insert with {parameter}={initial}",
                  "direct": direct(generator, insert_code, work, "direct-insert", fixture.get("build_options"))}
    replies, error = cli([{"command": "component.insert_design", "params": {
        "path": str(model.resolve()), "configuration": inserted["configuration"],
        "parameters": inserted["parameters"]}}], save=host)
    insert_row["changed"] = {"error": error} if error else measure(host, work, "insert.measure", threads=False, include_threads=False)
    rows.append(insert_row)
    edit_row = {"label": f"link: set {parameter}={updated}",
                "direct": direct(generator, change_code, work, "direct-change", fixture.get("build_options"))}
    refusal_row = {"label": "link: out-of-range refused", "direct": {"refused": True}}
    if error:
        edit_row["changed"] = {"error": "insert failed"}
        refusal_row["changed"] = {"refused": False, "message": "insert failed", "parameter": parameter}
        return rows + [edit_row, refusal_row]
    component = replies[0]["component"]
    # Use the returned id, and retain every other override through merge.
    overrides = {k: v for k, v in changed["parameters"].items() if inserted["parameters"].get(k) != v}
    _, error = cli([{"command": "component.set_link_parameters", "params": {
        "component": component, "parameters": overrides, "merge": True}}], src=host, save=edited)
    edit_row["changed"] = {"error": error} if error else measure(edited, work, "change.measure", threads=False, include_threads=False)
    rows.append(edit_row)
    _, refusal = cli([{"command": "component.set_link_parameters", "params": {
        "component": component, "parameters": {parameter: fixture["outside"]}, "merge": True}}], src=host)
    message = refusal if isinstance(refusal, str) else json.dumps(refusal) if refusal else ""
    # Do not bless a topology failure or an unknown command as a range refusal.
    mentions = bool(re.search(r"(?<!\w)" + re.escape(parameter) + r"(?!\w)", message, re.IGNORECASE))
    limit = bool(re.search(r"range|allow|restrict|limit|rule", message, re.IGNORECASE))
    refusal_row["changed"] = {"refused": bool(refusal and mentions and limit),
                              "parameter": parameter, "message": message}
    rows.append(refusal_row)
    return rows


def check_links(generator_dir, outdir):
    """Append optional link rows to faithfulness.json; unsupported builds keep it unchanged."""
    generator_dir, outdir = Path(generator_dir).resolve(), Path(outdir).resolve()
    fixture_path = generator_dir / "parametric" / "link_checks.json"
    if not fixture_path.exists():
        return
    if not supports_link_parameters():
        return
    fixtures = json.loads(fixture_path.read_text())
    generator = registry.Generator(generator_dir)
    package = generator_dir / "parametric" / fixtures["package"]
    manifest = tomllib.loads((package / "generator.toml").read_text())
    result_path = outdir / "faithfulness.json"
    result = json.loads(result_path.read_text())
    for fixture in fixtures["checks"]:
        with tempfile.TemporaryDirectory() as temporary:
            try:
                rows = link_rows(generator, package, package / manifest["model"], fixture, Path(temporary))
            except Exception as error:
                rows = [{"label": f"link: {fixture['parameter']} checks", "direct": {"error": str(error)}, "changed": {"error": str(error)}}]
            result["rebuild"].extend(rows)
    result["blocked"] = [row for row in result["blocked"] if "free parameter values on an inserted link" not in row["what"]]
    result_path.write_text(json.dumps(result, indent=1))


if __name__ == "__main__":
    import sys
    check_links(sys.argv[1], sys.argv[2])
