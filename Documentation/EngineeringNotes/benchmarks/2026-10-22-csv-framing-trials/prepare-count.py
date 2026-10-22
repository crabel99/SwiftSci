from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');D=R/'derived-count-trial'
shutil.copytree(S/'Sources/SwiftDataFrame',D/'Sources/SwiftDataFrame')
p=D/'Sources/SwiftDataFrame/IO/CSVRecordIndex.swift';s=p.read_text();old='    private(set) var count = 0';new='    var count: Int { completed.count * CSVFieldBlockLayout.capacity + current.count }';assert s.count(old)==1;s=s.replace(old,new).replace('        count += 1\n','').replace('            count -= removed\n','');p.write_text(s)
v=json.loads((R/'variants.json').read_text());v['derived-count']={'path':str(D),'pr':None};(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
