"""Recount Coupe et al. 2019 reading-aloud rates with the reading-time skill's counting rule.

Inputs (see docs/reading-pace-studies-20261104.md for where to get them and their sha256):
  sm.txt                 text of the supplement aaw2594_SM.pdf, from pdfplumber extract_text(layout=True)
  InfoRateData.csv       github.com/keruiduo/SupplMatInfoRate (CC-BY 4.0)
  AutomaticSylDetect.csv same repository

    python3 -I coupe-recount-20261104.py sm.txt InfoRateData.csv AutomaticSylDetect.csv ratios.json

Written and rerun on 2026-11-04; output in the doc.
"""

import re, sys, csv, unicodedata, statistics as st
from collections import defaultdict
sm, data, auto = sys.argv[1], sys.argv[2], sys.argv[3]
langs = "CAT CMN DEU ENG EUS FIN FRA HUN ITA JPN KOR SPA SRP THA TUR VIE YUE".split()
lines = open(sm, encoding='utf-8').read().split('\n')
start = next(i for i, l in enumerate(lines) if 'We list below these 15 texts' in l)
texts = defaultdict(dict); cur_p = None; cur_l = None
for l in lines[start:]:
    s = l.strip()
    if s.startswith('===== PAGE'): continue
    m = re.match(r'^Passage\s+([OPQ]\d)\s*$', s)
    if m: cur_p = m.group(1); cur_l = None; continue
    m = re.match(r'^([A-Z]{3}):\s*(.*)$', s)
    if m and m.group(1) in langs and cur_p:
        cur_l = m.group(1); texts[cur_p][cur_l] = m.group(2); continue
    if cur_p and cur_l and s:
        texts[cur_p][cur_l] += ' ' + s
def nchars(t):  # letters, digits, marks only, after NFC
    t = unicodedata.normalize('NFC', t)
    return sum(1 for c in t if unicodedata.category(c)[0] in 'LNM')
def nwords(t):
    return sum(1 for w in t.split() if any(unicodedata.category(c)[0] in 'LN' for c in w))
rows = list(csv.DictReader(open(data, encoding='utf-8', newline=''), delimiter='\t'))
ns = {}
for r in rows: ns[(r['Language'], r['Text'])] = float(r['NS'])
print('passages parsed:', sorted(texts), 'n=', len(texts))
print('lang | texts | syl/text | chars/text | words/text | syl/word | chars/syl')
res = {}
for L in langs:
    S = C = W = 0; k = 0
    for p in texts:
        if L in texts[p] and (L, p) in ns:
            t = texts[p][L]; S += ns[(L, p)]; C += nchars(t); W += nwords(t); k += 1
    if k:
        res[L] = (S / W, C / S)
        print(f"{L} | {k} | {S/k:.1f} | {C/k:.1f} | {W/k:.1f} | {S/W:.2f} | {C/S:.2f}")
import json; json.dump(res, open(sys.argv[4], 'w', encoding='utf-8'))

# per-observation rates using text counts and durations
autod = {}
for r in csv.DictReader(open(auto, encoding='utf-8', newline=''), delimiter='\t'):
    r = {k.strip(): v.strip() for k, v in r.items()}
    autod[r['soundname'].lower()] = float(r['dur'])
spk = defaultdict(lambda: defaultdict(list))
for r in rows:
    L, p = r['Language'], r['Text']
    if p not in texts or L not in texts[p]: continue
    t = texts[p][L]; c = nchars(t); w = nwords(t); s = float(r['NS']); d = float(r['Duration'])
    key = (r['Speaker'].replace('(', '_').replace(')', '_') + '_' + p).lower()
    tot = autod.get(key)
    spk[L][r['Speaker']].append((s/d*60, c/d*60, w/d*60, s/tot*60 if tot else None, c/tot*60 if tot else None, w/tot*60 if tot else None))
def q(v):
    v = sorted(v); n = len(v)
    def pct(p):
        k = (n-1)*p; f = int(k); return v[f] + (v[min(f+1,n-1)]-v[f])*(k-f)
    return f"{st.median(v):.0f} [{pct(.25):.0f}-{pct(.75):.0f}]"
print()
print('per minute, median [p25-p75] of 10 speaker means')
print('lang | syl/min excl.pauses | chars/min excl. | words/min excl. | syl/min incl.pauses* | chars/min incl.* | words/min incl.*')
for L in langs:
    S = spk[L]
    cols = []
    for i in range(6):
        vals = [st.mean([o[i] for o in obs if o[i] is not None]) for obs in S.values() if any(o[i] is not None for o in obs)]
        cols.append(q(vals) if vals else 'n/a')
    print(L, '|', ' | '.join(cols))
