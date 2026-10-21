from pathlib import Path
import sys,json,time,resource,ctypes,hashlib,struct,datetime
import numpy as np
engine=sys.argv[1];input_path=Path(sys.argv[2]);case=json.loads(input_path.read_text())
lib=ctypes.CDLL('/usr/lib/libSystem.B.dylib')
class MachInfo(ctypes.Structure):
 _fields_=[('virtual_size',ctypes.c_uint64),('resident_size',ctypes.c_uint64),('resident_size_max',ctypes.c_uint64),('user_sec',ctypes.c_int32),('user_micro',ctypes.c_int32),('sys_sec',ctypes.c_int32),('sys_micro',ctypes.c_int32),('policy',ctypes.c_int32),('suspend',ctypes.c_int32)]
self_task=ctypes.c_uint.in_dll(lib,'mach_task_self_').value
lib.task_info.argtypes=[ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint)]
def rss():
 info=MachInfo();count=ctypes.c_uint(ctypes.sizeof(info)//4)
 assert lib.task_info(self_task,20,ctypes.byref(info),ctypes.byref(count))==0
 return info.resident_size
def peak():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
def cpu():
 r=resource.getrusage(resource.RUSAGE_SELF);return round((r.ru_utime+r.ru_stime)*1e9)
versions={'python':sys.version,'numpy':np.__version__};pools={}
is_date='Date' in case['types']
date_formats=case.get('reference_date_formats',{})
date_names=list(date_formats)
if engine=='pandas':
 import pandas as pd
 versions['pandas']=pd.__version__
 types={'String':'str','Double':'float64','Int64':'int64'}
 kwargs=dict(sep=case['delimiter'],header=0,dtype={n:types[t] for n,t in zip(case['names'],case['types']) if t!='Date'},na_values=case['null_tokens'],keep_default_na=False,encoding='utf-8',engine='c',float_precision='round_trip')
 if is_date:kwargs.update(parse_dates=date_names,date_format=date_formats,cache_dates=True)
 def read():return pd.read_csv(case['path'],**kwargs)
elif engine=='polars':
 import polars as pl
 versions['polars']=pl.__version__;pools['polars']=pl.thread_pool_size()
 types={'String':pl.String,'Double':pl.Float64,'Int64':pl.Int64,'Date':pl.String}
 kwargs=dict(separator=case['delimiter'],has_header=True,schema={n:types[t] for n,t in zip(case['names'],case['types'])},null_values=case['null_tokens'],try_parse_dates=False)
 def read():
  frame=pl.read_csv(case['path'],**kwargs)
  if is_date:frame=frame.with_columns([pl.col(name).str.strptime(pl.Datetime('us'),format=fmt,strict=True,exact=True,cache=True) for name,fmt in date_formats.items()])
  return frame
elif engine=='duckdb':
 import duckdb,pyarrow as pa
 versions.update(duckdb=duckdb.__version__,pyarrow=pa.__version__)
 connection=duckdb.connect();pools['duckdb']=connection.sql("select current_setting('threads')").fetchone()[0]
 assert connection.sql("select current_setting('preserve_insertion_order')").fetchone()[0]
 types={'String':'VARCHAR','Double':'DOUBLE','Int64':'BIGINT','Date':'TIMESTAMP'}
 kwargs=dict(delimiter=case['delimiter'],header=True,columns={n:types[t] for n,t in zip(case['names'],case['types'])},na_values=case['null_tokens'],auto_detect=False)
 if is_date:kwargs.update(timestamp_format=next(iter(date_formats.values())))
 def read():return connection.read_csv(case['path'],**kwargs).to_arrow_table()
else:raise ValueError(engine)
def validate(frame):
 names=list(frame.columns) if engine!='duckdb' else frame.column_names
 failures=[];details=[]
 if names!=case['names']:failures.append('column names/order')
 if len(frame)!=case['rows']:failures.append('row count')
 for j,(name,kind) in enumerate(zip(case['names'],case['types'])):
  col=frame[name];dtype=str(col.dtype) if engine!='duckdb' else str(col.type)
  if engine=='pandas':
   matches={'Double':pd.api.types.is_float_dtype(col) and col.dtype.itemsize==8,'Int64':pd.api.types.is_integer_dtype(col) and col.dtype.itemsize==8,'String':pd.api.types.is_string_dtype(col),'Date':pd.api.types.is_datetime64_any_dtype(col)}[kind]
  elif engine=='polars':matches=col.dtype=={'Double':pl.Float64,'Int64':pl.Int64,'String':pl.String,'Date':pl.Datetime('us')}[kind]
  else:matches=col.type=={'Double':pa.float64(),'Int64':pa.int64(),'String':pa.string(),'Date':pa.timestamp('us')}[kind]
  if not matches:failures.append('type: '+name+': '+dtype)
  h=hashlib.sha256();nulls=0
  for start in range(0,len(frame),65536):
   if engine=='pandas':
    part=col.iloc[start:start+65536];valid=~part.isna().to_numpy()
    values=part.tolist() if kind=='String' else part.to_numpy()
   elif engine=='polars':
    part=col.slice(start,65536);valid=part.is_not_null().to_numpy();values=part.to_list() if kind=='String' else part.to_numpy()
   else:
    part=col.slice(start,65536);valid=part.is_valid().to_numpy();values=part.to_pylist() if kind=='String' else part.to_numpy()
   nulls+=int((~valid).sum())
   if kind=='String':
    buf=bytearray()
    for value,ok in zip(values,valid):
     if ok:
      b=value.encode('utf-8');buf+=b'\1'+struct.pack('<I',len(b))+b
     else:buf+=b'\0'
    h.update(buf)
   else:
    numbers=values.astype('datetime64[s]').astype(np.int64).astype(np.float64) if kind=='Date' else np.asarray(values,dtype=np.float64)
    packed=np.empty((len(valid),9),dtype=np.uint8);packed[:,0]=valid
    packed[:,1:]=np.ascontiguousarray(numbers,dtype='<f8').view(np.uint8).reshape(-1,8)
    keep=np.ones(packed.shape,dtype=bool);keep[~valid,1:]=False
    h.update(packed[keep].tobytes())
  actual=h.hexdigest()
  if actual!=case['hashes'][j]:failures.append('values/nulls: '+name)
  if nulls!=case['null_counts'][j]:failures.append('null count: '+name)
  details.append(dict(name=name,type=dtype,nulls=nulls,sha256=actual))
 return dict(passed=not failures,failures=failures,columns=details)
r0=rss();p0=peak();c0=cpu();t0=time.perf_counter_ns()
output=read()
t1=time.perf_counter_ns();c1=cpu();r1=rss();p1=peak()
checks=validate(output)
c2=cpu();t2=time.perf_counter_ns();del output;t3=time.perf_counter_ns();c3=cpu()
sample=dict(call_ns=t1-t0,call_cpu_ns=c1-c0,release_ns=t3-t2,release_cpu_ns=c3-c2,total_ns=t1-t0+t3-t2,total_cpu_ns=c1-c0+c3-c2,rss_before_bytes=r0,rss_held_bytes=r1,rss_held_delta_bytes=r1-r0,rss_after_release_bytes=rss(),process_peak_before_bytes=p0,process_peak_held_bytes=p1)
print(json.dumps(dict(engine=engine,input=case['id'],validated=checks['passed'],checks=checks,samples=[sample],versions=versions,pools=pools,options=kwargs,scope='Fresh-process first public read and release, native eager output; validation excluded; memory before validation'),default=str))
