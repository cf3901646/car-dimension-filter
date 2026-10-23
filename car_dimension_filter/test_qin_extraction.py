# -*- coding: utf-8 -*-
import sys, os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(__file__))
from refetch_empty_specs import fetch_single_series_specs

for sid, name in [(5964, "秦PLUS"), (448, "轩逸"), (656, "奇骏"), (6962, "小米SU7")]:
    sid, sc, v_dict = fetch_single_series_specs(sid)
    print(f"\n{name} ({sid}) -> score: {sc}, versions count: {len(v_dict)}")
    for k, v in list(v_dict.items())[:2]:
        print(f"  {k}: {v}")
