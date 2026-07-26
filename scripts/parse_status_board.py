#!/usr/bin/env python3
import sys
import json
import re

def parse_row(line):
    in_backtick = False
    cols = []
    current = []
    sep_count = 0

    for ch in line[1:-1]:
        if ch == '`':
            in_backtick = not in_backtick
            current.append(ch)
        elif ch == '|' and not in_backtick and sep_count < 5:
            cols.append(''.join(current).strip())
            current = []
            sep_count += 1
        else:
            current.append(ch)

    cols.append(''.join(current).strip())
    return cols


def strip_backticks(s):
    return s.strip().replace('`', '')


def main():
    path = sys.argv[1]

    with open(path, encoding='utf-8') as f:
        lines = f.readlines()

    in_target = False
    header_pattern = ['Source', 'Beelink path', 'Format', 'Status', 'Last updated', 'Notes']

    for raw in lines:
        s = raw.rstrip('\n')

        if s.startswith('### Tier 1'):
            in_target = True
            continue

        if s.startswith('### Tier 2') or s.startswith('## '):
            in_target = False
            continue

        if not in_target:
            continue

        if not s.startswith('|'):
            continue

        # skip header lines
        parts = [p.strip() for p in s.strip('|').split('|')]
        if parts == header_pattern:
            continue

        # skip separator (| --- | --- | ... |)
        if re.match(r'^\|[\s\-|]+\|$', s):
            continue

        if s.strip() == '|':
            continue

        cols = parse_row(s)
        if len(cols) < 6:
            continue

        beelink = strip_backticks(cols[1]).strip()
        row = {
            'source_name': cols[0].strip(),
            'beelink_path': beelink if beelink and beelink != '—' else None,
            'format': cols[2].strip(),
            'status': cols[3].strip(),
            'last_updated': cols[4].strip() if cols[4].strip() != '—' else None,
            'notes': cols[5].strip(),
        }
        print(json.dumps(row, ensure_ascii=False))


if __name__ == '__main__':
    main()
