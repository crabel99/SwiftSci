from pathlib import Path
import subprocess,re,json,hashlib
R=Path(__file__).resolve().parent;roots={'parent':Path('/private/tmp/swiftsci-csv-number-loop-20261022/build/production'),'candidate':Path('/private/tmp/swiftsci-csv-null-dispatch-20261022/build/production'),**{e:R/'build'/e for e in ['dispatch-inline','attempt-outline','direct-value']}}
D=R/'assembly';D.mkdir(exist_ok=True);summary=[]
for label,root in roots.items():
 binary=root/'StreamProbe';cmd=['xcrun','otool','-tvV',str(binary)];p=subprocess.run(cmd,capture_output=True,text=True,check=True);lines=p.stdout.splitlines();blocks=[];functions=[]
 for i,l in enumerate(lines):
  if (l.startswith('_$s14SwiftDataFrame19CSVColumnConversionO6append') or l.startswith('_$s14SwiftDataFrame16CSVColumnAttemptC6append')) and 'CSVCompactRecordView' in l:
   j=next((k for k in range(i+1,len(lines)) if lines[k].startswith('_') and lines[k].endswith(':')),len(lines));block=lines[i:j];blocks.append('\n'.join(block));instructions=[line for line in block if re.match(r'^[0-9a-f]{16}\s',line)]
   calls=[line for line in instructions if re.search(r'\s(?:bl|b)\s.*CSVColumnAttempt',line)]
   functions.append(dict(symbol=l,instruction_entries=len(instructions),typed_attempt_calls=calls))
 (D/(label+'-compact-dispatch.txt')).write_text('\n\n'.join(blocks)+'\n')
 summary.append(dict(implementation=label,functions=functions,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),command=cmd,scope='Static disassembly entries and calls. Missing standalone symbols can mean inlining or elimination. Not executed instruction count, FLOPs, or cache evidence.'))
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print([(a['implementation'],[(f['symbol'].split('CSVRecordAccess')[0][-20:],f['instruction_entries']) for f in a['functions']]) for a in summary])
