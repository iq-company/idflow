import fnmatch, re
from typing import Any

_cmp_re = re.compile(r'^\s*(==|!=|>=|<=|>|<)\s*(.+)\s*$')

def match_filter(prop_value: Any, expr: str) -> bool:
    m = _cmp_re.match(expr)
    if m:
        op, rhs = m.groups()
        try:
            pv = float(prop_value); rv = float(rhs)
        except Exception:
            return False
        return {"==": pv == rv,"!=": pv != rv,">": pv > rv,"<": pv < rv,">=": pv >= rv,"<=": pv <= rv}[op]
    if expr.strip().lower() == "exists":
        return bool(prop_value)
    return fnmatch.fnmatch(str(prop_value), expr)

