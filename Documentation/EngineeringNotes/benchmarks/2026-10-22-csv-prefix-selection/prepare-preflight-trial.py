from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');D=R/'variants/preflight'
shutil.copytree(S/'Sources/SwiftDataFrame',D/'Sources/SwiftDataFrame')
p=D/'Sources/SwiftDataFrame/IO/CSVASCIIPrefixStringDecoder.swift';s=p.read_text();a=s.index('        guard nullValues.count > 2');b=s.index('        var low:',a)
s=s[:a]+'''        guard nullValues.count > 2, nullValues.count <= selectedRowCount / 2 else { return nil }
        // Admit two token traversals and one byte scan before preparing any masks.
        var remaining = selectedRowCount - nullValues.count - nullValues.count
        for token in nullValues {
            guard token.isContiguousUTF8 else { return nil }
            let count = token.utf8.count
            guard count <= remaining else { return nil }
            remaining -= count
        }
'''+s[b:]
s=s.replace('guard remaining > 0, byte < 128 else { return nil }\n                remaining -= 1','guard byte < 128 else { return nil }');p.write_text(s)
v=json.loads((R/'variants.json').read_text());v['preflight']={'path':str(D),'pr':None};(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
s=(R/'run-crossover.py').read_text();a=s.index('cases=');b=s.index('D=R/label;',a)
s=s[:a]+'''flags=json.loads((R/'crossover/review-flags.json').read_text())
selected={(f['candidate']['scope'],f['candidate']['case']) for f in flags}
contracts={Path(p).stem:Path(p) for p in json.loads((R/'crossover-contracts.json').read_text())}
cases=[(scope,case,contracts[case]) for scope,case in sorted(selected)]
P=Path('/private/tmp/swiftsci-csv-string-cost-20261022')
cases += [(scope,'energy-default',P/'inputs/energy-default.json') for scope in ['eager','stream']]
cases += [('eager','Aotizhongxin-default',P/'inputs/Aotizhongxin-default.json')]
'''+s[b:]
# Retain the selected row count for boundary files, standard10000-row streaming for household reference.
s=s.replace("[str(inp['rows']),policy]","[str(inp['rows']) if case != 'energy-default' else '10000',policy]")
(R/'run-preflight-screen.py').write_text(s)
