# MG rail set: generator package on SolidCraft 0.50.0 vs the Python generator

Measures: volume mm3 / area mm2 / bbox / faces f, bodies b. Parametric = config row + parameters on the single .sc, Python = build.py (appearance off, caps only as the same cylinders).

| code | python | parametric | spec check on the parametric part | spec check on the Python part (appearance off) | equal |
|---|---|---|---|---|---|
| MGN12H2R300Z0C | 40339.65 / 19943.89 / [0.000..300.000] x [-13.500..13.500] x [0.000..13.000] / 78f 3b | 40339.65 / 19943.89 / [0.000..300.000] x [-13.500..13.500] x [0.000..13.000] / 78f 3b | 29/31 FAIL: Block 1 length L; Block 2 length L | 29/31 FAIL: Block 1 length L; Block 2 length L | True |
| MGN12H2R300Z0C caps | 40746.80 / 20893.91 / [0.000..300.000] x [-13.500..13.500] x [0.000..13.000] / 114f 15b | 40746.80 / 20893.91 / [0.000..300.000] x [-13.500..13.500] x [0.000..13.000] / 114f 15b | 29/31 FAIL: Block 1 length L; Block 2 length L | 29/31 FAIL: Block 1 length L; Block 2 length L | True |
| MGN15H1R200Z0C | 41780.31 / 15983.95 / [0.000..200.000] x [-16.000..16.000] x [0.000..16.000] / 39f 2b | 41780.31 / 15983.95 / [0.000..200.000] x [-16.000..16.000] x [0.000..16.000] / 39f 2b | 22/23 FAIL: Block 1 length L | 22/23 FAIL: Block 1 length L | True |
| MGN15H1R200Z0C caps | 41949.95 / 16379.79 / [0.000..200.000] x [-16.000..16.000] x [0.000..16.000] / 54f 7b | 41949.95 / 16379.79 / [0.000..200.000] x [-16.000..16.000] x [0.000..16.000] / 54f 7b | 22/23 FAIL: Block 1 length L | 22/23 FAIL: Block 1 length L | True |
| MGN9C1R195ZFH | 12328.91 / 8520.93 / [0.000..195.000] x [-10.000..10.000] x [0.000..10.000] / 54f 2b | 12328.91 / 8520.93 / [0.000..195.000] x [-10.000..10.000] x [0.000..10.000] / 54f 2b | 22/23 FAIL: Block 1 length L | 22/23 FAIL: Block 1 length L | True |
| !MGN12H2R3000 | MGNR12 max single length is 2000 mm | REFUSED: MGNR12 max single length is 2000 mm | - | - | True |
| !MGN7C1R700 | MGNR7 max single length is 600 mm | REFUSED: MGNR7 max single length is 600 mm | - | - | True |

## Configuration row and parameters per code

- MGN12H2R300Z0C: row `H-12`, {'blocks': '2', 'length': '300 mm'}, template 0, printed `MGN12H2R300Z0C` round trip True
- MGN12H2R300Z0C caps: row `H-12`, {'blocks': '2', 'length': '300 mm'}, template 0, printed `MGN12H2R300Z0C` round trip True
- MGN15H1R200Z0C: row `H-15`, {'blocks': '1', 'length': '200 mm'}, template 0, printed `MGN15H1R200Z0C` round trip True
- MGN15H1R200Z0C caps: row `H-15`, {'blocks': '1', 'length': '200 mm'}, template 0, printed `MGN15H1R200Z0C` round trip True
- MGN9C1R195ZFH: row `C-9`, {'blocks': '1', 'length': '195 mm'}, template 0, printed `MGN9C1R195ZFH` round trip True

## component.insert_design of the instance file into an assembly (measured in the assembly)

| code | measure in assembly | equals instance |
|---|---|---|
| MGN12H2R300Z0C | 40339.65 / 19943.89 / [0.000..300.000] x [-13.500..13.500] x [0.000..13.000] / 78f 3b | True |
| MGN12H2R300Z0C caps | 40746.80 / 20893.91 / [0.000..300.000] x [-13.500..13.500] x [0.000..13.000] / 114f 15b | True |
| MGN15H1R200Z0C | 41780.31 / 15983.95 / [0.000..200.000] x [-16.000..16.000] x [0.000..16.000] / 39f 2b | True |
| MGN15H1R200Z0C caps | 41949.95 / 16379.79 / [0.000..200.000] x [-16.000..16.000] x [0.000..16.000] / 54f 7b | True |
| MGN9C1R195ZFH | 12328.91 / 8520.93 / [0.000..195.000] x [-10.000..10.000] x [0.000..10.000] / 54f 2b | True |

## Insert with a configuration (0.50.0)

- insert_design configuration=H-12: ok
- row H-12 inserted == Python MGN12H1R300Z0C: True; python 33604.38 / 16692.34 / [0.000..300.000] x [-13.500..13.500] x [0.000..13.000] / 60f 2b; inserted 33604.38 / 16692.34 / [0.000..300.000] x [-13.500..13.500] x [0.000..13.000] / 60f 2b
- insert_design configuration=H-12 parameters={length: 400 mm}: accepted, but rail x extent is 300.0 (300 = the parameters key is ignored)
- component.set_link_parameters: {"command": "component.set_link_parameters", "error": "unknown command `component.set_link_parameters`", "step": 2}
- parameters.change length in the assembly that holds the link: {"command": "parameters.change", "error": "unknown parameter `length`", "step": 2}
- insert_design configuration=nope: {"command": "component.insert_design", "error": "invalid parameters for `component.insert_design`: configuration `nope` does not exist in the source design", "step": 1}
- links and parameters after insert (is the part still parametric?): {"links": [{"changed": false, "component": 1, "configuration": 19, "file": "<path>/mg-rail-set.sc", "found": true, "name": "mg-rail-set", "path": "<path> | user parameters in the assembly: []

## Rebuild on a length change

- parameters.change length 300 -> 400 on the instance == fresh MGN12H2R400 instance: True
- ... == Python MGN12H2R400Z0C: True
- rebuilt : 49296.02 / 24360.16 / [0.000..400.000] x [-13.500..13.500] x [-0.000..13.000] / 90f 3b
- fresh R400 instance: 49296.02 / 24360.16 / [0.000..400.000] x [-13.500..13.500] x [-0.000..13.000] / 90f 3b
- python R400: 49296.02 / 24360.16 / [0.000..400.000] x [-13.500..13.500] x [-0.000..13.000] / 90f 3b
- assembly: linked file edited to length 400, component.update_links == fresh R400 instance: True
- update_links reply: {"failed": [], "unchanged": [], "updated": ["inst-MGN12H2R300Z0C"], "warnings": []}

## Where the limits apply

- ordinary edit parameters.change length=3000 mm on MGN12 (max 2000): accepted: {"changed": {"length": 3000.0}, "errors": [], "recomputed": 8, "restored": 1}
- ordinary edit blocks=9 (max 4): accepted: {"changed": {"blocks": 9.0}, "errors": [], "recomputed": 5, "restored": 0}
- ordinary edit caps=1 on MGN9 (caps only 12/15): accepted: {"changed": {"caps": 1.0}, "errors": [], "recomputed": 4, "restored": 3, "switched": [{"feature": 5, "name": "Rail cap 1", "suppressed": false}, {"feature": 6, "name": "Rail caps", "suppressed": false
- row with length 900 mm on MGN7 (max 600), config.activate: ERROR {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `MGNR7 lengths, S4 p.85 Table 2-4-15` restricts the final value", "step": 1}
- row with caps 1 on MGN9, config.activate: ERROR {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `Caps exist for MGN12 and MGN15 only (S4 p.82 Table 2-4-9)` restricts the final value", "step": 1}
- row with blocks 5, config.activate: ERROR {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `1 to 4 blocks` restricts the final value", "step": 1}
- config.preview of a bad row (length 900 on MGN7): ERROR {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `MGNR7 lengths, S4 p.85 Table 2-4-15` restricts the final value", "step": 1}
- ordinary edit length=30 mm on MGN12 (n would be 0: floor(-0.4)+1): accepted: {"changed": {"length": 30.0}, "errors": [], "recomputed": 9, "restored": 0}
