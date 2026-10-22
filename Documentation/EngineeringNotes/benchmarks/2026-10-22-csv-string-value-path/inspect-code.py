from pathlib import Path
import hashlib,json,re,struct,subprocess
R=Path(__file__).resolve().parent;D=R/'assembly';D.mkdir(exist_ok=True);rows=[]
for label in ['control','hashed-optional','both-optional']:
 binary=R/'build'/label/'ResourceProbe';cmd=['xcrun','otool','-tvV',str(binary)]
 lines=subprocess.check_output(cmd,text=True).splitlines();blocks={}
 for i,line in enumerate(lines):
  if not (line.startswith('_$s14SwiftDataFrame') and line.endswith(':')):continue
  if ('CSVColumnConversionO6append' not in line and 'CSVColumnAttemptC' not in line) or 'CSVCompactRecordView' not in line:continue
  j=next((k for k in range(i+1,len(lines)) if lines[k].startswith('_') and lines[k].endswith(':')),len(lines))
  blocks[line]='\n'.join(lines[i:j])
 (D/(label+'-compact-dispatch.txt')).write_text('\n\n'.join(blocks.values())+'\n')
 raw=binary.read_bytes();header=struct.unpack_from('<8I',raw);assert header[0]==0xfeedfacf;off=32;sections={}
 for _ in range(header[4]):
  cmd_id,size=struct.unpack_from('<II',raw,off)
  if cmd_id==0x19:
   seg=raw[off+8:off+24].rstrip(b'\0').decode();nsect=struct.unpack_from('<I',raw,off+64)[0]
   for j in range(nsect):
    pos=off+72+80*j;name=raw[pos:pos+16].rstrip(b'\0').decode();length=struct.unpack_from('<Q',raw,pos+40)[0];start=struct.unpack_from('<I',raw,pos+48)[0]
    if seg=='__TEXT':sections[name]={'bytes':length,'sha256':hashlib.sha256(raw[start:start+length]).hexdigest()}
  off+=size
 rows.append(dict(variant=label,command=cmd,binary_sha256=hashlib.sha256(raw).hexdigest(),sections=sections,functions=[dict(symbol=symbol,instruction_entries=sum(bool(re.match(r'^[0-9a-f]{16}\s',line)) for line in block.splitlines())) for symbol,block in blocks.items()],scope='Static emitted instructions and bytes, not executed instruction counts or hardware measurements.'))
(D/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
assert rows[0]['sections']==rows[1]['sections']
print('Control and hashed-optional have identical bytes in every __TEXT section.')
