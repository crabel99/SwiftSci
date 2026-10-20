from pathlib import Path
import shutil,json,subprocess
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-scalar-resource-20261019')
base='546510bb7df19fc87a664bded5947c738011ee1d'
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',base,'Sources/SwiftDataFrame'],cwd=S,text=True).splitlines()
for label in ['baseline','presized']:
 D=R/label
 for name in paths:
  p=D/name;p.parent.mkdir(parents=True,exist_ok=True)
  p.write_bytes(subprocess.check_output(['git','show',base+':'+name],cwd=S))
p=R/'presized/Sources/SwiftDataFrame/IO/SystemsCSVParser.swift';s=p.read_text();needle='''        var fields = [PackedCSVField]()
        fields.reserveCapacity(min(range.count / 8, 100_000))
        var rowStarts = [0]
        rowStarts.reserveCapacity(min(range.count / 16, 100_000) + 1)'''
assert s.count(needle)==1
s=s.replace(needle,'''        let sizes = countQuotedIndex(buffer: buffer, range: range)
        var fields = [PackedCSVField]()
        fields.reserveCapacity(sizes.fields)
        var rowStarts = [0]
        rowStarts.reserveCapacity(sizes.rows + 1)''')
needle='    private func scanIndex(\n'
method='''    // Diagnostic trial: include a full structural counting pass before allocation.
    private func countQuotedIndex(
        buffer: UnsafeBufferPointer<UInt8>, range: Range<Int>
    ) -> (fields: Int, rows: Int) {
        var fields = 0, rows = 0
        var index = range.lowerBound, fieldStart = range.lowerBound
        var insideQuotes = false
        while index < range.upperBound {
            let byte = buffer[index]
            if insideQuotes {
                if byte == quoteByte {
                    if index + 1 < range.upperBound && buffer[index + 1] == quoteByte {
                        index += 2
                        continue
                    }
                    insideQuotes = false
                }
            } else if byte == quoteByte {
                insideQuotes = true
            } else if byte == delimiterByte {
                fields += 1
                fieldStart = index + 1
            } else if byte == lfByte {
                fields += 1
                rows += 1
                fieldStart = index + 1
            }
            index += 1
        }
        if fieldStart < range.upperBound { fields += 1; rows += 1 }
        return (fields, rows)
    }

'''
s=s.replace(needle,method+needle);p.write_text(s)
variants=json.loads((R/'variants.json').read_text()) if (R/'variants.json').exists() else {};sha=base
for label in ['baseline','presized']:variants[label]={'path':str(R/label),'base_sha':sha,'pr':None,'diagnostic_patch':label=='presized'}
(R/'variants.json').write_text(json.dumps(variants,indent=2)+'\n')
shutil.copy2('/Users/crabel/local-ai/spl/swiftsci/pr-resource-metrics-20261018/ResourceProbe.swift',R/'ResourceProbe.swift')
(R/'PLAN.md').write_text('''# Quoted CSV allocation diagnosis\n\nOctober 20, 2026. Historical and current readers reproduce oversized output arrays. Pointer instrumentation shows that a column reserving 250000 elements receives the same address previously used by a 401406-element parser field buffer. A standalone Swift Array program reproduces the reuse without SwiftSci.\n\nCompare the current source at 546510bb7d with a throwaway exact-count prepass. The prepass scans the actual input using the same quote and escape rules; it does not receive fixture sizes or a supplied schema. Both readers perform normal schema inference and the same output validation. The extra scan is inside every measured call. Do not use instrumented builds for timing.\n\nFive alternating timing pairs, two warmups and five measured samples per process. Three separate memory pairs, one operation without warmup. Measure CPU user+system and elapsed time including call and output release; check all values outside timing. Capture live heap and RSS before validation. Cases: 100000, 250000 and 1000000 quoted rows at width four; 1000000 quoted rows at width two; 1000000 unquoted rows at width four.\n\nThis experiment asks whether avoiding growing parser arrays improves overall resources. A retained-memory win alone does not justify a more expensive default. Preserve failures and any CPU tradeoff. Do not alter production code, push a branch, or claim energy savings.\n''')
