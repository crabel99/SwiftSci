"""Write candidate inputs and scalar references beneath the selected output root."""
from pathlib import Path
import sys
from contracts import digest, write_json
from boundary_cases import cases
from boundary_fixtures import validate_input
from boundary_reference import reference


def generate(root):
    root=Path(root)
    for name,p in cases():
        validate_input(p,p['operation'],len(p['row_ids']))
        path=root/'inputs'/f'{name}.json';write_json(path,p);raw=path.read_bytes()
        write_json(root/'references'/f'{name}.json', {
            'operation':p['operation'],'inputIdentity':{'sha256':digest(raw),'bytes':len(raw)},
            'model':{'observations':len(p['row_ids'])},
            'independentReference':{'precision_decimal_digits':100,'values':reference(p)}})


if __name__=='__main__': generate(sys.argv[1])
