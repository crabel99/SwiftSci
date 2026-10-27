from pathlib import Path
import subprocess, sys
r = Path(__file__).resolve().parent
for mode, tag, selected in [('Debug', 'green', ['SwiftMLTests/CoreMLMulticlassExportTests']), ('Debug', 'full-debug', []), ('Release', 'full-release', [])]:
    result = subprocess.run([sys.executable, str(r / 'validate-native.py'), mode, tag, *selected], cwd=r / 'source')
    if result.returncode:
        raise SystemExit(result.returncode)
