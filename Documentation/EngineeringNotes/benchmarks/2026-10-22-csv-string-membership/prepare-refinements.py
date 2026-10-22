from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parent;variants=json.loads((R/'variants.json').read_text())
for name,parent in [('required-prep','control'),('prefix-required-prep','ascii-prefix')]:
 root=R/'variants'/name;shutil.copytree(R/'variants'/parent/'Sources/SwiftDataFrame',root/'Sources/SwiftDataFrame')
 p=root/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';s=p.read_text();old='        let nulls = CSVNullMatcher(nullValues)\n';assert s.count(old)==1;s=s.replace(old,'')
 for decoder in ['CSVIntegerDecoder','CSVDoubleDecoder','CSVDateDecoder']:
  old=decoder+'(nulls: nulls';assert s.count(old)==1;s=s.replace(old,decoder+'(nulls: CSVNullMatcher(nullValues)')
 if name=='prefix-required-prep':
  old='''        if let first = text.utf8.first, first < 128 {''';assert s.count(old)==1;s=s.replace(old,'''        guard !nullValues.isEmpty else { return .value(text) }
        if let first = text.utf8.first, first < 128 {''')
 p.write_text(s);variants[name]={'path':str(root),'pr':None}
(R/'variants.json').write_text(json.dumps(variants,indent=2)+'\n')
s=(R/'run-semantics.py').read_text().replace("D=R/'semantics'","D=R/'refined-semantics'").replace("['control','ascii-prefix']","['required-prep','prefix-required-prep']")
(R/'run-refined-semantics.py').write_text(s)
