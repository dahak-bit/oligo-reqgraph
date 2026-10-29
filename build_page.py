#!/usr/bin/env python3
"""Phase C generator: one page, four views (Map · Explore · Register · Notes), shared filters,
hash-routed views, programme-type presets, CSV/SVG export, A4 print stylesheet, keyboard access.
Deterministic layout from graph.json; the renderer holds no layout facts.
Usage: python build_page.py   →  pkg/index.html, pkg/figure1.svg"""
import json, os, html, re, sys
INTERNAL="--internal" in sys.argv  # default: public page (About = scope only); --internal adds changes, audit, roadmap, open items
HERE=os.path.dirname(os.path.abspath(__file__)); PKG=HERE
g=json.load(open(os.path.join(PKG,"graph.json"))); NB={n["id"]:n for n in g["nodes"]}

GATES=[(x["id"],x["label"]) for x in g["meta"]["gates"]]
GATES=[(i,{"cta":"CTA / IND","filing":"Filing & approval","post":"Post-approval"}.get(i,l)) for i,l in GATES]
DOMAINS=[("quality","Quality & CMC"),("nonclin","Nonclinical safety"),("clinical","Clinical &|pharmacology"),
         ("paed","Paediatric"),("rare","Rare, expedited &|individualised"),("auth","Trial & marketing|authorisation")]
REGIONS=["ICH","EU","US","JP","UK","INTL"]
docs=[n for n in g["nodes"] if n["kind"] not in ("milestone","consideration")]
P={n["id"]:(n["domain"],n["gate_from"],n["gate_to"],n["key"]) for n in docs}
GROUPS=[(grp["domain"],min(NB[m]["gate_from"] for m in grp["members"]),max(NB[m]["gate_to"] for m in grp["members"]),grp["members"]) for grp in g["meta"]["groups"]]
grouped=set(m for *_,ms in GROUPS for m in ms)
TRIG_LABEL=g["meta"]["triggers"]
OVERLAYS={t:(lab,[n["id"] for n in docs if t in n["triggers"]]) for t,lab in TRIG_LABEL.items()}
STATUSES=[("in_force","In force"),("draft","Draft"),("pending","Pending adoption"),("programme","Programme / designation"),
          ("guidance","Non-binding consensus"),("superseded","Superseded"),("verify","Unverified")]
VERIF=[("page","Source opened"),("search","URL on official site"),("secondary","Secondary source opened"),("knowledge","Not checked live")]
# Built-in filter presets per programme type (jurisdictions a sponsor of that programme type typically files in).
PRESETS={
 "paed_onc":{"label":"Paediatric oncology programme","region":["ICH","EU","US"],"from":1,"to":7,"ov":"paed_onc","hide":True},
 "intrathecal":{"label":"Intrathecal / CNS programme","region":["ICH","EU","US","INTL"],"from":0,"to":6,"ov":"intrathecal","hide":True},
 "individualised":{"label":"Individualised ASO (n-of-1)","region":["EU","US","INTL"],"from":0,"to":3,"ov":"individualised","hide":True},
 "galnac":{"label":"GalNAc–siRNA, hepatic target","region":["ICH","EU","US","JP"],"from":0,"to":7,"ov":"galnac","hide":True},
 "lnp":{"label":"LNP-formulated oligo","region":["ICH","EU","US"],"from":0,"to":6,"ov":"lnp","hide":True},
 "aoc":{"label":"Antibody–oligo conjugate","region":["ICH","EU","US"],"from":0,"to":6,"ov":"aoc","hide":True},
}
def esc(s): return html.escape(str(s),quote=True)

# ---------- geometry (unchanged from v0.3 map) ----------
LW=168; CW=118; TOP=58; LANEPAD=10; CH=20; CGAP=5
W=LW+CW*len(GATES)+16
def gx(i): return LW+i*CW
lanes={}
for d,(dom,a,b,key) in P.items():
    if d not in grouped: lanes.setdefault(dom,[]).append((a,b,[d]))
for dom,a,b,ids in GROUPS: lanes.setdefault(dom,[]).append((a,b,ids))
rows_per_lane={}; placed={}
for dom,items in lanes.items():
    items.sort(key=lambda t:(t[0],-(t[1]-t[0]),P[t[2][0]][3]))
    rows=[]
    for a,b,ids in items:
        for ri,r in enumerate(rows):
            if all(b<ra or a>rb for ra,rb in r): r.append((a,b)); placed[ids[0]]=ri; break
        else: rows.append([(a,b)]); placed[ids[0]]=len(rows)-1
    rows_per_lane[dom]=len(rows)
lane_y={}; y=TOP
for dom,_ in DOMAINS:
    lane_y[dom]=y; y+=LANEPAD*2+rows_per_lane[dom]*(CH+CGAP)
H=y+8

def bar_status(ids):
    sts={NB[i]["status"] for i in ids}
    return NB[ids[0]]["status"] if len(sts)==1 else "mixed"

svg=[f'<svg class="fig" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Figure 1. Regulatory map">']
svg.append('<defs><pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="5" height="5" class="hatch-bg"/><line x1="0" y1="0" x2="0" y2="5" class="hatch-ln"/></pattern></defs>')
for i,(gid,lab) in enumerate(GATES):
    svg.append(f'<rect class="colmask" data-col="{i}" x="{gx(i)}" y="{TOP-6}" width="{CW}" height="{H-TOP}"/>')
sy=30
svg.append(f'<line x1="{gx(0)}" y1="{sy}" x2="{gx(len(GATES))}" y2="{sy}" class="spine"/>')
for i,(gid,lab) in enumerate(GATES):
    x=gx(i)
    svg.append(f'<line x1="{x}" y1="{sy-5}" x2="{x}" y2="{sy+5}" class="spine"/>')
    svg.append(f'<text x="{x+CW/2}" y="{sy-10}" class="gate" text-anchor="middle">{esc(lab)}</text>')
    svg.append(f'<line x1="{x}" y1="{TOP-6}" x2="{x}" y2="{H-6}" class="grid vline"/>')
svg.append(f'<line x1="{gx(len(GATES))}" y1="{TOP-6}" x2="{gx(len(GATES))}" y2="{H-6}" class="grid vline"/>')
ex=gx(5)
svg.append(f'<polygon points="{ex},{sy-7} {ex+7},{sy} {ex},{sy+7} {ex-7},{sy}" class="eop2"/>')
svg.append(f'<text x="{ex}" y="{sy+20}" class="gate-sub" text-anchor="middle">EoP2 · PIP/iPSP trigger</text>')
for li,(dom,lab) in enumerate(DOMAINS):
    y0=lane_y[dom]; h=LANEPAD*2+rows_per_lane[dom]*(CH+CGAP)
    svg.append(f'<g class="lanegrp" data-dom="{dom}" data-y0="{y0}" data-h="{h}">')
    svg.append(f'<rect x="8" y="{y0}" width="{W-16}" height="{h}" class="lane{" alt" if li%2 else ""} lanebg"/>')
    ll=lab.split("|")
    svg.append(f'<text x="16" y="{y0+16}" class="lane-lab">'+"".join(f'<tspan x="16" dy="{0 if i==0 else 13}">{esc(s)}</tspan>' for i,s in enumerate(ll))+'</text>')
    for a,b,ids in lanes[dom]:
        ri=placed[ids[0]]; lead=NB[ids[0]]
        x=gx(a)+4; w=CW*(b-a+1)-8; yy=y0+LANEPAD+ri*(CH+CGAP)
        st=bar_status(ids); cls="chip st-"+st; barcls="bar st-"+st
        if len(ids)==1 and lead["kind"]=="programme": cls+=" prog"
        if all(NB[i]["kind"]=="legal_act" for i in ids): cls+=" law"
        regions=sorted({NB[i]["region"] for i in ids},key=REGIONS.index)
        aria=("; ".join(P[i][3] for i in ids))+f". {dict(DOMAINS)[dom].replace('|',' ')}, {GATES[a][1]}"+(f" to {GATES[b][1]}" if b!=a else "")
        svg.append(f'<g class="{barcls}" tabindex="0" role="group" aria-label="{esc(aria)}" data-ids="{" ".join(ids)}" data-dom="{dom}" data-a="{a}" data-b="{b}" data-y="{yy}" data-row="{ri}">')
        svg.append(f'<rect x="{x}" y="{yy}" width="{w}" height="{CH}" rx="{10 if "prog" in cls else 2}" class="{cls}"/>')
        seg=CH/len(regions)
        for k,r in enumerate(regions):
            svg.append(f'<rect x="{x}" y="{yy+k*seg}" width="4" height="{seg}" class="stripe r-{r}" data-region="{r}" data-y0="{yy}" data-h="{CH}"/>')
        parts=[]
        for j,d in enumerate(ids):
            n=NB[d]; key=P[d][3]
            title=f'{n["label"]} — {n.get("ref") or ""} {n.get("date") or ""} · {n.get("status_note") or n["status"]}'
            reg=f'<tspan class="reg r-{n["region"]}">{esc(n["region"])}</tspan> ' if (j==0 or NB[ids[j-1]]["region"]!=n["region"]) else ''
            sep=f'<tspan class="sep" data-sep-for="{d}"> · </tspan>' if j else ''
            if j and " " in key and key.split(" ",1)[0]==P[ids[j-1]][3].split(" ",1)[0]: key=key.split(" ",1)[1]
            search=(n["label"]+" "+(n.get("ref") or "")+" "+P[d][3]).lower()
            t=(f'<tspan class="k" data-id="{d}" data-region="{n["region"]}" data-status="{n["status"]}" '
               f'data-verif="{n.get("verification") or "none"}" data-s="{esc(search)}">{reg}{esc(key)}<title>{esc(title)}</title></tspan>')
            if n.get("url"): t=f'<a href="{esc(n["url"])}" target="_blank" rel="noopener" tabindex="-1">{t}</a>'
            parts.append(sep+t)
        svg.append(f'<text x="{x+9}" y="{yy+13.5}" class="key">{"".join(parts)}</text>')
        svg.append('</g>')
    svg.append('</g>')
svg.append('</svg>')
SVG="\n".join(svg)

# ---------- Panel 1 ----------
cons=[n for n in g["nodes"] if n["kind"]=="consideration"]
addr={c["id"]:[] for c in cons}
for e in g["edges"]:
    if e["rel"]=="addresses" and e["target"] in addr: addr[e["target"]].append(e["source"])
panel_rows=[]
for c in cons:
    keys=[f'<button class="kref" data-go="{s}">{esc(P[s][3])}</button>' for s in sorted(addr[c["id"]]) if s in P]
    panel_rows.append(f'<li><b>{esc(c["label"])}.</b> {esc(c["scope"])} {("<i>Addressed in:</i> "+"; ".join(keys)+".") if keys else "<i class=gap>Gap — no document in the graph addresses this directly.</i>"}</li>')
PANEL="\n".join(panel_rows)

# ---------- Table 1 (sortable) ----------
ISSUER={"ICH":"ICH","EU":"EMA / European Commission","US":"FDA / US Congress","JP":"MHLW / PMDA","UK":"MHRA / UK Parliament","INTL":"OSWG"}
STL={"in_force":"In force","draft":"Draft","pending":"Pending","programme":"Programme","guidance":"Consensus","superseded":"Superseded","verify":"Unverified"}; VL=dict(VERIF); DOMI=[d for d,_ in DOMAINS]; STI=[s for s,_ in STATUSES]; VI=[v for v,_ in VERIF]
order=sorted(docs,key=lambda n:(DOMI.index(P[n["id"]][0]),P[n["id"]][1],P[n["id"]][3]))
trs=[]
for i,n in enumerate(order):
    key=P[n["id"]][3]; dom=dict(DOMAINS)[P[n["id"]][0]].replace("|"," ")
    link=f'<a href="{esc(n["url"])}" target="_blank" rel="noopener">{esc(n["label"])}</a>' if n.get("url") else esc(n["label"])
    note=n.get("status_note") or ""; note=note if len(note)<=90 else note[:88]+"…"
    sort=json.dumps([i,key.lower(),n["label"].lower(),DOMI.index(P[n["id"]][0])*10+P[n["id"]][1],ISSUER.get(n["region"],n["region"]),(n.get("ref") or "~").lower(),n.get("date") or "~",STI.index(n["status"]) if n["status"] in STI else 9,VI.index(n.get("verification")) if n.get("verification") in VI else 9])
    trs.append(f'<tr data-id="{n["id"]}" data-sort="{esc(sort)}"><td class="k"><span class="rdot r-{n["region"]}"></span><button class="kref" data-go="{n["id"]}">{esc(key)}</button></td><td>{link}</td><td>{esc(dom)}</td>'
               f'<td>{esc(ISSUER.get(n["region"],n["region"]))}</td><td class="mono">{esc(n.get("ref") or "—")}</td><td class="mono">{esc(n.get("date") or "—")}</td>'
               f'<td><span class="stchip st-{n["status"]}">{esc(STL.get(n["status"],n["status"]))}</span>{("<br><span class=note2>"+esc(note)+"</span>") if note else ""}</td>'
               f'<td>{esc(VL.get(n.get("verification"),"—"))}</td></tr>')
TABLE="\n".join(trs)
THEAD="".join(f'<th scope="col"><button class="sort" data-col="{i}" aria-sort="none">{esc(l)}<span class="arr" aria-hidden="true"></span></button></th>' for i,l in enumerate(["Key","Document","Domain","Issuer","Reference","Date","Status","Checked"],start=1))

def chips(name,items):
    return "".join(f'<button class="fchip" data-f="{name}" data-v="{v}" aria-pressed="true">{esc(l)}</button>' for v,l in items)
F_REGION=chips("region",[(r,r) for r in REGIONS]); F_STATUS=chips("status",STATUSES)
F_DOMAIN=chips("domain",[(d,l.replace("|"," ")) for d,l in DOMAINS]); F_VERIF=chips("verif",VERIF)
OVBTN="".join(f'<button class="ov" data-ov="{k}" aria-pressed="false">{esc(lab)}</button>' for k,(lab,_) in OVERLAYS.items())
GATE_OPTS="".join(f'<option value="{i}">{esc(l)}</option>' for i,(_,l) in enumerate(GATES))
PRESET_OPTS='<option value="">Preset…</option>'+"".join(f'<option value="{k}">{esc(v["label"])}</option>' for k,v in PRESETS.items())
OVJSON=json.dumps({k:ids for k,(lab,ids) in OVERLAYS.items()}); PRJSON=json.dumps(PRESETS)
GRAPHJSON=json.dumps(g,ensure_ascii=False,separators=(",",":")).replace("</","<\\/")

# ---------- Notes content ----------
SCOPE='''
<p class="figtitle"><b>Scope</b> — what this map covers and what it leaves out on purpose</p>
<div class="cols">
<div><h3>In scope</h3><ul>
<li>Synthetic oligonucleotide actives: antisense (incl. gapmers and splice-switching), siRNA, aptamers; conjugated (GalNAc, antibody, peptide) and lipid-nanoparticle-formulated forms.</li>
<li>Jurisdictions: ICH, EU centralised procedure and Clinical Trials Regulation, US FDA and federal statute, Japan MHLW/PMDA oligonucleotide texts, UK trial authorisation.</li>
<li>Development from candidate selection to post-approval obligations arising from paediatric and conditional-approval commitments.</li>
<li>Non-binding consensus (OSWG, Toxicologic Pathology Forum, review articles) where regulators are known to rely on it and no binding text exists — marked as such.</li>
</ul></div>
<div><h3>Out of scope (deliberately)</h3><ul>
<li>mRNA and gene-editing products (own regulatory frameworks, ATMP in the EU), except where a document explicitly covers both.</li>
<li>China NMPA, Health Canada, Australia TGA, Swissmedic and other national frameworks.</li>
<li>Pharmacovigilance, risk-management plans, labelling, pricing and reimbursement, GMP inspection law, environmental risk assessment.</li>
<li>Product-specific precedent (assessment reports, labels) — a possible future node type.</li>
</ul></div>
<div><h3>Reading the verification fields</h3><ul>
<li><b>Source opened</b>: the official page or PDF was read during the check.</li>
<li><b>URL on official site</b>: the document was located on the issuing body’s domain but not opened.</li>
<li><b>Secondary source opened</b>: a non-official source (law-firm summary, library record) was read because the primary text could not be reached.</li>
<li><b>Not checked live</b>: carried from prior knowledge. As of 28 October 2026 no document is in this state.</li>
<li>Negative results are recorded with the date they were established, so that “nothing found” is distinguishable from “not looked”.</li>
</ul></div>
</div>'''

HOWTO='''
<p class="figtitle"><b>Using this page</b></p>
<div class="cols">
<div><h3>Filters and presets</h3><ul>
<li>Filters apply to all views. <b>Dim</b> keeps non-matching documents at low opacity; <b>Hide</b> removes them, turns a programme-type selection into a filter, and closes up empty rows and lanes.</li>
<li>One built-in preset per programme type (jurisdictions, gate range, programme type, Hide). <b>Save as preset</b> stores the current filters for the selected programme type in this browser only; <b>Built-in presets</b> forgets saved ones.</li>
<li>The active view is in the address bar (<code>#map</code>, <code>#explore</code>, <code>#register</code>, <code>#notes</code>), so a view can be linked.</li>
</ul></div>
<div><h3>Export and print</h3><ul>
<li><b>Copy SVG</b> copies Figure 1 in the current theme and filter state; <b>Copy CSV</b> copies the register rows currently shown with all data fields; <b>Copy JSON</b> copies the whole graph.</li>
<li><b>Print</b> renders Figure 1 on A4 landscape pages (split at lane boundaries), then Panel 1 and the filtered Table 1 in portrait.</li>
<li>The data files (JSON, CSV, schema) and the generator are in the accompanying package; data are CC BY 4.0, code MIT.</li>
</ul></div>
<div><h3>Keyboard and colour</h3><ul>
<li>Tab moves between bars in Figure 1, ←/→ between keys of a series bar, Enter opens the detail sheet, Esc closes it; ←/→ also move between the view tabs.</li>
<li>No status is carried by colour alone: in force = solid outline; draft = short dashes; pending = long dashes; programme = rounded; non-binding consensus = dotted; unverified = hatched fill and red key; superseded = struck through; mixed series = dash-dot. Jurisdiction is always also given as a text tag.</li>
</ul></div>
</div>'''

CHANGES='''
<p class="figtitle"><b>What changed</b></p>
<h3 class="sub">Page v0.4.0 — Phase C (28 October 2026)</h3>
<ul class="chg">
<li><b>One page, four views.</b> Map (default), Explore (force graph), Register (Table 1) and Notes share one filter panel; the active view is in the URL hash (<code>#map</code>, <code>#explore</code>, <code>#register</code>, <code>#notes</code>) so a view can be linked. The former explorer page is retired; its detail sheet is now reachable from every view (click a key in the figure, a node in Explore, or a key in the register or in Panel 1).</li>
<li><b>Explore</b> draws documents with their <code>references</code>, <code>amends</code> and <code>supersedes</code> relations; considerations (<code>addresses</code>) and gates (derived <code>applies_at</code>, <code>supports</code>, <code>prerequisite_for</code>) are switchable layers. Dim/Hide and programme-type selections behave as in the map.</li>
<li><b>Presets.</b> One built-in preset per programme type (jurisdictions, gate range, programme-type filter in Hide mode); the current filter state can be saved over a preset in the browser (local storage, this browser only) and restored to the built-in set.</li>
<li><b>Register</b> sorts on every column; “Copy CSV” copies the rows currently shown with all data fields.</li>
<li><b>Export.</b> Copy SVG resolves the colours of the active theme (light or dark), so the clipboard SVG no longer depends on the page theme. Print (⌘/Ctrl-P) renders Figure 1 on an A4 landscape page and Panel 1 and the filtered Table 1 on A4 portrait pages; filters and the other views are omitted.</li>
<li><b>Accessibility.</b> Bars are keyboard targets (Tab between bars, ←/→ between keys in a series bar, Enter opens the detail sheet, Esc closes it). Status is no longer carried by colour alone: every status has a distinct outline pattern or shape — see <i>Accessibility check</i> below. Hide mode now removes lanes with no visible bar.</li>
</ul>
<h3 class="sub">Data v0.3 (28 October 2026)</h3>
<ul class="chg">
<li><b>Data model:</b> every node carries <code>domain</code>, <code>gate_from</code>/<code>gate_to</code>, a unique <code>key</code>, optional <code>group</code>, <code>triggers</code> and <code>last_checked</code>; <code>phase</code> and stored <code>governs_phase</code> edges are gone (gate links are regenerated at build time under <code>derived</code>). Figure placement and series aggregation now come from the data; the renderer holds no layout facts.</li>
<li><b>Content:</b> the intrathecal/CNS gap is closed with four consensus and methodology references (two opened and cited in full); hepatotoxicity and nephrotoxicity each gained an FDA clinical guidance; revision history added (Q1A(R2) → consolidated Q1, E6(R2) → E6(R3), E9 + E9(R1), 2014 expedited-programs guidance → 2024 accelerated-approval draft).</li>
<li><b>Verification:</b> the four US statutes were re-verified on primary govinfo texts; ICH Q14 on the EMA page; the sponsor-investigator IND draft via its Federal Register notice; no document remains “not checked live”. EDQM newsroom and Pharmeuropa 38.2 confirmed the absence of an oligonucleotide chapter (negative result, dated).</li>
<li><b>Tooling:</b> <code>validate.py</code> (schema, integrity, unique keys, span and group consistency, orphan check, optional link report) and a CI workflow that runs it on every change and the link check quarterly.</li>
<li><b>Second pass (same day):</b> Korte et al. 2020 fully cited; USP negative result dated; EMA drug–device guideline and 21 CFR Part 4 added for device-delivered CNS programmes; accelerated assessment and conditional MA spans start at Phase 3; Rare Pediatric Disease voucher linked to the govinfo text of Pub. L. 119-75.</li>
</ul>'''

A11Y='''
<p class="figtitle"><b>Accessibility check</b> (28 October 2026) — status and jurisdiction colours under simulated colour-vision deficiency</p>
<div class="cols">
<div><h3>Method</h3><p class="small">The light-theme palette was transformed with the Viénot–Brettel–Mollon matrices for protanopia, deuteranopia and tritanopia in linear RGB, and the smallest CIE76 colour difference (ΔE) between any two colours of a set was recorded. Values below about 10 are hard to tell apart; below 5 they are practically identical.</p>
<table class="mini"><thead><tr><th>Set</th><th>Normal</th><th>Protan</th><th>Deutan</th><th>Tritan</th></tr></thead><tbody>
<tr><td>Status fill tints</td><td>2.8</td><td>2.4</td><td>1.9</td><td>3.0</td></tr>
<tr><td>Status outline colours</td><td>14.0</td><td>12.4</td><td>14.7</td><td>10.1</td></tr>
<tr><td>Jurisdiction colours</td><td>32.0</td><td>6.5</td><td>3.1</td><td>14.3</td></tr>
</tbody></table></div>
<div><h3>Finding</h3><ul>
<li>The pale fill tints were never meant to be told apart on their own, and they are not: even with normal vision the closest pair (non-binding consensus vs mixed) differs by ΔE 2.8.</li>
<li>Outline colours remain distinguishable under all three simulations (minimum ΔE 10.1, in-force blue vs programme green under tritanopia).</li>
<li>Jurisdiction colours collapse under protanopia (ICH vs JP, US vs UK) and deuteranopia (EU vs INTL). They are redundant by design: every key carries its jurisdiction tag as text and the register names the issuer.</li>
</ul></div>
<div><h3>Consequence (implemented)</h3><ul>
<li>Every status now has a second, colour-independent cue: in force = solid outline; draft = short dashes; pending = long dashes; programme = rounded pill; non-binding consensus = dotted; unverified = hatched fill; superseded = struck-through key; mixed series = dash-dot. Binding legal acts additionally have a heavier outline.</li>
<li>The same cues are used in the legend swatches and in the status chips of the register.</li>
<li>Not yet done: a test with a screen reader; the figure’s bars carry <code>aria-label</code>s but the SVG as a whole is a single image for assistive technology.</li>
</ul></div>
</div>'''

OPEN='''
<p class="figtitle" id="open"><b>Open items</b> — everything still to be checked or decided, as of 28 October 2026</p>
<div class="cols open">
<div><h3>A · Needs a practitioner or a decision</h3><ol>
<li><b>Span review.</b> All gate spans were set by one author. Priority: the quality lane (do all ICH Q texts really engage at CTA?), the paediatric lane, and the rare lane. Accelerated assessment and conditional MA were moved to start at Phase 3 (strategy) rather than at filing (request) — confirm.</li>
<li><b>Trigger coverage.</b> The six programme-type sets were seeded by one author; baseline documents that should also carry a trigger (e.g. ICH M3(R2) for intrathecal, ICH S11 for every paediatric programme) have not been reviewed.</li>
<li><b>Paediatric-oncology set</b> — review by someone who has taken a PIP through PDCO.</li>
<li><b>Presets.</b> The six built-in presets (jurisdictions and gate range per programme type) are one author’s defaults; a sponsor of each programme type should confirm them.</li>
<li><b>Node type for product precedent</b> (assessment reports and labels of approved oligonucleotides) — add or not.</li>
<li><b>Default view</b> — keep jurisdiction stripes on a mixed map, or default to one jurisdiction.</li>
<li><b>Authorship.</b> CITATION.cff names and ORCID; licence holder in LICENSE.</li>
</ol></div>
<div><h3>B · Sources not fully reached</h3><ol start="8">
<li><b>IT nerve-fibre opinion</b> (Toxicologic Pathology Forum): DOI, authors and year not found; only a library record.</li>
<li><b>Rare Pediatric Disease voucher:</b> Pub. L. 119-75 confirmed on govinfo, but the reauthorising sections (CAA 2026 §§6601–6605) were not reached; the 2029-09-30 date rests on a law-firm summary. Voucher-award sunset unknown.</li>
<li><b>PIP format guideline 2014/C 338/01:</b> EUR-Lex text not opened; EMA news of 30 Sept 2014 corroborates.</li>
<li><b>39 documents</b> are “URL on official site” without the page opened. A one-time pass opening each would move them to “source opened”; the quarterly link check catches dead links, not content drift.</li>
<li><b>Korte et al. 2020</b> (IT NHP lesions): citation from a library record; full text not read.</li>
</ol></div>
<div><h3>C · Moving targets (re-check dates)</h3><ol start="13">
<li><b>EU pharma package:</b> Parliament adoption, OJ publication, final act numbers — monthly until published.</li>
<li><b>EMA oligonucleotide quality guideline:</b> adoption after the Jan 2025 consultation.</li>
<li><b>FDA oligonucleotide nonclinical draft</b> (Nov 2024): finalisation.</li>
<li><b>FDA Plausible Mechanism draft</b> (Feb 2026): finalisation; docket number.</li>
<li><b>ICH Q1 consolidated</b> (Step 4 planned Nov 2026) and <b>M4Q(R2)</b> (Jun 2027): on adoption, Q1A(R2) becomes superseded.</li>
<li><b>ICH E14/S7B Q&amp;A (R1)</b> 2026 update: noted in the inventory, not opened.</li>
<li><b>FDA accelerated-approval draft</b> (Dec 2024): finalisation; then supersedes part of the 2014 guidance.</li>
<li><b>Stepwise PIP:</b> integration into routine EMA practice announced after the Feb 2026 report.</li>
<li><b>Pharmacopoeias:</b> negative results for Ph. Eur. and USP dated 2026-10-28; re-check each Pharmeuropa and Pharmacopeial Forum issue.</li>
</ol></div>
</div>
<div class="cols open" style="margin-top:14px">
<div><h3>D · Product and tooling</h3><ol start="22">
<li>Print layout verified in Chromium only; named pages (<code>page: fig</code> for the landscape figure) need checking in Firefox and Safari.</li>
<li>Screen-reader pass of the figure (bars carry labels, the SVG is otherwise one image) and of the Explore view (canvas only; the register is the accessible equivalent).</li>
<li>CI link check is informational; decide whether a 404 on an official URL should fail the build.</li>
<li>Saved presets live in the browser’s local storage; a shareable preset would need the filter state in the URL, which this page keeps out of the hash on purpose (plain view names only).</li>
</ol></div>
<div><h3>Closed in Phase C</h3><ul class="small">
<li>Hide mode now removes empty lanes instead of keeping a one-row minimum.</li>
<li>Status tints run through a colour-vision simulation; non-colour cues added (see <i>Accessibility check</i>).</li>
<li>SVG export follows the active theme.</li>
<li>Explorer and map merged into one page with shared filters.</li>
</ul></div>
</div>'''

AUDIT='''
<p class="figtitle"><b>Audit of data v0.2</b> (28 October 2026, before the v0.3 changes above), measured on the graph itself</p>
<div class="cols">
<div><h3>Structure</h3><ul>
<li><b>No domain dimension.</b> 50 of 92 nodes are typed <code>guideline</code>, which does not separate quality from nonclinical from clinical. 26 nodes sat in a <code>cross_cutting</code> phase bucket that carries no information. The map introduces six domains instead.</li>
<li><b>Phase is a point, applicability is a span.</b> 64 documents had <code>governs_phase</code> edges, only 7 to more than one gate; 22 converged on “filing” and 14 on “nonclinical”, making those milestones hubs with no discriminating value. The map replaces the edges by placement across gates.</li>
<li><b>Modality is almost unused.</b> 81 of 92 nodes carry <code>all_oligo</code>; programme-type triggers (AOC, LNP, intrathecal, individualised, paediatric oncology) existed only in prose. The programme-type buttons are a first mapping and now live in the data.</li>
<li><b>Edge mix.</b> 73 of 148 relations were <code>governs_phase</code>; the remaining <code>references</code>, <code>amends</code> and <code>addresses</code> edges are the ones worth drawing, and Explore now shows only those by default.</li>
</ul></div>
<div><h3>Content</h3><ul>
<li><b>Intrathecal / CNS delivery</b> was a consideration with no document addressing it — the most important gap for paediatric brain-tumour programmes (closed in v0.3).</li>
<li><b>Hepatotoxicity and nephrotoxicity</b> each hung on a single document (closed in v0.3).</li>
<li><b>8 documents were not checked live</b>, among them the four US statutes (closed in v0.3).</li>
<li><b>Ph. Eur. and USP</b> have no dedicated oligonucleotide chapter that could be confirmed; that negative result is itself a finding worth stating (dated in v0.3).</li>
<li><b>Two designations were drawn as applying at filing only</b> (accelerated assessment, conditional MA) although their strategy starts earlier; moved to Phase 3, review pending.</li>
</ul></div>
<div><h3>Presentation (previous explorer)</h3><ul>
<li>Force layout is non-deterministic: positions differ on every load, so the view cannot serve as a reference figure. The map is the reference; Explore is for navigation.</li>
<li>Colour carried jurisdiction, but the decision-relevant variable is status: ICH is 96% in force, US documents are 27% drafts.</li>
<li>Labels averaged 45 characters; keys of ≤24 characters are needed for a figure and a citable register.</li>
</ul></div>
</div>'''

ROADMAP='''
<p class="figtitle"><b>Roadmap</b> — from reference map to maintained open resource</p>
<div class="rm">
<section><h3>Phase A · Data model v0.3 <span class="when done">done · 28 Oct 2026</span></h3>
<p>Goal: one source of truth from which both the map and the explorer are generated, with no layout decisions hidden in renderer code.</p>
<ul>
<li><b><code>domain</code></b> (quality, nonclin, clinical, paed, rare, auth) replaces the <code>cross_cutting</code> bucket; zero nodes without a domain.</li>
<li><b><code>gate_from</code> / <code>gate_to</code></b> replace <code>phase</code>; gate links are regenerated from spans, not stored.</li>
<li><b><code>key</code></b> (unique, ≤24 characters) and <b><code>group</code></b> so that series aggregation is data, not code.</li>
<li><b><code>triggers</code></b>: programme types a document is engaged by (<code>aoc</code>, <code>lnp</code>, <code>galnac</code>, <code>intrathecal</code>, <code>individualised</code>, <code>paed_onc</code>).</li>
<li><b><code>supersedes</code> edges</b> for revisions and <code>last_checked</code> per document.</li>
<li><b>Validation in CI:</b> JSON schema, referential integrity, unique keys, span sanity, link check with HTTP status per document.</li>
</ul></section>
<section><h3>Phase B · Content completion <span class="when done">done except practitioner review · 28 Oct 2026</span></h3>
<p>Goal: close the gaps the audit found and raise every document to “source opened”.</p>
<ul>
<li><b>Intrathecal / CNS route — done.</b> Four consensus/methodology references added (see Panel 1); no binding agency guidance specific to the IT route was found, stated as a dated negative result. Device/combination aspects covered by the EMA drug–device guideline and 21 CFR Part 4, both opened.</li>
<li><b>Class toxicities — done.</b> FDA DILI (2009) and renal-impairment PK (2024) guidances added and linked.</li>
<li><b>Verify the eight knowledge-only entries — done.</b> Zero remain; one (the 2014 PIP format guideline) rests on an EMA news item rather than the EUR-Lex text.</li>
<li><b>Pharmacopoeias — done.</b> Negative results recorded and dated for Ph. Eur. and USP, 28 Oct 2026.</li>
<li><b>Review spans with practitioners — open (item 1).</b></li>
<li><b>Scope statement — done.</b></li>
</ul></section>
<section><h3>Phase C · Product <span class="when done">done · 28 Oct 2026</span></h3>
<p>Goal: one page, three views, shared filters, stable links.</p>
<ul>
<li><b>Views — done.</b> Map (default), Explore (documents with <code>references</code>/<code>amends</code>/<code>supersedes</code>; considerations and gates as layers), Register (sortable), Notes. One filter panel for all; the active view is in the URL hash.</li>
<li><b>Filters — done.</b> Jurisdiction, status, domain, verification, gate range, programme type, search, Dim/Hide, plus one built-in preset per programme type and user-saved presets (browser-local).</li>
<li><b>Export — done.</b> Copy SVG (theme-resolved), Copy CSV of the filtered register, A4 print stylesheet (Figure 1 landscape; Panel 1 and Table 1 portrait).</li>
<li><b>Accessibility — done, with two open checks (items 22–23).</b> Keyboard access to bars and keys; colour-vision simulation of the palette and non-colour status cues.</li>
</ul></section>
<section><h3>Phase D · Release and governance <span class="when">next</span></h3>
<p>Goal: citable, correctable, maintained.</p>
<ul>
<li><b>Repository</b> with the generator, data, schema, CONTRIBUTING and an issue template per correction (one document per issue: URL, number, date, status). CI runs the validation above on every change.</li>
<li><b>Zenodo deposit</b> with a versioned DOI; CITATION.cff completed; the DOI shown on the page.</li>
<li><b>Re-verification cadence:</b> quarterly link and status check; a changelog that records every status transition (draft → final, in force → superseded) with the date it was noticed.</li>
<li><b>Companion article:</b> a regulatory map for oligonucleotide therapeutics with a paediatric-oncology worked example. Figure 1 is this map, Panel 1 the considerations, Table 1 the register, the JSON the supplement. The map’s value to a reviewer is that it is generated, so the figure cannot drift from the data.</li>
<li><b>Outreach</b> to the groups that would use and correct it: oligonucleotide therapeutics societies, paediatric trial networks and strategy forums, regulatory-science working groups.</li>
</ul></section>
<section><h3>Open decisions</h3><p>Consolidated with everything else still unverified in <a href="#open">Open items</a> below.</p></section>
</div>'''

LEGEND_STATUS='''<div class="keyrow">
  <span><b>Status</b></span>
  <span><i class="sw" style="background:var(--st-in_force);border-color:var(--st-in_force-b)"></i>In force</span>
  <span><i class="sw" style="background:var(--st-draft);border-color:var(--st-draft-b);border-style:dashed"></i>Draft</span>
  <span><i class="sw sw-long" style="background:var(--st-pending);border-color:var(--st-pending-b)"></i>Pending adoption</span>
  <span><i class="sw" style="background:var(--st-programme);border-color:var(--st-programme-b);border-radius:6px"></i>Programme / designation</span>
  <span><i class="sw" style="background:var(--st-guidance);border-color:var(--st-guidance-b);border-style:dotted"></i>Non-binding consensus</span>
  <span><i class="sw sw-hatch" style="border-color:var(--st-verify-b);border-style:dashed"></i>Unverified</span>
  <span><i class="sw" style="background:var(--st-guidance);border-color:var(--st-guidance-b)"></i><s>Superseded</s></span>
  <span><i class="sw sw-dd" style="background:var(--st-mixed);border-color:var(--st-mixed-b)"></i>Series with mixed status</span>
</div>
<div class="keyrow">
  <span><b>Jurisdiction</b></span>
  %%JUR%%
  <span style="margin-left:auto">Bold outline = binding legal act · rounded = designation or programme · hatched bar or red key = unverified</span>
</div>'''.replace("%%JUR%%","".join(f'<span><i class="swd" style="background:var(--r-{r})"></i>{r}</span>' for r in REGIONS))

# ---------- page template ----------
page=r'''<title>Oligo Regulatory Map</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap">
<style>
/* Journal-figure page. Status = bar fill + outline pattern; jurisdiction = stripe + text tag. One red accent. */
:root{--bg:#ffffff;--ink:#111111;--ink2:#555555;--ink3:#8a8a8a;--rule:#1a1a1a;--hair:#d9d9d9;
  --lane:#fafafa;--lane-alt:#f3f3f3;--accent:#c8102e;--accent-soft:#fbe9ec;--mask:rgba(0,0,0,.05);--focus:#1d5fd1;
  --st-in_force:#dce8f2;--st-in_force-b:#4f7ea8;--st-draft:#fff0cf;--st-draft-b:#c98f12;
  --st-pending:#ece4f8;--st-pending-b:#7b5cb8;--st-programme:#e2f2e4;--st-programme-b:#3f8f52;
  --st-guidance:#f0f0f0;--st-guidance-b:#8a8a8a;--st-verify:#fde6e9;--st-verify-b:#c8102e;--st-mixed:#e9eef2;--st-mixed-b:#6b8093;
  --r-ICH:#3f6fb0;--r-EU:#1f9d8f;--r-US:#c6603a;--r-JP:#9a5bb8;--r-UK:#4e8d4a;--r-INTL:#7d8287;
  --serif:"Source Serif 4",Georgia,"Times New Roman",serif;--sans:"Helvetica Neue",Helvetica,Arial,sans-serif;--mono:ui-monospace,Menlo,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121212;--ink:#ececec;--ink2:#b5b5b5;--ink3:#8c8c8c;
  --rule:#e6e6e6;--hair:#333;--lane:#171717;--lane-alt:#1e1e1e;--accent:#ff4d5e;--accent-soft:#3a1a1f;--mask:rgba(255,255,255,.06);--focus:#7fb0ff;
  --st-in_force:#1f3447;--st-in_force-b:#7fb0dc;--st-draft:#3d2e0c;--st-draft-b:#e4b24a;--st-pending:#2c2240;--st-pending-b:#b59be6;
  --st-programme:#1c3322;--st-programme-b:#7cc78e;--st-guidance:#262626;--st-guidance-b:#9a9a9a;--st-verify:#3a1a1f;--st-verify-b:#ff6b7a;
  --st-mixed:#232b32;--st-mixed-b:#9db0c2;--r-ICH:#6f9fe0;--r-EU:#39c4b4;--r-US:#e8865e;--r-JP:#c084e0;--r-UK:#78bf72;--r-INTL:#aab2b5;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#121212;--ink:#ececec;--ink2:#b5b5b5;--ink3:#8c8c8c;--rule:#e6e6e6;--hair:#333;--lane:#171717;--lane-alt:#1e1e1e;
  --accent:#ff4d5e;--accent-soft:#3a1a1f;--mask:rgba(255,255,255,.06);--focus:#7fb0ff;--st-in_force:#1f3447;--st-in_force-b:#7fb0dc;--st-draft:#3d2e0c;--st-draft-b:#e4b24a;
  --st-pending:#2c2240;--st-pending-b:#b59be6;--st-programme:#1c3322;--st-programme-b:#7cc78e;--st-guidance:#262626;--st-guidance-b:#9a9a9a;
  --st-verify:#3a1a1f;--st-verify-b:#ff6b7a;--st-mixed:#232b32;--st-mixed-b:#9db0c2;--r-ICH:#6f9fe0;--r-EU:#39c4b4;--r-US:#e8865e;--r-JP:#c084e0;--r-UK:#78bf72;--r-INTL:#aab2b5;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--serif);font-size:15px;line-height:1.5;
  padding-block:24px 56px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.wrap{max-width:1180px;margin:0 auto}
h1{font-family:var(--sans);font-size:22px;letter-spacing:-.01em;margin:0 0 4px;text-wrap:balance}
h3{font-family:var(--sans);font-size:13.5px;margin:0 0 6px} h3.sub{margin:14px 0 4px}
.byline{font-family:var(--sans);font-size:12.5px;color:var(--ink2);margin:0 0 14px}
.figtitle{font-family:var(--sans);font-size:14px;margin:26px 0 8px} .figtitle b{font-weight:700}
code{font-family:var(--mono);font-size:.9em;background:var(--lane-alt);padding:0 4px;border-radius:3px}
button{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
/* tabs */
.tabs{display:flex;gap:4px;align-items:center;border-bottom:1.5px solid var(--rule);margin:0 0 12px;font-family:var(--sans);font-size:13px;flex-wrap:wrap}
.tab{background:transparent;border:0;border-bottom:3px solid transparent;padding:8px 12px 7px;cursor:pointer;color:var(--ink2);font-weight:700;margin-bottom:-1.5px}
.tab[aria-selected="true"]{color:var(--ink);border-bottom-color:var(--accent)}
.tabs .tools{margin-left:auto;display:flex;gap:6px;align-items:center;padding-bottom:4px}
.view{display:none} .view.on{display:block}
/* filters */
.filters{font-family:var(--sans);font-size:12px;border:1px solid var(--hair);border-radius:6px;padding:10px 12px;margin:0 0 10px;
  display:grid;grid-template-columns:1fr 1fr;gap:8px 18px}
.frow{display:flex;flex-wrap:wrap;gap:5px;align-items:center;min-width:0}
.frow .lab{color:var(--ink2);min-width:92px;font-weight:700;font-size:11px;letter-spacing:.03em;text-transform:uppercase}
.fchip,.ov,.tbtn{color:var(--ink);background:transparent;border:1px solid var(--hair);border-radius:14px;padding:3px 9px;cursor:pointer;line-height:1.3;font-size:12px;font-family:var(--sans)}
.fchip[aria-pressed="false"]{opacity:.42;text-decoration:line-through}
.ov[aria-pressed="true"]{border-color:var(--accent);background:var(--accent-soft)}
.tbtn{border-radius:6px} .tbtn[aria-pressed="true"]{background:var(--accent-soft);border-color:var(--accent)}
.frow input[type=search],.frow select,.viewbar select{font:inherit;font-family:var(--sans);font-size:12px;color:var(--ink);background:var(--bg);border:1px solid var(--hair);border-radius:6px;padding:4px 8px}
.frow input[type=search]{min-width:200px;flex:1}
.fwide{grid-column:1 / -1}
.count{margin-left:auto;color:var(--ink2);font-variant-numeric:tabular-nums}
.seg{display:inline-flex;border:1px solid var(--hair);border-radius:6px;overflow:hidden}
.seg button{color:var(--ink);background:transparent;border:0;padding:3px 9px;cursor:pointer;font-family:var(--sans);font-size:12px}
.seg button[aria-pressed="true"]{background:var(--lane-alt);font-weight:700}
.viewbar{font-family:var(--sans);font-size:12px;display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 8px;color:var(--ink2)}
/* figure */
#printfigs{display:none}
.figbox{border-top:1.5px solid var(--rule);border-bottom:1.5px solid var(--rule);padding:12px 0 6px;overflow-x:auto}
svg.fig{display:block;font-family:var(--sans);max-width:none}
.spine{stroke:var(--rule);stroke-width:1.2;fill:none} .grid{stroke:var(--hair);stroke-width:.6}
.gate{font-size:11px;font-weight:700;fill:var(--ink)} .gate-sub{font-size:9px;fill:var(--ink2)} .eop2{fill:var(--accent)}
.lane{fill:var(--lane)} .lane.alt{fill:var(--lane-alt)}
.lane-lab{font-size:10.5px;font-weight:700;fill:var(--ink);letter-spacing:.02em}
.colmask{fill:var(--mask);opacity:0;pointer-events:none} .colmask.out{opacity:1}
.chip{stroke-width:.9}
.chip.st-in_force{fill:var(--st-in_force);stroke:var(--st-in_force-b)}
.chip.st-draft{fill:var(--st-draft);stroke:var(--st-draft-b);stroke-dasharray:3 2}
.chip.st-pending{fill:var(--st-pending);stroke:var(--st-pending-b);stroke-dasharray:7 2.5}
.chip.st-programme{fill:var(--st-programme);stroke:var(--st-programme-b)}
.chip.st-guidance{fill:var(--st-guidance);stroke:var(--st-guidance-b);stroke-dasharray:1 2}
.chip.st-verify{fill:url(#hatch);stroke:var(--st-verify-b);stroke-dasharray:3 2}
.chip.st-mixed{fill:var(--st-mixed);stroke:var(--st-mixed-b);stroke-dasharray:7 2 1.5 2}
.chip.st-superseded{fill:var(--st-guidance);stroke:var(--st-guidance-b)} .bar.st-superseded .k{text-decoration:line-through}
.chip.law{stroke-width:1.6}
.hatch-bg{fill:var(--st-verify)} .hatch-ln{stroke:var(--st-verify-b);stroke-width:.7;opacity:.55}
.stripe{pointer-events:none}
.r-ICH{fill:var(--r-ICH)} .r-EU{fill:var(--r-EU)} .r-US{fill:var(--r-US)} .r-JP{fill:var(--r-JP)} .r-UK{fill:var(--r-UK)} .r-INTL{fill:var(--r-INTL)}
.key{font-size:9.5px;fill:var(--ink)} .reg{font-size:8px;font-weight:700;letter-spacing:.04em} .sep{fill:var(--ink3)}
svg.fig a{text-decoration:none} .k{cursor:pointer} .k[data-status="verify"]{fill:var(--st-verify-b)} .k:hover,.k.kf{fill:var(--accent)} .k.kf{text-decoration:underline}
.bar{outline:none} .bar:focus-visible .chip{stroke:var(--focus);stroke-width:2.2;stroke-dasharray:none}
.bar.hi .chip{stroke:var(--accent);stroke-width:2} .k.hi{font-weight:700}
.bar.lo,.k.lo{opacity:.22} .bar.off,.k.off,.sep.off,.lanegrp.off{display:none}
/* legend */
.legend{font-size:13.5px;margin:10px 0 0} .legend.abbr{font-size:12.5px;color:var(--ink2);margin-top:6px}
.keyrow{font-family:var(--sans);font-size:11.5px;display:flex;flex-wrap:wrap;gap:6px 14px;margin:8px 0 0;color:var(--ink2)}
.keyrow span{display:inline-flex;align-items:center;gap:5px}
.sw{display:inline-block;width:16px;height:10px;border-radius:2px;border:1px solid}
.sw-long{border-style:dashed;border-width:1px} .sw-hatch{background:repeating-linear-gradient(45deg,var(--st-verify) 0 2px,var(--st-verify-b) 2px 3px)}
.sw-dd{border-style:double;border-width:3px;height:12px}
.swd{display:inline-block;width:10px;height:10px;border-radius:50%}
/* panel, table */
.panel{border:1px solid var(--rule);padding:14px 18px;margin:30px 0 0} .panel h2{font-family:var(--sans);font-size:14px;margin:0 0 8px}
.panel ol{margin:0;padding-left:20px} .panel li{margin:0 0 7px;font-size:14px} .panel li b{font-weight:600} .panel li i{color:var(--ink2)} .gap{color:var(--accent)}
.kref{background:none;border:0;padding:0;cursor:pointer;font:inherit;color:var(--ink);text-decoration:underline;text-decoration-color:var(--ink3);text-underline-offset:2px}
.kref:hover{color:var(--accent)} td.k .kref{font-weight:600;font-family:var(--sans);font-size:12px;text-align:left;display:inline}
table.reg{border-collapse:collapse;width:100%;min-width:900px;table-layout:fixed;font-family:var(--sans);font-size:12px;margin-top:4px}
table.reg thead th{text-align:left;font-weight:700;border-top:1.5px solid var(--rule);border-bottom:1px solid var(--rule);padding:4px 4px 3px}
.sort{background:none;border:0;padding:3px 4px;cursor:pointer;font-weight:700;font-family:var(--sans);font-size:12px;display:inline-flex;gap:4px;align-items:center;border-radius:4px}
.sort:hover{background:var(--lane-alt)} .sort .arr::after{content:"↕";color:var(--ink3);font-weight:400}
.sort[aria-sort="ascending"] .arr::after{content:"↑";color:var(--accent)} .sort[aria-sort="descending"] .arr::after{content:"↓";color:var(--accent)}
table.reg tbody td{padding:6px 8px;vertical-align:top;border-bottom:1px solid var(--hair)} table.reg tbody tr:last-child td{border-bottom:1.5px solid var(--rule)}
table.reg tbody tr.off{display:none} table.reg tbody tr.sel td{background:var(--accent-soft)}
td.mono{font-family:var(--mono);font-size:11px;overflow-wrap:anywhere} .note2{color:var(--ink2);font-size:11px}
.rdot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:0}
.stchip{display:inline-block;font-size:11px;font-weight:700;padding:1px 7px;border-radius:10px;border:1px solid}
.stchip.st-in_force{background:var(--st-in_force);border-color:var(--st-in_force-b)} .stchip.st-draft{background:var(--st-draft);border-color:var(--st-draft-b);border-style:dashed}
.stchip.st-pending{background:var(--st-pending);border-color:var(--st-pending-b);border-style:dashed} .stchip.st-programme{background:var(--st-programme);border-color:var(--st-programme-b)}
.stchip.st-guidance{background:var(--st-guidance);border-color:var(--st-guidance-b);border-style:dotted} .stchip.st-superseded{background:var(--st-guidance);border-color:var(--st-guidance-b);text-decoration:line-through}
.stchip.st-verify{background:repeating-linear-gradient(45deg,var(--st-verify) 0 3px,var(--accent-soft) 3px 4px);border-color:var(--st-verify-b);border-style:dashed}
.tablewrap{overflow-x:auto} .fn{font-size:12.5px;color:var(--ink2);margin-top:6px}
a{color:var(--ink);text-decoration:underline;text-decoration-color:var(--ink3);text-underline-offset:2px}
.cols{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;font-size:13.5px} .cols ul{margin:0;padding-left:18px} .cols li{margin-bottom:6px} .small{font-size:12.5px;color:var(--ink2)}
table.mini{border-collapse:collapse;font-family:var(--sans);font-size:12px;margin-top:6px;width:100%} table.mini th,table.mini td{text-align:left;padding:3px 6px;border-bottom:1px solid var(--hair);font-variant-numeric:tabular-nums} table.mini th{border-top:1.5px solid var(--rule);border-bottom:1px solid var(--rule)}
.rm section{border-top:1px solid var(--hair);padding:12px 0 6px} .rm ul{margin:4px 0 0;padding-left:20px} .rm li{margin-bottom:6px;font-size:14px}
.rm p{margin:0 0 4px;font-size:14px;color:var(--ink2)}
.when.done{color:var(--st-programme-b);font-weight:700} .open ol{margin:0;padding-left:20px} .open li{margin-bottom:6px;font-size:13.5px} .chg{font-size:14px;padding-left:20px;margin:0} .chg li{margin-bottom:6px} .when{font-weight:400;color:var(--ink2);margin-left:8px;font-size:12px}
.note{font-size:13px;color:var(--ink2);margin:26px 0 0;border-top:1px solid var(--hair);padding-top:10px}
/* explore */
.xwrap{position:relative;height:72vh;min-height:420px;border:1px solid var(--hair);border-radius:6px;overflow:hidden;background:var(--lane)}
svg.graph{width:100%;height:100%;display:block;touch-action:none;font-family:var(--sans)}
.lane-label{fill:var(--ink2);font-family:var(--sans);font-size:10px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}
.lane-rule{stroke:var(--hair);stroke-dasharray:3 5}
.link{stroke:var(--ink3);stroke-width:1px;opacity:.7} .link.hl{stroke:var(--accent);stroke-width:1.8px;opacity:1}
.link.derived{stroke-dasharray:2 3;opacity:.45} .link.dim{opacity:.06}
.node{cursor:pointer;outline:none} .node text{font-size:10px;fill:var(--ink);paint-order:stroke;stroke:var(--lane);stroke-width:3px;stroke-linejoin:round;pointer-events:none}
.node.dim{opacity:.14} .node.lo{opacity:.22}
.node .shape{stroke:var(--bg);stroke-width:1.2px} .node.sel .shape{stroke:var(--ink);stroke-width:2.5px} .node.hi .shape{stroke:var(--accent);stroke-width:2.5px}
.node:focus-visible .shape{stroke:var(--focus);stroke-width:2.5px}
.xcount{font-family:var(--sans);font-size:11px;color:var(--ink2);position:absolute;left:10px;bottom:10px;background:var(--bg);border:1px solid var(--hair);border-radius:20px;padding:3px 9px}
.xhint{position:absolute;right:10px;bottom:10px;font-family:var(--sans);font-size:11px;color:var(--ink2);background:var(--bg);border:1px solid var(--hair);border-radius:6px;padding:4px 8px}
.xfail{position:absolute;inset:0;display:none;align-items:center;justify-content:center;font-family:var(--sans);font-size:13px;color:var(--ink2);padding:20px;text-align:center}
/* detail sheet */
.sheet{position:fixed;top:0;right:0;height:100%;width:360px;max-width:92%;background:var(--bg);border-left:1px solid var(--hair);box-shadow:-6px 0 24px rgba(0,0,0,.12);
  transform:translateX(100%);transition:transform .2s ease;overflow:auto;z-index:20;padding:16px 16px calc(20px + env(safe-area-inset-bottom,0px));font-family:var(--sans);font-size:13px}
.sheet.open{transform:none}
.sheet .x{position:absolute;top:10px;right:10px;background:var(--lane-alt);border:1px solid var(--hair);border-radius:6px;width:30px;height:30px;font-size:16px;line-height:1;cursor:pointer}
.sheet h2{font-family:var(--sans);font-size:16px;margin:4px 0 10px;padding-right:34px;letter-spacing:-.01em}
.d-kind{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink2)}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px} .badge{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:700;border-radius:6px;padding:2px 7px;border:1px solid}
.kv{font-size:12.5px;color:var(--ink2);margin:2px 0} .kv b{color:var(--ink);font-weight:700}
.scope{font-size:13px;margin:10px 0;font-family:var(--serif)}
.oligo{font-size:12.5px;background:var(--lane-alt);border-left:3px solid var(--accent);padding:8px 10px;margin:10px 0;font-family:var(--serif)}
.oligo span{display:block;font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--accent);margin-bottom:3px;font-weight:700;font-family:var(--sans)}
.src{display:inline-flex;align-items:center;gap:6px;margin-top:6px;font-size:12.5px;font-weight:700;text-decoration:none;border:1px solid var(--hair);border-radius:6px;padding:6px 10px}
.rel-group{margin-top:12px} .rel-group h3{font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink2);margin:0 0 5px}
.rchip{display:inline-flex;align-items:center;gap:6px;font-size:12px;border:1px solid var(--hair);background:var(--lane-alt);border-radius:14px;padding:3px 9px;margin:0 4px 4px 0;cursor:pointer;max-width:100%;font-family:var(--sans)}
.rchip .swd{width:7px;height:7px}
.disc{font-size:11px;color:var(--ink2);border-top:1px solid var(--hair);margin-top:16px;padding-top:10px}
dialog{border:1px solid var(--hair);border-radius:8px;background:var(--bg);color:var(--ink);max-width:min(720px,94vw);font-family:var(--sans);font-size:13px}
dialog textarea{width:100%;min-height:220px;font-family:var(--mono);font-size:11px;background:var(--lane);color:var(--ink);border:1px solid var(--hair)}
@media (max-width:900px){.cols{grid-template-columns:1fr} .filters{grid-template-columns:1fr}}
@media (max-width:760px){body{font-size:14px} h1{font-size:19px} .frow .lab{min-width:100%}
  .sheet{width:100%;max-width:100%;top:auto;bottom:0;height:72%;border-left:0;border-top:1px solid var(--hair);border-radius:14px 14px 0 0;transform:translateY(100%)} .sheet.open{transform:none} .xhint{display:none}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
/* print: Figure 1 on A4 landscape, Panel 1 and Table 1 on A4 portrait */
@page{size:A4;margin:14mm} @page fig{size:A4 landscape;margin:10mm}
@media print{
  :root{--bg:#fff;--ink:#111;--ink2:#444;--ink3:#777;--rule:#000;--hair:#bbb;--lane:#fafafa;--lane-alt:#f0f0f0;--accent:#c8102e;--accent-soft:#fbe9ec;
    --st-in_force:#dce8f2;--st-in_force-b:#4f7ea8;--st-draft:#fff0cf;--st-draft-b:#c98f12;--st-pending:#ece4f8;--st-pending-b:#7b5cb8;--st-programme:#e2f2e4;--st-programme-b:#3f8f52;
    --st-guidance:#f0f0f0;--st-guidance-b:#8a8a8a;--st-verify:#fde6e9;--st-verify-b:#c8102e;--st-mixed:#e9eef2;--st-mixed-b:#6b8093;color-scheme:light}
  body{padding:0;font-size:10.5pt} .wrap{max-width:none}
  .tabs,.filters,.viewbar,#view-explore,#view-notes,.sheet,.note,.figbox{display:none!important}
  .kref{text-decoration:none;text-align:left}
  .view{display:block!important}
  h1,.byline,.figprint{page:fig} .figprint{break-after:page} #printfigs{display:block!important}
  .pfig{break-inside:avoid} .pfig+.pfig{break-before:page} .pfig .figtitle{margin:0 0 4px} .pfig svg{width:100%;height:auto;display:block}
  .colmask{display:none} .bar.lo,.k.lo{opacity:.35}
  .legend{font-size:9pt} .keyrow{font-size:8.5pt}
  .panel{break-before:page;border:1px solid #000} .panel li{font-size:9.5pt}
  .tablewrap{overflow:visible} table.reg{min-width:0;font-size:7.5pt;table-layout:fixed} table.reg td,table.reg th{padding:2px 3px} .note2{font-size:6.5pt} .stchip{font-size:7pt;padding:0;border:0!important;background:none!important;text-decoration:none!important} .stchip.st-superseded{text-decoration:line-through!important} .stchip::after{content:' —'} .note2{display:inline}
  table.reg col:nth-child(1){width:10%!important} table.reg col:nth-child(2){width:26%!important} table.reg col:nth-child(3){width:9%!important} table.reg col:nth-child(4){width:10%!important} table.reg col:nth-child(5){width:14%!important} table.reg col:nth-child(6){width:7%!important} table.reg col:nth-child(7){width:18%!important} table.reg col:nth-child(8){width:6%!important} .sort .arr{display:none}
  tr{break-inside:avoid} thead{display:table-header-group} a{text-decoration:none}
  .figtitle{break-after:avoid}
}
</style>
<div class="wrap">
<h1>Regulatory requirements for oligonucleotide therapeutics</h1>
<p class="byline">Development map · ICH, EU, US, Japan, UK · data model %%DM%%, release v%%VER%%, %%GEN%% · %%NDOC%% documents, %%NCON%% oligonucleotide-specific considerations</p>

<div class="tabs" role="tablist" aria-label="Views">
  <button class="tab" role="tab" id="tab-map" aria-controls="view-map" aria-selected="true" data-view="map">Map</button>
  <button class="tab" role="tab" id="tab-explore" aria-controls="view-explore" aria-selected="false" data-view="explore" tabindex="-1">Explore</button>
  <button class="tab" role="tab" id="tab-register" aria-controls="view-register" aria-selected="false" data-view="register" tabindex="-1">Register</button>
  <button class="tab" role="tab" id="tab-notes" aria-controls="view-notes" aria-selected="false" data-view="notes" tabindex="-1">%%NOTESTAB%%</button>
  <span class="tools"><button class="tbtn" id="printBtn" title="Print Figure 1, Panel 1 and Table 1 on A4">Print</button><button class="tbtn" id="themeBtn" aria-label="Toggle light or dark theme">Theme</button></span>
</div>

<div class="filters" id="filters" aria-label="Filters (apply to all views)">
  <div class="frow"><span class="lab">Jurisdiction</span>%%F_REGION%%</div>
  <div class="frow"><span class="lab">Status</span>%%F_STATUS%%</div>
  <div class="frow"><span class="lab">Domain</span>%%F_DOMAIN%%</div>
  <div class="frow"><span class="lab">Verification</span>%%F_VERIF%%</div>
  <div class="frow"><span class="lab">Gates</span><select id="gFrom" aria-label="From gate">%%GATE_OPTS%%</select><span>to</span><select id="gTo" aria-label="To gate">%%GATE_OPTS%%</select></div>
  <div class="frow"><span class="lab">Search</span><input id="q" type="search" placeholder="key, title or reference…" autocomplete="off"></div>
  <div class="frow fwide"><span class="lab">Programme type</span>%%OVBTN%%
    <span class="seg" role="group" aria-label="Non-matching documents"><button id="mDim" aria-pressed="true">Dim</button><button id="mHide" aria-pressed="false">Hide</button></span></div>
  <div class="frow fwide"><span class="lab">Preset</span>
    <select id="preset" aria-label="Filter preset">%%PRESET_OPTS%%</select>
    <button class="tbtn" id="savePreset" title="Store the current filters as this browser’s preset for the selected programme type">Save as preset</button>
    <button class="tbtn" id="clearPresets" title="Forget saved presets and return to the built-in ones">Built-in presets</button>
    <button class="tbtn" id="reset">Reset</button>
    <span class="count" id="count" aria-live="polite"></span></div>
</div>

<section class="view on" id="view-map" role="tabpanel" aria-labelledby="tab-map">
<div class="viewbar"><span>Figure: click a key for details, Tab to move between bars, ←/→ within a series, Enter opens, Esc closes.</span><span style="margin-left:auto"></span><button class="tbtn" id="copySvg">Copy SVG</button></div>
<div class="figprint">
<p class="figtitle"><b>Figure 1:</b> Regulatory documents mapped to development gates and regulatory domains</p>
<div class="figbox">%%SVG%%</div>
<div id="printfigs"></div>
%%LEGEND_STATUS%%
<p class="legend">Each bar is one document or one series of documents with the same applicability, placed in its regulatory domain and spanning the development gates at which it applies. Bar colour and outline pattern encode status; the stripe at the left edge and the tag before each key encode the issuing jurisdiction. The red diamond marks the end-of-phase-2 interaction, where paediatric plan obligations (PIP in the EU, iPSP in the US) cluster. Programme-type buttons highlight the documents additionally engaged by that programme; the paediatric-oncology set reflects RACE Act and Paediatric Regulation obligations for molecularly targeted agents. Hover a key for the full title, reference and status; click it for the detail sheet with the source link. “Dim” keeps non-matching documents visible at low opacity; “Hide” removes them, treats a programme-type selection as a filter, and closes up empty rows and lanes.</p>
<p class="legend abbr">AOC=antibody–oligonucleotide conjugate. ASO=antisense oligonucleotide. CMC=chemistry, manufacturing and controls. CTA=clinical trial application. CTD=common technical document. EoP2=end of phase 2. GL=guideline. iASO=individualised ASO. IMPD=investigational medicinal product dossier. IND=investigational new drug application. iPSP=initial paediatric study plan. LNP=lipid nanoparticle. MA=marketing authorisation. MRCT=multi-regional clinical trial. OSWG=Oligonucleotide Safety Working Group. PIP=paediatric investigation plan. RDEP=Rare Disease Evidence Principles. RPD=rare paediatric disease. TK=toxicokinetics.</p>
</div>
<div class="panel"><h2>Panel 1: Oligonucleotide-specific considerations and where the documents address them</h2><ol>%%PANEL%%</ol></div>
</section>

<section class="view" id="view-explore" role="tabpanel" aria-labelledby="tab-explore">
<div class="viewbar">
  <span>Layers</span>
  <button class="tbtn" id="xCons" aria-pressed="true" title="Considerations and the documents that address them">Considerations</button>
  <button class="tbtn" id="xGates" aria-pressed="false" title="Development gates and derived document→gate links">Gates</button>
  <button class="tbtn" id="xLanes" aria-pressed="false" title="Arrange nodes by gate">Gate lanes</button>
  <span style="margin-left:auto"></span>
  <button class="tbtn" id="copyJson">Copy JSON</button>
</div>
<div class="xwrap" id="xwrap">
  <svg class="graph" id="xsvg" aria-label="Explore: documents and their relations"></svg>
  <div class="xcount" id="xcount"></div>
  <div class="xhint">Drag nodes · scroll to zoom · click for detail</div>
  <div class="xfail" id="xfail">The graph library could not be loaded. The Map and Register views do not need it.</div>
</div>
<p class="legend">Documents are drawn with their <code>references</code>, <code>amends</code> and <code>supersedes</code> relations; node colour is the issuing jurisdiction, squares are binding legal acts, dashed outlines mark drafts or unverified entries. The <i>Considerations</i> layer adds the oligonucleotide-specific topics of Panel 1 with their <code>addresses</code> links; the <i>Gates</i> layer adds the development spine and the derived document→gate links (dashed). Positions are not stable between loads; use the map as the reference figure.</p>
</section>

<section class="view" id="view-register" role="tabpanel" aria-labelledby="tab-register">
<div class="viewbar"><button class="tbtn" id="syncTbl" aria-pressed="true">Register follows filters</button><span style="margin-left:auto"></span><button class="tbtn" id="copyCsv">Copy CSV</button></div>
<p class="figtitle" style="margin-top:4px"><b>Table 1:</b> Document register with reference, status and verification</p>
<div class="tablewrap"><table class="reg" id="tbl"><colgroup><col style="width:13%"><col style="width:29%"><col style="width:9%"><col style="width:10%"><col style="width:15%"><col style="width:7%"><col style="width:11%"><col style="width:6%"></colgroup>
<thead><tr>%%THEAD%%</tr></thead><tbody>%%TABLE%%</tbody></table></div>
<p class="fn">Keys match the bars in Figure 1; the dot before each key gives the jurisdiction. “Checked” records how the entry was verified in October 2026: source opened=official page or PDF read; URL on official site=document located on the issuing body’s domain without opening it; secondary source opened=non-official source read because the primary text could not be reached. Click a column header to sort; click a key for the detail sheet.</p>
</section>

<section class="view" id="view-notes" role="tabpanel" aria-labelledby="tab-notes">
%%NOTES%%
</section>

<p class="note">%%DISCLAIMER%% Data: CC BY 4.0, code: MIT. Layout generated deterministically from the graph data; the same input always yields the same figure.</p>
</div>
<aside class="sheet" id="sheet" aria-live="polite"></aside>
<dialog id="dlg"><p id="dlgMsg">Clipboard access was refused. Select the text and copy it.</p><textarea id="dlgTxt" readonly></textarea><form method="dialog" style="margin-top:8px;text-align:right"><button class="tbtn">Close</button></form></dialog>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<script>
const GRAPH=%%GRAPHJSON%%;
(function(){
"use strict";
const OV=%%OVJSON%%, PRESETS=%%PRJSON%%; const NG=%%NG%%, CH=%%CH%%, CGAP=%%CGAP%%, PAD=%%PAD%%, TOP=%%TOP%%;
const REGIONS=%%REGIONS%%, GATES=GRAPH.meta.gates.map(x=>x.label), DOM_LABEL=%%DOMLABEL%%;
const ST_LABEL=%%STLABEL%%, VL=%%VLABEL%%, KIND_LABEL={milestone:"Development gate",legal_act:"Law / regulation",guideline:"Guideline",pharmacopoeia:"Pharmacopoeia",programme:"Programme / designation",consideration:"Oligonucleotide consideration"};
const REL_LABEL={applies_at:"Applies at gate",prerequisite_for:"Leads to",references:"References",supports:"Supports",amends:"Amends",addresses:"Addresses",informs:"Informs",supersedes:"Supersedes"};
const N=new Map(GRAPH.nodes.map(n=>[n.id,n]));
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const cssv=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const regionColor=r=>cssv('--r-'+(REGIONS.includes(r)?r:'INTL'));
const svg=$('svg.fig'), H0=+svg.getAttribute('height');
const bars=$$('.bar'), keys=$$('.k[data-id]'), lanes=$$('.lanegrp'), rows=$$('#tbl tbody tr'), masks=$$('.colmask'), vlines=$$('.vline');
const S={region:new Set(),status:new Set(),domain:new Set(),verif:new Set(),from:0,to:NG-1,q:'',ov:null,hide:false,sync:true};
$$('.fchip').forEach(b=>S[b.dataset.f].add(b.dataset.v));
const gFrom=$('#gFrom'),gTo=$('#gTo'); gTo.value=NG-1;
const docOf={}; keys.forEach(t=>{const bar=t.closest('.bar');docOf[t.dataset.id]={t,bar,region:t.dataset.region,status:t.dataset.status,verif:t.dataset.verif,dom:bar.dataset.dom,a:+bar.dataset.a,b:+bar.dataset.b,s:t.dataset.s};});
let VIS=new Set(), OVSET=null;
function passesFilters(d){
  if(!S.region.has(d.region)||!S.status.has(d.status)||!S.domain.has(d.dom))return false;
  if(!S.verif.has(d.verif)&&d.verif!=='none')return false;
  if(d.b<S.from||d.a>S.to)return false;
  if(S.q&&!d.s.includes(S.q))return false;
  return true;
}
/* ---------- Map ---------- */
function relayout(shown){
  let y=TOP, h;
  lanes.forEach(l=>{
    const vis=[...l.querySelectorAll('.bar')].filter(b=>shown.has(b));
    const laneOn=S.domain.has(l.dataset.dom)&&vis.length>0;
    l.classList.toggle('off',!laneOn); if(!laneOn)return;
    const rowsF=[]; vis.forEach(b=>{const a=+b.dataset.a,bb=+b.dataset.b; let ri=rowsF.findIndex(r=>r.every(([ra,rb])=>bb<ra||a>rb));
      if(ri<0){rowsF.push([[a,bb]]);ri=rowsF.length-1;}else rowsF[ri].push([a,bb]);
      const ny=y+PAD+ri*(CH+CGAP); b.setAttribute('transform','translate(0,'+(ny-(+b.dataset.y))+')');});
    h=PAD*2+rowsF.length*(CH+CGAP);
    const bg=l.querySelector('.lanebg'); bg.setAttribute('y',y); bg.setAttribute('height',h);
    l.querySelector('.lane-lab').setAttribute('y',y+16); y+=h;
  });
  const Hn=y+8; svg.setAttribute('height',Hn); svg.setAttribute('viewBox','0 0 '+svg.viewBox.baseVal.width+' '+Hn);
  vlines.forEach(v=>v.setAttribute('y2',Hn-6)); masks.forEach(m=>m.setAttribute('height',Hn-TOP));
}
function restoreLayout(){
  lanes.forEach(l=>{l.classList.remove('off'); const bg=l.querySelector('.lanebg'); bg.setAttribute('y',l.dataset.y0); bg.setAttribute('height',l.dataset.h);
    l.querySelector('.lane-lab').setAttribute('y',+l.dataset.y0+16); l.querySelectorAll('.bar').forEach(b=>b.removeAttribute('transform'));});
  svg.setAttribute('height',H0); svg.setAttribute('viewBox','0 0 '+svg.viewBox.baseVal.width+' '+H0);
  vlines.forEach(v=>v.setAttribute('y2',H0-6)); masks.forEach(m=>m.setAttribute('height',H0-TOP));
}
function applyMap(vis,ov){
  const shownBars=new Set();
  bars.forEach(b=>{const ids=b.dataset.ids.split(' ');const any=ids.some(i=>vis.has(i));
    b.classList.toggle('off',S.hide&&!any); b.classList.toggle('lo',!any); b.setAttribute('tabindex',(S.hide&&!any)?'-1':'0');
    if(!(S.hide&&!any))shownBars.add(b);
    const hi=!!ov&&ids.some(i=>vis.has(i)&&ov.has(i)); b.classList.toggle('hi',hi);
    if(ov&&any&&!hi)b.classList.add('lo');
    let seen=false; ids.forEach(id=>{const v=!S.hide||vis.has(id);const s=b.querySelector('.sep[data-sep-for="'+id+'"]');
      if(s)s.classList.toggle('off',!(v&&seen)); if(v)seen=true;});
    const regs=[...new Set(ids.filter(i=>!S.hide||vis.has(i)).map(i=>docOf[i].region))];
    const st=[...b.querySelectorAll('.stripe')]; const y0=+st[0].dataset.y0,h=+st[0].dataset.h; let k=0;
    st.forEach(r=>{const on=regs.includes(r.dataset.region); r.style.display=on?'':'none';
      if(on){r.setAttribute('y',y0+k*(h/Math.max(1,regs.length)));r.setAttribute('height',h/Math.max(1,regs.length));k++;}});});
  keys.forEach(t=>{const id=t.dataset.id,v=vis.has(id);
    t.classList.toggle('off',S.hide&&!v); t.classList.toggle('lo',!S.hide&&!v);
    t.classList.toggle('hi',!!ov&&ov.has(id)&&v); if(ov&&v&&!ov.has(id))t.classList.add('lo');});
  masks.forEach(m=>{const c=+m.dataset.col;m.classList.toggle('out',c<S.from||c>S.to);});
  if(S.hide)relayout(shownBars); else restoreLayout();
}
/* keyboard on bars: Tab between bars, arrows between keys in a bar, Enter opens the sheet */
bars.forEach(b=>{let ki=0; const ks=[...b.querySelectorAll('.k')];
  const mark=()=>ks.forEach((k,i)=>k.classList.toggle('kf',i===ki&&ks.length>1&&document.activeElement===b));
  b.addEventListener('focus',()=>{ki=0;mark();}); b.addEventListener('blur',()=>ks.forEach(k=>k.classList.remove('kf')));
  b.addEventListener('keydown',e=>{
    const live=ks.filter(k=>!k.classList.contains('off'));
    if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault(); if(!live.length)return; let j=live.indexOf(ks[ki]); j=(j+(e.key==='ArrowRight'?1:-1)+live.length)%live.length; ki=ks.indexOf(live[j]); mark();}
    else if(e.key==='Enter'||e.key===' '){e.preventDefault(); const k=ks[ki]&&!ks[ki].classList.contains('off')?ks[ki]:live[0]; if(k)openSheet(k.dataset.id);}
  });});
keys.forEach(t=>t.addEventListener('click',e=>{if(e.metaKey||e.ctrlKey)return; e.preventDefault(); openSheet(t.dataset.id);}));
/* ---------- Register ---------- */
const tbody=$('#tbl tbody'); let sortCol=0, sortDir=1;
function sortRows(){
  const rs=[...tbody.querySelectorAll('tr')]; rs.forEach(r=>r._s=r._s||JSON.parse(r.dataset.sort));
  rs.sort((a,b)=>{const x=a._s[sortCol],y=b._s[sortCol]; return (x<y?-1:x>y?1:a._s[0]-b._s[0])*sortDir;});
  rs.forEach(r=>tbody.appendChild(r));
  $$('.sort').forEach(h=>h.setAttribute('aria-sort',+h.dataset.col===sortCol?(sortDir>0?'ascending':'descending'):'none'));
}
$$('.sort').forEach(h=>h.onclick=()=>{const c=+h.dataset.col; if(sortCol===c)sortDir=-sortDir; else{sortCol=c;sortDir=1;} sortRows();});
function applyRegister(vis){ rows.forEach(r=>r.classList.toggle('off',S.sync&&!vis.has(r.dataset.id))); }
$$('.kref').forEach(k=>k.onclick=()=>openSheet(k.dataset.go));
function csvOf(ids){
  const cols=["id","key","label","kind","domain","gate_from","gate_to","group","region","ref","date","status","status_note","confidence","verification","last_checked","url","scope","oligo_note","modality","triggers"];
  const q=v=>{v=v==null?'':Array.isArray(v)?v.join(';'):String(v); return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;};
  return [cols.join(',')].concat(ids.map(id=>cols.map(c=>q(N.get(id)[c])).join(','))).join('\n');
}
/* ---------- Explore (d3) ---------- */
let X=null;
function initExplore(){
  if(!window.d3){$('#xfail').style.display='flex';return;}
  const xs=d3.select('#xsvg'), cw=$('#xwrap'); const root=xs.append('g'); const laneG=root.append('g'), linkG=root.append('g'), nodeG=root.append('g');
  let W=cw.clientWidth,H=cw.clientHeight;
  const zoom=d3.zoom().scaleExtent([0.3,3]).on('zoom',e=>root.attr('transform',e.transform)); xs.call(zoom);
  const nodes=GRAPH.nodes.map(n=>Object.assign({},n)); const nm=new Map(nodes.map(n=>[n.id,n]));
  const links=GRAPH.edges.map(e=>Object.assign({},e,{derived:false})).concat((GRAPH.derived&&GRAPH.derived.applies_at||[]).map(e=>Object.assign({},e,{derived:true})));
  const radius=n=>n.kind==='milestone'?11:(n.kind==='consideration'?6:7.5);
  const sim=d3.forceSimulation(nodes)
    .force('link',d3.forceLink(links).id(d=>d.id).distance(l=>l.rel==='prerequisite_for'?70:90).strength(l=>l.derived?.1:.35))
    .force('charge',d3.forceManyBody().strength(-220)).force('collide',d3.forceCollide().radius(n=>radius(n)+13))
    .force('center',d3.forceCenter(W/2,H/2)).force('x',d3.forceX(W/2).strength(.04)).force('y',d3.forceY(H/2).strength(.06));
  const link=linkG.selectAll('line').data(links).join('line').attr('class',l=>'link'+(l.derived?' derived':''));
  const node=nodeG.selectAll('g').data(nodes).join('g').attr('class','node').attr('tabindex',0).attr('role','button')
    .attr('aria-label',d=>d.key||d.label)
    .call(d3.drag().on('start',(e,d)=>{if(!e.active)sim.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y;})
      .on('drag',(e,d)=>{d.fx=e.x;d.fy=e.y;}).on('end',(e,d)=>{if(!e.active)sim.alphaTarget(0);if(!X.lanes){d.fx=null;d.fy=null;}}))
    .on('click',(e,d)=>{e.stopPropagation();openSheet(d.id);})
    .on('keydown',(e,d)=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openSheet(d.id);}});
  node.each(function(d){const s=d3.select(this); const r=radius(d);
    if(d.kind==='milestone'||d.kind==='legal_act')s.append('rect').attr('class','shape').attr('x',-r).attr('y',-r).attr('width',2*r).attr('height',2*r).attr('rx',d.kind==='milestone'?3:8);
    else if(d.kind==='consideration')s.append('path').attr('class','shape').attr('d',`M0 ${-r-1} L${r+1} 0 L0 ${r+1} L${-r-1} 0 Z`);
    else s.append('circle').attr('class','shape').attr('r',r);
    if(d.status==='draft'||d.status==='verify'||d.confidence==='low')s.select('.shape').attr('stroke-dasharray','2 2');});
  node.append('text').attr('x',d=>radius(d)+4).attr('y',4).text(d=>d.kind==='milestone'||d.kind==='consideration'?(d.short||d.label):d.key);
  const paint=()=>{node.select('.shape').attr('fill',d=>d.kind==='consideration'?cssv('--accent'):d.kind==='milestone'?cssv('--ink2'):regionColor(d.region)).attr('stroke',d=>(d.status==='draft'||d.status==='verify'||d.confidence==='low')?cssv('--ink'):cssv('--bg'));
    node.selectAll('text').attr('stroke',cssv('--lane'));};
  paint();
  xs.on('click',()=>closeSheet());
  sim.on('tick',()=>{link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y); node.attr('transform',d=>`translate(${d.x},${d.y})`);});
  const adj=new Map(nodes.map(n=>[n.id,new Set()])); links.forEach(l=>{const s=l.source.id||l.source,t=l.target.id||l.target; adj.get(s).add(t); adj.get(t).add(s);});
  function highlight(id){ if(!id){node.classed('dim',false);link.classed('dim hl',false);return;} const nb=adj.get(id);
    node.classed('dim',n=>n.id!==id&&!nb.has(n.id)); link.classed('hl',l=>l.source.id===id||l.target.id===id).classed('dim',l=>!(l.source.id===id||l.target.id===id)); }
  node.on('mouseenter',(e,d)=>highlight(d.id)).on('mouseleave',()=>{if(!X.sel)highlight(null);});
  const laneX=n=>(((n.gate_from||0)+(n.gate_to||0))/2+0.5)*(W/GATES.length);
  function drawLanes(on){laneG.selectAll('*').remove(); if(!on)return; GATES.forEach((lab,i)=>{const x=(i+0.5)*(W/GATES.length);
    if(i>0)laneG.append('line').attr('class','lane-rule').attr('x1',i*(W/GATES.length)).attr('x2',i*(W/GATES.length)).attr('y1',26).attr('y2',H);
    laneG.append('text').attr('class','lane-label').attr('x',x).attr('y',16).attr('text-anchor','middle').text(W<620?lab.split(/[ /]/)[0].slice(0,5):lab);});}
  function setLanes(on){X.lanes=on; $('#xLanes').setAttribute('aria-pressed',on); drawLanes(on);
    if(on){sim.force('x',d3.forceX(d=>laneX(d)).strength(.9)); sim.force('y',d3.forceY(H/2).strength(.05)); sim.force('center',null); nodes.forEach(n=>{n.fx=null;n.fy=null;});}
    else{sim.force('x',d3.forceX(W/2).strength(.04)); sim.force('y',d3.forceY(H/2).strength(.06)); sim.force('center',d3.forceCenter(W/2,H/2));}
    sim.alpha(.7).restart();}
  function nodeShown(n,vis){
    if(n.kind==='milestone')return X.gates;
    if(n.kind==='consideration')return X.cons;
    return S.hide?vis.has(n.id):S.domain.has(n.domain)&&S.region.has(n.region);
  }
  function apply(vis,ov){
    const shown=new Set(nodes.filter(n=>nodeShown(n,vis)).map(n=>n.id));
    node.style('display',n=>shown.has(n.id)?null:'none')
      .classed('lo',n=>n.kind!=='milestone'&&n.kind!=='consideration'&&!S.hide&&(!vis.has(n.id)||(ov&&!ov.has(n.id))))
      .classed('hi',n=>!!ov&&ov.has(n.id)&&vis.has(n.id));
    const linkOn=l=>{const s=l.source.id,t=l.target.id; if(!shown.has(s)||!shown.has(t))return false;
      if(l.derived)return X.gates; if(l.rel==='addresses'||l.rel==='informs')return X.cons&&(l.rel==='addresses'||X.gates);
      if(l.rel==='supports'||l.rel==='prerequisite_for')return X.gates; return true;};
    link.style('display',l=>linkOn(l)?null:'none');
    const drawn=links.filter(linkOn).length;
    $('#xcount').textContent=`${shown.size} nodes · ${drawn} links`;
    node.classed('sel',n=>n.id===X.sel);
  }
  function resize(){W=cw.clientWidth;H=cw.clientHeight; if(X.lanes){sim.force('x',d3.forceX(d=>laneX(d)).strength(.9));drawLanes(true);} else sim.force('center',d3.forceCenter(W/2,H/2)); sim.alpha(.3).restart();}
  addEventListener('resize',resize);
  X={apply,paint,setLanes,highlight,resize,cons:true,gates:false,lanes:false,sel:null,restart:()=>sim.alpha(.4).restart()};
  $('#xCons').onclick=e=>{X.cons=e.currentTarget.getAttribute('aria-pressed')!=='true';e.currentTarget.setAttribute('aria-pressed',X.cons);applyAll();X.restart();};
  $('#xGates').onclick=e=>{X.gates=e.currentTarget.getAttribute('aria-pressed')!=='true';e.currentTarget.setAttribute('aria-pressed',X.gates);applyAll();X.restart();};
  $('#xLanes').onclick=e=>setLanes(e.currentTarget.getAttribute('aria-pressed')!=='true');
  setTimeout(()=>xs.call(zoom.transform,d3.zoomIdentity),50);
}
/* ---------- Detail sheet (all views) ---------- */
const sheet=$('#sheet'); let SEL=null;
const badge=(t,c)=>`<span class="badge" style="border-color:${c};color:${c}">${t}</span>`;
function openSheet(id){
  const n=N.get(id); if(!n)return; SEL=id; if(X){X.sel=id;X.highlight(id);X.apply(VIS,OVSET);}
  rows.forEach(r=>r.classList.toggle('sel',r.dataset.id===id));
  const rc=regionColor(n.region);
  const groups={}; GRAPH.edges.concat(GRAPH.derived&&GRAPH.derived.applies_at||[]).forEach(e=>{let o=null;
    if(e.source===id)o=e.target; else if(e.target===id)o=e.source; if(!o)return; (groups[e.rel]=groups[e.rel]||[]).push(o);});
  let rels=''; Object.keys(groups).sort().forEach(rel=>{const chips=groups[rel].map(o=>{const m=N.get(o);if(!m)return'';
    const col=m.kind==='consideration'?cssv('--accent'):m.kind==='milestone'?cssv('--ink2'):regionColor(m.region);
    return `<button class="rchip" data-go="${m.id}"><span class="swd" style="background:${col}"></span><b>${esc(m.key||m.short||m.label)}</b></button>`;}).join('');
    rels+=`<div class="rel-group"><h3>${REL_LABEL[rel]||rel}</h3>${chips}</div>`;});
  const isDoc=n.kind!=='milestone'&&n.kind!=='consideration';
  const stc=n.status?cssv('--st-'+(ST_LABEL[n.status]?n.status:'guidance')+'-b'):cssv('--ink2');
  sheet.innerHTML=`<button class="x" id="closeSheet" aria-label="Close">×</button>
    <div class="d-kind">${KIND_LABEL[n.kind]||n.kind}</div><h2>${esc(n.label)}</h2>
    <div class="meta">${isDoc?badge(n.region,rc):''} ${badge(DOM_LABEL[n.domain]||n.domain,cssv('--ink2'))} ${isDoc&&n.status?badge(ST_LABEL[n.status]||n.status,stc):''} ${isDoc?badge('confidence: '+n.confidence,n.confidence==='high'?cssv('--st-programme-b'):n.confidence==='medium'?cssv('--st-draft-b'):cssv('--accent')):''}</div>
    <div class="kv"><b>Key:</b> <span style="font-family:var(--mono)">${esc(n.key)}</span> · <b>Gates:</b> ${GATES[n.gate_from]}${n.gate_to!==n.gate_from?' → '+GATES[n.gate_to]:''}</div>
    ${n.triggers&&n.triggers.length?`<div class="kv"><b>Engaged by:</b> ${n.triggers.map(t=>GRAPH.meta.triggers[t]||t).join(', ')}</div>`:''}
    ${n.ref?`<div class="kv"><b>Reference:</b> <span style="font-family:var(--mono)">${esc(n.ref)}</span></div>`:''}
    ${n.date?`<div class="kv"><b>Date:</b> ${esc(n.date)}</div>`:''}
    ${n.status_note?`<div class="kv"><b>Status:</b> ${esc(n.status_note)}</div>`:''}
    ${n.verification?`<div class="kv"><b>Checked:</b> ${VL[n.verification]||n.verification}${n.last_checked?' · '+esc(n.last_checked):''}</div>`:''}
    ${n.scope?`<div class="scope">${esc(n.scope)}</div>`:''}
    ${n.oligo_note?`<div class="oligo"><span>Oligonucleotide note</span>${esc(n.oligo_note)}</div>`:''}
    ${n.url?`<a class="src" href="${esc(n.url)}" target="_blank" rel="noopener">Open source ↗</a>`:(isDoc?`<div class="kv" style="margin-top:6px">No verified URL — confirm with the issuing body.</div>`:'')}
    ${rels}<div class="disc">${esc(GRAPH.meta.disclaimer)}</div>`;
  sheet.classList.add('open'); sheet.scrollTop=0;
  $('#closeSheet').onclick=closeSheet; sheet.querySelectorAll('[data-go]').forEach(c=>c.onclick=()=>openSheet(c.dataset.go));
  $('#closeSheet').focus();
}
function closeSheet(){sheet.classList.remove('open'); SEL=null; rows.forEach(r=>r.classList.remove('sel')); if(X){X.sel=null;X.highlight(null);X.apply(VIS,OVSET);}}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&sheet.classList.contains('open'))closeSheet();});
/* ---------- shared apply ---------- */
function applyAll(){
  OVSET=S.ov?new Set(OV[S.ov]):null;
  VIS=new Set(); Object.keys(docOf).forEach(id=>{const d=docOf[id]; if(passesFilters(d)&&!(S.hide&&OVSET&&!OVSET.has(id)))VIS.add(id);});
  applyMap(VIS,OVSET); applyRegister(VIS); if(X)X.apply(VIS,OVSET);
  const total=Object.keys(docOf).length;
  $('#count').textContent=VIS.size+' of '+total+' documents'+(S.ov&&!S.hide?' · '+[...VIS].filter(i=>OVSET.has(i)).length+' highlighted':'');
}
/* ---------- filter controls ---------- */
function setChips(name,vals){S[name]=new Set(vals); $$('.fchip[data-f="'+name+'"]').forEach(b=>b.setAttribute('aria-pressed',S[name].has(b.dataset.v)));}
function setOv(v){S.ov=v||null; $$('.ov[data-ov]').forEach(x=>x.setAttribute('aria-pressed',x.dataset.ov===S.ov));}
function setHide(h){S.hide=!!h; $('#mDim').setAttribute('aria-pressed',!S.hide); $('#mHide').setAttribute('aria-pressed',S.hide);}
function setGates(a,b){S.from=a;S.to=b;gFrom.value=a;gTo.value=b;}
const presetSel=$('#preset'); let saved={}; try{saved=JSON.parse(localStorage.getItem('oligo-reqgraph.presets')||'{}')||{};}catch(e){saved={};}
function stateOf(){return {region:[...S.region],status:[...S.status],domain:[...S.domain],verif:[...S.verif],from:S.from,to:S.to,ov:S.ov,hide:S.hide};}
function loadState(p){
  const all=n=>$$('.fchip[data-f="'+n+'"]').map(b=>b.dataset.v);
  setChips('region',p.region||all('region')); setChips('status',p.status||all('status')); setChips('domain',p.domain||all('domain')); setChips('verif',p.verif||all('verif'));
  setGates(p.from??0,p.to??NG-1); setOv(p.ov||null); setHide(!!p.hide); S.q=''; $('#q').value='';
}
function markCustom(){if(presetSel.value)presetSel.value='';}
presetSel.onchange=()=>{const k=presetSel.value; if(!k)return; loadState(saved[k]||PRESETS[k]); applyAll();};
$('#savePreset').onclick=e=>{const k=presetSel.value; const b=e.currentTarget,o=b.textContent;
  if(!k){b.textContent='Choose a programme type first';setTimeout(()=>b.textContent=o,1600);return;}
  saved[k]=stateOf(); try{localStorage.setItem('oligo-reqgraph.presets',JSON.stringify(saved));b.textContent='Saved in this browser';}catch(err){b.textContent='Could not save (storage blocked)';}
  setTimeout(()=>b.textContent=o,1600);};
$('#clearPresets').onclick=e=>{saved={}; try{localStorage.removeItem('oligo-reqgraph.presets');}catch(err){} const b=e.currentTarget,o=b.textContent; b.textContent='Built-in presets restored'; if(presetSel.value){loadState(PRESETS[presetSel.value]);applyAll();} setTimeout(()=>b.textContent=o,1600);};
$$('.fchip').forEach(b=>b.onclick=()=>{const on=b.getAttribute('aria-pressed')!=='true'; b.setAttribute('aria-pressed',on); on?S[b.dataset.f].add(b.dataset.v):S[b.dataset.f].delete(b.dataset.v); markCustom(); applyAll();});
$$('.ov[data-ov]').forEach(b=>b.onclick=()=>{setOv(b.getAttribute('aria-pressed')==='true'?null:b.dataset.ov); markCustom(); applyAll();});
gFrom.onchange=()=>{S.from=+gFrom.value;if(S.to<S.from){S.to=S.from;gTo.value=S.to;} markCustom(); applyAll();};
gTo.onchange=()=>{S.to=+gTo.value;if(S.from>S.to){S.from=S.to;gFrom.value=S.from;} markCustom(); applyAll();};
$('#q').oninput=e=>{S.q=e.target.value.trim().toLowerCase();applyAll();};
$('#mDim').onclick=()=>{setHide(false);markCustom();applyAll();}; $('#mHide').onclick=()=>{setHide(true);markCustom();applyAll();};
const syncB=$('#syncTbl'); syncB.onclick=()=>{S.sync=!S.sync;syncB.setAttribute('aria-pressed',S.sync);syncB.textContent=S.sync?'Register follows filters':'Register shows all';applyAll();};
$('#reset').onclick=()=>{loadState({}); presetSel.value=''; applyAll();};
/* ---------- export ---------- */
async function toClipboard(btn,text,okMsg){const o=btn.textContent;
  try{await navigator.clipboard.writeText(text);btn.textContent=okMsg;}
  catch(e){const d=$('#dlg'); $('#dlgTxt').value=text; d.showModal(); $('#dlgTxt').select(); btn.textContent='Shown for manual copy';}
  setTimeout(()=>btn.textContent=o,1600);}
function themedSvg(){
  const vars=['--bg','--ink','--ink2','--ink3','--rule','--hair','--lane','--lane-alt','--accent','--focus','--st-in_force','--st-in_force-b','--st-draft','--st-draft-b','--st-pending','--st-pending-b','--st-programme','--st-programme-b','--st-guidance','--st-guidance-b','--st-verify','--st-verify-b','--st-mixed','--st-mixed-b','--r-ICH','--r-EU','--r-US','--r-JP','--r-UK','--r-INTL'];
  let css=%%SVGCSS%%; vars.forEach(v=>{css=css.split('var('+v+')').join(cssv(v));});
  const c=svg.cloneNode(true); c.querySelectorAll('.off').forEach(e=>e.remove()); c.querySelectorAll('[style*="display: none"],[style*="display:none"]').forEach(e=>e.remove());
  c.querySelectorAll('.colmask').forEach(e=>e.remove()); c.querySelectorAll('[tabindex]').forEach(e=>e.removeAttribute('tabindex'));
  c.setAttribute('xmlns','http://www.w3.org/2000/svg'); c.setAttribute('xmlns:xlink','http://www.w3.org/1999/xlink');
  const w=c.viewBox.baseVal.width,h=c.viewBox.baseVal.height;
  c.insertAdjacentHTML('afterbegin',`<style>${css}</style><rect width="${w}" height="${h}" fill="${cssv('--bg')}"/>`);
  return c.outerHTML;
}
$('#copySvg').onclick=e=>toClipboard(e.currentTarget,themedSvg(),'SVG copied');
$('#copyCsv').onclick=e=>{const ids=[...tbody.querySelectorAll('tr')].filter(r=>!r.classList.contains('off')).map(r=>r.dataset.id); toClipboard(e.currentTarget,csvOf(ids),ids.length+' rows copied');};
$('#copyJson').onclick=e=>toClipboard(e.currentTarget,JSON.stringify(GRAPH,null,2),'JSON copied');
/* print: Figure 1 split at lane boundaries so that each part fits one A4 landscape page */
function printSplit(){
  const box=$('#printfigs'); box.innerHTML=''; const LIMIT=700, FIRST=620; /* px of figure height per landscape page at ~0.93 scale; first page shares with the title */
  const Ls=lanes.filter(l=>!l.classList.contains('off')).map(l=>{const bg=l.querySelector('.lanebg');return {dom:l.dataset.dom,y:+bg.getAttribute('y'),h:+bg.getAttribute('height')};});
  const pages=[]; let cur=[],acc=TOP;
  Ls.forEach(L=>{if(cur.length&&acc+L.h>(pages.length?LIMIT:FIRST)){pages.push(cur);cur=[];acc=TOP;} cur.push(L);acc+=L.h;}); if(cur.length)pages.push(cur);
  pages.forEach((pg,i)=>{const c=svg.cloneNode(true); const keep=new Set(pg.map(L=>L.dom)); let y=TOP;
    c.querySelectorAll('.lanegrp').forEach(l=>{if(!keep.has(l.dataset.dom)){l.remove();return;} const bg=l.querySelector('.lanebg'); const dy=y-(+bg.getAttribute('y')); l.setAttribute('transform','translate(0,'+dy+')'); y+=+bg.getAttribute('height');});
    const Hn=y+8; c.setAttribute('height',Hn); c.setAttribute('viewBox','0 0 '+c.viewBox.baseVal.width+' '+Hn);
    c.querySelectorAll('.vline').forEach(v=>v.setAttribute('y2',Hn-6)); c.querySelectorAll('.colmask,.off').forEach(e=>e.remove()); c.querySelectorAll('[tabindex]').forEach(e=>e.removeAttribute('tabindex'));
    const w=document.createElement('div'); w.className='pfig'; if(i>0)w.insertAdjacentHTML('afterbegin','<p class="figtitle"><b>Figure 1 (continued, part '+(i+1)+' of '+pages.length+'):</b> lanes '+pg.map(L=>DOM_LABEL[L.dom]).join(', ')+'</p>');
    w.appendChild(c); box.appendChild(w);});
}
addEventListener('beforeprint',printSplit); addEventListener('afterprint',()=>{$('#printfigs').innerHTML='';});
$('#printBtn').onclick=()=>{printSplit();window.print();};
window.__printSplit=printSplit;
$('#themeBtn').onclick=()=>{const r=document.documentElement; const cur=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
  r.setAttribute('data-theme',cur==='dark'?'light':'dark'); if(X)X.paint(); if(SEL)openSheet(SEL);};
/* ---------- views + hash routing ---------- */
const VIEWS=['map','explore','register','notes']; const ALIAS={open:'notes',tbl:'register'};/* #open: internal build only */
function showView(v,push){
  if(!VIEWS.includes(v))v='map';
  $$('.tab').forEach(t=>{const on=t.dataset.view===v; t.setAttribute('aria-selected',on); t.setAttribute('tabindex',on?'0':'-1');});
  $$('.view').forEach(s=>s.classList.toggle('on',s.id==='view-'+v));
  if(v==='explore'){ if(X===null)initExplore(); if(X){X.resize();X.apply(VIS,OVSET);} }
  if(push&&location.hash!=='#'+v)history.replaceState(null,'','#'+v);
}
function route(){let h=(location.hash||'#map').slice(1); const target=ALIAS[h]?document.getElementById(h):null; if(ALIAS[h])h=ALIAS[h];
  showView(h,false); if(target)setTimeout(()=>target.scrollIntoView({block:'start'}),30);}
$$('.tab').forEach(t=>{t.onclick=()=>{location.hash='#'+t.dataset.view;};
  t.onkeydown=e=>{if(e.key!=='ArrowRight'&&e.key!=='ArrowLeft')return; const ts=$$('.tab'); let i=ts.indexOf(t)+(e.key==='ArrowRight'?1:-1); i=(i+ts.length)%ts.length; ts[i].focus(); ts[i].click();};});
addEventListener('hashchange',route);
sortRows(); applyAll(); route();

})();
</script>
'''
SVGCSS='''.spine{stroke:var(--rule);stroke-width:1.2;fill:none}.grid{stroke:var(--hair);stroke-width:.6}
.gate{font-size:11px;font-weight:700;fill:var(--ink)}.gate-sub{font-size:9px;fill:var(--ink2)}.eop2{fill:var(--accent)}
.lane{fill:var(--lane)}.lane.alt{fill:var(--lane-alt)}.lane-lab{font-size:10.5px;font-weight:700;fill:var(--ink);letter-spacing:.02em}
.chip{stroke-width:.9}.chip.st-in_force{fill:var(--st-in_force);stroke:var(--st-in_force-b)}.chip.st-draft{fill:var(--st-draft);stroke:var(--st-draft-b);stroke-dasharray:3 2}
.chip.st-pending{fill:var(--st-pending);stroke:var(--st-pending-b);stroke-dasharray:7 2.5}.chip.st-programme{fill:var(--st-programme);stroke:var(--st-programme-b)}
.chip.st-guidance{fill:var(--st-guidance);stroke:var(--st-guidance-b);stroke-dasharray:1 2}.chip.st-verify{fill:url(#hatch);stroke:var(--st-verify-b);stroke-dasharray:3 2}
.chip.st-mixed{fill:var(--st-mixed);stroke:var(--st-mixed-b);stroke-dasharray:7 2 1.5 2}.chip.st-superseded{fill:var(--st-guidance);stroke:var(--st-guidance-b)}.chip.law{stroke-width:1.6}
.hatch-bg{fill:var(--st-verify)}.hatch-ln{stroke:var(--st-verify-b);stroke-width:.7;opacity:.55}
.r-ICH{fill:var(--r-ICH)}.r-EU{fill:var(--r-EU)}.r-US{fill:var(--r-US)}.r-JP{fill:var(--r-JP)}.r-UK{fill:var(--r-UK)}.r-INTL{fill:var(--r-INTL)}
.key{font-size:9.5px;fill:var(--ink)}.reg{font-size:8px;font-weight:700;letter-spacing:.04em}.sep{fill:var(--ink3)}text{font-family:Helvetica,Arial,sans-serif}.k[data-status="verify"]{fill:var(--st-verify-b)}
.lo{opacity:.22}.hi .chip{stroke:var(--accent);stroke-width:2}.st-superseded .k{text-decoration:line-through}'''
REPL={"%%DM%%":g["meta"].get("data_model","0.3"),"%%VER%%":g["meta"]["version"],"%%GEN%%":g["meta"]["generated"],"%%NDOC%%":str(len(docs)),"%%NCON%%":str(len(cons)),
 "%%F_REGION%%":F_REGION,"%%F_STATUS%%":F_STATUS,"%%F_DOMAIN%%":F_DOMAIN,"%%F_VERIF%%":F_VERIF,"%%GATE_OPTS%%":GATE_OPTS,"%%OVBTN%%":OVBTN,"%%PRESET_OPTS%%":PRESET_OPTS,
 "%%SVG%%":SVG,"%%LEGEND_STATUS%%":LEGEND_STATUS,"%%PANEL%%":PANEL,"%%THEAD%%":THEAD,"%%TABLE%%":TABLE,"%%NOTES%%":(SCOPE+HOWTO+CHANGES+A11Y+AUDIT+ROADMAP+OPEN) if INTERNAL else (SCOPE+HOWTO),"%%NOTESTAB%%":"Notes" if INTERNAL else "About",
 "%%DISCLAIMER%%":esc(g["meta"]["disclaimer"]),"%%GRAPHJSON%%":GRAPHJSON,"%%OVJSON%%":OVJSON,"%%PRJSON%%":PRJSON,"%%NG%%":str(len(GATES)),"%%CH%%":str(CH),"%%CGAP%%":str(CGAP),"%%PAD%%":str(LANEPAD),"%%TOP%%":str(TOP),
 "%%REGIONS%%":json.dumps(REGIONS),"%%DOMLABEL%%":json.dumps({d:l.replace("|"," ") for d,l in DOMAINS}|{"spine":"Development spine","consideration":"Consideration"}),
 "%%STLABEL%%":json.dumps(dict(STATUSES)),"%%VLABEL%%":json.dumps(dict(VERIF)),"%%SVGCSS%%":json.dumps(SVGCSS)}
out=page
for k,v in REPL.items(): out=out.replace(k,v)
assert "%%" not in out, re.findall(r"%%\w+%%",out)
open(os.path.join(PKG,"index.html" if not INTERNAL else "index-internal.html"),"w").write(out)

# standalone SVG (light theme, links kept) for manuscript use
LIGHT={"--bg":"#ffffff","--ink":"#111111","--ink2":"#555555","--ink3":"#8a8a8a","--rule":"#1a1a1a","--hair":"#d9d9d9","--lane":"#fafafa","--lane-alt":"#f3f3f3","--accent":"#c8102e",
 "--st-in_force":"#dce8f2","--st-in_force-b":"#4f7ea8","--st-draft":"#fff0cf","--st-draft-b":"#c98f12","--st-pending":"#ece4f8","--st-pending-b":"#7b5cb8","--st-programme":"#e2f2e4","--st-programme-b":"#3f8f52",
 "--st-guidance":"#f0f0f0","--st-guidance-b":"#8a8a8a","--st-verify":"#fde6e9","--st-verify-b":"#c8102e","--st-mixed":"#e9eef2","--st-mixed-b":"#6b8093",
 "--r-ICH":"#3f6fb0","--r-EU":"#1f9d8f","--r-US":"#c6603a","--r-JP":"#9a5bb8","--r-UK":"#4e8d4a","--r-INTL":"#7d8287"}
css=SVGCSS
for k,v in LIGHT.items(): css=css.replace(f"var({k})",v)
s=SVG.replace('<svg class="fig"','<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" class="fig"',1)
s=re.sub(r' tabindex="[-0-9]+"','',s); s=re.sub(r'<rect class="colmask"[^>]*/>\n?','',s)
s=s.replace('<defs>',f'<style>{css}</style><rect width="{W}" height="{H}" fill="#ffffff"/><defs>',1)
open(os.path.join(PKG,"figure1.svg"),"w").write(s)
print("index-internal.html" if INTERNAL else "index.html",len(out)//1024,"KB · figure1.svg · rows",rows_per_lane,"canvas",W,"x",H)
