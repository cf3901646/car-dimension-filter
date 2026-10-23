# -*- coding: utf-8 -*-
import csv, sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

with open('car_dimension_filter/data/brands_series_catalog.csv', 'r', encoding='utf-8') as f:
    for idx, row in enumerate(csv.reader(f)):
        r_str = ','.join(row)
        if '2569' in r_str or 'SU7' in r_str or '小米' in r_str or '星锐' in r_str:
            print(f'Line {idx+1}: {row}')
