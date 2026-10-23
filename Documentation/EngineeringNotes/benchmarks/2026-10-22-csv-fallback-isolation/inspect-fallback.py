from pathlib import Path
import hashlib,json,subprocess,re,collections
R=Path(__file__).resolve().parent;D=R/'fallback-code';D.mkdir(exist_ok=False);results=[]
for e in ['cleanup','production','no-preparation','metadata']:
 b=R/'build'/e/'ResourceProbe';raw=subprocess.check_output(['xcrun','otool','-tvV',str(b)],text=True).splitlines();blocks={}
 for i,line in enumerate(raw):
  if not (line.startswith('_$s14SwiftDataFrame') and line.endswith(':')):continue
  if not (('CSVColumnConversionO6append' in line or 'CSVColumnAttemptC' in line) and ('CSVCompactRecordView' in line or 'CSVFlatRecordView' in line or 'CSVStringDecoder' in line)):continue
  j=next((k for k in range(i+1,len(raw)) if raw[k].startswith('_') and raw[k].endswith(':')),len(raw));blocks[line]='\n'.join(raw[i:j])
 (D/(e+'.asm')).write_text('\n\n'.join(blocks.values())+'\n');fs=[]
 for symbol,block in blocks.items():
  name=subprocess.check_output(['xcrun','swift-demangle',symbol[:-1]],text=True).strip()
  instructions=[l for l in block.splitlines() if re.match(r'^[0-9a-f]{16}\s',l)];calls=[l.strip() for l in instructions if re.search(r'\s(?:bl|blr|blraa|blrab)\s',l)]
  fs.append(dict(symbol=symbol,demangled=name,instructions=len(instructions),indirect_calls=[l for l in calls if re.search(r'\sblr[a-z]*\s',l)],calls=calls))
 results.append(dict(engine=e,binary_sha256=hashlib.sha256(b.read_bytes()).hexdigest(),functions=fs));print(e,len(fs),'functions',[(f['instructions'],len(f['indirect_calls'])) for f in fs],flush=True)
(D/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
