from pathlib import Path
import json,subprocess,shutil
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');P=Path('/private/tmp/swiftsci-csv-wide-profile-20261022')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()=='9c067c6c5116d78c0849073acea7fb150404efab'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
for f in ['build.py','ResourceProbe.swift','StreamProbe.swift','GrammarProbe.swift','link-probes.py','verify.py','build-standard-worker.py']:shutil.copy2(P/f,R/f)
old='''                let weights = SIMD16<UInt8>(1, 2, 4, 8, 16, 32, 64, 128, 1, 2, 4, 8, 16, 32, 64, 128)
                let selected = SIMD16<UInt8>.zero.replacing(with: weights, where: structural)
                matches = UInt16(selected.lowHalf.wrappedSum()) | (UInt16(selected.highHalf.wrappedSum()) << 8)'''
changes={'apple-full':'''                let lowWeights = SIMD16<UInt8>(1, 2, 4, 8, 16, 32, 64, 128, 0, 0, 0, 0, 0, 0, 0, 0)
                let highWeights = SIMD16<UInt8>(0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 4, 8, 16, 32, 64, 128)
                let low = SIMD16<UInt8>.zero.replacing(with: lowWeights, where: structural)
                let high = SIMD16<UInt8>.zero.replacing(with: highWeights, where: structural)
                matches = UInt16(simd_reduce_add(low)) | (UInt16(simd_reduce_add(high)) << 8)''','apple-wide':'''                let weights = SIMD16<UInt8>(1, 2, 4, 8, 16, 32, 64, 128, 1, 2, 4, 8, 16, 32, 64, 128)
                let selected = SIMD16<UInt8>.zero.replacing(with: weights, where: structural)
                let low = SIMD8<UInt16>(truncatingIfNeeded: selected.lowHalf)
                let high = SIMD8<UInt16>(truncatingIfNeeded: selected.highHalf)
                matches = simd_reduce_add(low | (high &<< 8))'''}
v={}
for name,new in changes.items():
 D=R/(name+'-trial');shutil.copytree(S/'Sources/SwiftDataFrame',D/'Sources/SwiftDataFrame');v[name]={'path':str(D),'pr':None}
 p=D/'Sources/SwiftDataFrame/IO/SystemsCSVParser.swift';s=p.read_text();assert old in s;s=s.replace('import Foundation','import Foundation\nimport simd',1);p.write_text(s.replace(old,new))
(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
