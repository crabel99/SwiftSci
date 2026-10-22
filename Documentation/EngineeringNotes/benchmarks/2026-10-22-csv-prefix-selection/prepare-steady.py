from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parent
s=(R/'StreamProbe.swift').read_text();a=s.index('        let r0 = resident()');b=s.index('        let valid =',a)
s=s[:a]+'''        for _ in 0..<2 {
            let count = try await consume(DataFrame.readCSVStream(contentsOf: url, chunkSize: chunkSize, options: options))
            precondition(count == input.rows)
        }
        var samples = [[String: Any]]()
        for _ in 0..<5 {
            let r0 = resident(), p0 = peak(), h0 = heap(), c0 = cpu(), t0 = DispatchTime.now().uptimeNanoseconds
            let count = try await consume(DataFrame.readCSVStream(contentsOf: url, chunkSize: chunkSize, options: options))
            let t1 = DispatchTime.now().uptimeNanoseconds, c1 = cpu(), h1 = heap(), p1 = peak(), r1 = resident()
            precondition(count == input.rows)
            samples.append(["total_ns": Int64(t1-t0), "total_cpu_ns": c1-c0,
                "rss_before_bytes":r0,"rss_after_bytes":r1,"rss_growth_bytes":r1-r0,
                "peak_before_bytes":p0,"peak_after_bytes":p1,"heap_before_bytes":h0,"heap_after_bytes":h1])
        }
'''+s[b:]
a=s.index('        let result: [String: Any]');b=s.index('        print(',a)
s=s[:a]+'''        let result: [String: Any] = ["validated": valid, "rows":input.rows,"input":input.id,
            "chunk_size":chunkSize,"samples":samples,"warmups":2,
            "scope":"Two warmup streams, five separately timed full streams with row checks, then one untimed full native type/value/null/order validation. Per-worker medians are observations; repeated reads are not independent workers. Peak RSS includes warmups and preceding reads."]
'''+s[b:];(R/'StreamRepeatProbe.swift').write_text(s)
for engine in ['cleanup','production','preflight']:
 D=R/'build'/engine;rec=json.loads((D/'build.json').read_text())
 cmd=[str(R/'StreamRepeatProbe.swift') if a.endswith('/ResourceProbe.swift') else a for a in rec['commands'][1]]
 cmd[cmd.index('-o')+1]=str(D/'StreamRepeatProbe')
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 (D/'StreamRepeatProbe.build.json').write_text(json.dumps(dict(command=cmd,binary_sha256=hashlib.sha256((D/'StreamRepeatProbe').read_bytes()).hexdigest(),harness_sha256=hashlib.sha256((R/'StreamRepeatProbe.swift').read_bytes()).hexdigest()),indent=2)+'\n')
s=(R/'run-preflight-screen.py').read_text();a=s.index("P=Path('/private/tmp/swiftsci-csv-string-cost-20261022')");b=s.index('D=R/label;',a);s=s[:a]+s[b:]
s=s.replace("for binary in ['ResourceProbe','StreamProbe']:","for binary in ['ResourceProbe','StreamRepeatProbe']:")
s=s.replace("for b in ['ResourceProbe','StreamProbe']","for b in ['ResourceProbe','StreamRepeatProbe']")
s=s.replace("else 'StreamProbe'","else 'StreamRepeatProbe'").replace("['known','fresh','1',policy]","['known','timing','5',policy]")
s=s.replace("d=json.loads(p.stdout);assert d['validated']","d=json.loads(p.stdout);assert d['validated'];d['comparison_sample']={k:st.median(v[k] for v in d['samples']) for k in d['samples'][0] if isinstance(d['samples'][0][k],(int,float))}")
s=s.replace("d.get('samples',[d])[0]","d['comparison_sample']")
s=s.replace("Native output hashes, values, types and null counts checked.","Two warmups plus five reads; per-worker medians, peak includes earlier reads. Native output hashes, values, types and null counts checked.")
(R/'run-steady-boundaries.py').write_text(s)
