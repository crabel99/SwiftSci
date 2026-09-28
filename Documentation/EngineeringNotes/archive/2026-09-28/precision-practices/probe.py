"""Isolate NIST input conversion with exact rational ANOVA, not SwiftSci execution."""
import hashlib
import json
import subprocess
import sys
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path


def anova(groups):
    count = sum(map(len, groups))
    means = [sum(g) / len(g) for g in groups]
    mean = sum(map(sum, groups)) / count
    between = sum(len(g) * (m - mean) ** 2 for g, m in zip(groups, means))
    within = sum(sum((x - m) ** 2 for x in g) for g, m in zip(groups, means))
    return (between / (len(groups) - 1)) / (within / (count - len(groups)))


def decimal(value):
    with localcontext() as ctx:
        ctx.prec = 40
        return str(Decimal(value.numerator) / Decimal(value.denominator))


root = Path(sys.argv[1]).resolve()
results = []
for name in ['SmLs07', 'SmLs08', 'SmLs09']:
    path = root / 'Benchmarks/Fixtures/nist-models/inputs' / (name + '.json')
    raw = path.read_bytes()
    groups = json.loads(raw, parse_float=Fraction, parse_int=Fraction)['groups']
    origin = Fraction(groups[0][0].numerator // groups[0][0].denominator)
    direct = [[Fraction.from_float(float(x)) for x in g] for g in groups]
    early = [[Fraction.from_float(float(x - origin)) for x in g] for g in groups]
    late = [[Fraction.from_float(float(x) - float(origin)) for x in g] for g in groups]
    exact_f = anova(groups)
    direct_f, early_f, late_f = map(anova, [direct, early, late])
    ref = json.loads((root / 'Benchmarks/Fixtures/nist-models/references' / (name + '.json')).read_text())
    assert exact_f == Fraction(ref['nistCertifiedValues'][0])
    assert direct_f == late_f, 'Post-conversion shift changed represented problem'
    assert abs(early_f - exact_f) < Fraction(1, 10**10)
    results.append(dict(dataset=name, input_sha256=hashlib.sha256(raw).hexdigest(),
                        origin=decimal(origin), original_decimal_F=decimal(exact_f),
                        direct_double_F=decimal(direct_f), shift_after_double_F=decimal(late_f),
                        shift_before_double_F=decimal(early_f),
                        early_shift_absolute_error=decimal(abs(early_f - exact_f))))
print(json.dumps(dict(method='Exact rational ANOVA after three input-conversion paths; no SwiftSci runtime or performance claim',
                      source_commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),
                      python=sys.version, results=results),indent=2))
