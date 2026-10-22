from pathlib import Path
import json
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-string-cost-20261022')
s=(R/'link-probes.py').read_text().replace('import subprocess,hashlib,json','import subprocess,hashlib,json,sys').replace("D=R/'build/production'","D=R/'build'/sys.argv[1]").replace("R/'grammar-result.json'","R/(sys.argv[1]+'-grammar-result.json')")
(R/'link-variant.py').write_text(s)
s=(P/'setup-controls.py').read_text();start=s.index('roots=');end=s.index('for e,d in roots.items():')
s=s[:start]+"roots={e:R/'build'/e for e in engines}\nvariants=json.loads((R/'variants.json').read_text())\nsource_roots={e:Path(variants[e]['path']) for e in engines}\n"+s[end:]
a=s.index("T=Path(");b=s.index("D=R/label;",a)
s=s[:a]+"cases=[(scope,Path(p).stem,Path(p)) for p in json.loads((R/'crossover-contracts.json').read_text()) for scope in ['eager','stream']]\n"+s[b:]
s=s.replace("['10000',policy]","[str(inp['rows']),policy]")
(R/'run-crossover.py').write_text(s)
s=s.replace("(R/'crossover-contracts.json')","(Path('/private/tmp/swiftsci-csv-string-cost-20261022/setup-contracts.json'))").replace("for scope in ['eager','stream']","for scope in ['eager']")
(R/'run-setup.py').write_text(s)
s=(P/'run-refined-semantics.py').read_text().replace("R/'unicode/all-scalars.json'","Path('/private/tmp/swiftsci-csv-string-cost-20261022/unicode/all-scalars.json')").replace("['required-prep','prefix-required-prep']","['production']").replace("R/'refined-semantics'","R/'unicode-semantics'")
(R/'run-unicode.py').write_text(s)
