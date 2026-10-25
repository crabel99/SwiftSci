"""Run the portable audit while denying file reads except the given archive."""
import gzip
import importlib.util
import json
import os
from pathlib import Path
import sys

verifier=Path(sys.argv[1]).resolve();archive=Path(sys.argv[2]).resolve()
spec=importlib.util.spec_from_file_location('portable_receipt_audit',verifier)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
attempts=[]
def restrict(event,args):
    if event=='open':
        name=args[0]
        if isinstance(name,int):return
        resolved=Path(os.fsdecode(name)).resolve()
        if resolved!=archive:
            attempts.append(str(resolved));raise PermissionError('Portable audit tried an unarchived file: '+str(resolved))
    if event in {'subprocess.Popen','ctypes.dlopen','os.system','socket.connect'}:
        raise PermissionError('Portable audit tried a native or network operation: '+event)
sys.addaudithook(restrict)
result=module.main(archive)
result['isolation']=dict(scope='module.main receipt audit, after trusted verifier and standard-library loading',
    only_archive_file_reads_allowed_during_receipt_audit=True,unarchived_file_read_attempts_during_receipt_audit=attempts,
    native_library_loading_and_subprocesses_denied_during_receipt_audit=True)
print(json.dumps(result,indent=2,allow_nan=False))
