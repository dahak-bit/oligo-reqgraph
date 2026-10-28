#!/usr/bin/env python3
"""Journal-figure-style regulatory map for oligonucleotide therapeutics.
v2: status encoded in colour, jurisdiction as a coloured stripe + tag, full filter set,
audit findings and roadmap sections. Deterministic layout from graph.json."""
import json, os, html
HERE=os.path.dirname(__file__); PKG=os.path.join(HERE,"pkg")
g=json.load(open(os.path.join(PKG,"graph.json"))); NB={n["id"]:n for n in g["nodes"]}

GATES=[("discovery","Discovery"),("nonclinical","Nonclinical"),("cta","CTA / IND"),("p1","Phase 1"),
       ("p2","Phase 2"),("p3","Phase 3"),("filing","Filing & approval"),("post","Post-approval")]
DOMAINS=[("quality","Quality & CMC"),("nonclin","Nonclinical safety"),("clinical","Clinical &|pharmacology"),
         ("paed","Paediatric"),("rare","Rare, expedited &|individualised"),("auth","Trial & marketing|authorisation")]
REGIONS=["ICH","EU","US","JP","UK","INTL"]
# ---- placement comes from the data (v0.3): domain, gate_from, gate_to, key, group, triggers ----
docs=[n for n in g["nodes"] if n["kind"] not in ("milestone","consideration")]
P={n["id"]:(n["domain"],n["gate_from"],n["gate_to"],n["key"]) for n in docs}
GROUPS=[(grp["domain"],min(NB[m]["gate_from"] for m in grp["members"]),max(NB[m]["gate_to"] for m in grp["members"]),grp["members"]) for grp in g["meta"]["groups"]]
grouped=set(m for *_,ms in GROUPS for m in ms)
TRIG_LABEL=g["meta"]["triggers"]
OVERLAYS={t:(lab,[n["id"] for n in docs if t in n["triggers"]]) for t,lab in TRIG_LABEL.items()}
STATUSES=[("in_force","In force"),("draft","Draft"),("pending","Pending adoption"),("programme","Programme / designation"),
          ("guidance","Non-binding consensus"),("superseded","Superseded"),("verify","Unverified")]
VERIF=[("page","Source opened"),("search","URL on official site"),("secondary","Secondary source opened"),("knowledge","Not checked live")]

def esc(s): return html.escape(str(s),quote=True)

# ---------- geometry ----------
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

svg=[f'<svg class="fig" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Regulatory map">']
svg.append('<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" class="hatch-bg"/><line x1="0" y1="0" x2="0" y2="6" class="hatch-ln"/></pattern></defs>')
# gate-range shading layer (toggled by JS)
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

def bar_status(ids):
    sts={NB[i]["status"] for i in ids}
    return NB[ids[0]]["status"] if len(sts)==1 else "mixed"

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
        svg.append(f'<g class="{barcls}" data-ids="{" ".join(ids)}" data-dom="{dom}" data-a="{a}" data-b="{b}" data-y="{yy}" data-row="{ri}">')
        svg.append(f'<rect x="{x}" y="{yy}" width="{w}" height="{CH}" rx="{10 if "prog" in cls else 2}" class="{cls}"/>')
        # jurisdiction stripe(s) at the left edge: one segment per region present in the bar
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
            if n.get("url"): t=f'<a href="{esc(n["url"])}" target="_blank" rel="noopener">{t}</a>'
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
    keys=[P[s][3] for s in sorted(addr[c["id"]]) if s in P]
    panel_rows.append(f'<li><b>{esc(c["label"])}.</b> {esc(c["scope"])} {("<i>Addressed in:</i> "+esc("; ".join(keys))+".") if keys else "<i class=gap>Gap — no document in the graph addresses this directly.</i>"}</li>')
PANEL="\n".join(panel_rows)

# ---------- Table 1 ----------
ISSUER={"ICH":"ICH","EU":"EMA / European Commission","US":"FDA / US Congress","JP":"MHLW / PMDA","UK":"MHRA / UK Parliament","INTL":"OSWG"}
STL=dict(STATUSES); VL=dict(VERIF)
order=sorted(docs,key=lambda n:(DOMAINS.index(next(d for d in DOMAINS if d[0]==P[n["id"]][0])),P[n["id"]][1],P[n["id"]][3]))
trs=[]
for n in order:
    key=P[n["id"]][3]; dom=dict(DOMAINS)[P[n["id"]][0]].replace("|"," ")
    link=f'<a href="{esc(n["url"])}" target="_blank" rel="noopener">{esc(n["label"])}</a>' if n.get("url") else esc(n["label"])
    note=n.get("status_note") or ""; note=note if len(note)<=90 else note[:88]+"…"
    trs.append(f'<tr data-id="{n["id"]}"><td class="k"><span class="rdot r-{n["region"]}"></span>{esc(key)}</td><td>{link}</td><td>{esc(dom)}</td>'
               f'<td>{esc(ISSUER.get(n["region"],n["region"]))}</td><td class="mono">{esc(n.get("ref") or "—")}</td><td class="mono">{esc(n.get("date") or "—")}</td>'
               f'<td><span class="stchip st-{n["status"]}">{esc(STL.get(n["status"],n["status"]))}</span>{("<br><span class=note2>"+esc(note)+"</span>") if note else ""}</td>'
               f'<td>{esc(VL.get(n.get("verification"),"—"))}</td></tr>')
TABLE="\n".join(trs)

def chips(name,items,cls="fchip"):
    return "".join(f'<button class="{cls}" data-f="{name}" data-v="{v}" aria-pressed="true">{esc(l)}</button>' for v,l in items)
F_REGION=chips("region",[(r,r) for r in REGIONS])
F_STATUS=chips("status",STATUSES)
F_DOMAIN=chips("domain",[(d,l.replace("|"," ")) for d,l in DOMAINS])
F_VERIF=chips("verif",VERIF)
OVBTN="".join(f'<button class="ov" data-ov="{k}" aria-pressed="false">{esc(lab)}</button>' for k,(lab,_) in OVERLAYS.items())
GATE_OPTS="".join(f'<option value="{i}">{esc(l)}</option>' for i,(_,l) in enumerate(GATES))
OVJSON=json.dumps({k:ids for k,(lab,ids) in OVERLAYS.items()})

# ---------- Audit + roadmap content ----------
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
<li>Product-specific precedent (assessment reports, labels) — a possible future node type, listed under open decisions.</li>
</ul></div>
<div><h3>Reading the verification fields</h3><ul>
<li><b>Source opened</b>: the official page or PDF was read during the check.</li>
<li><b>URL on official site</b>: the document was located on the issuing body’s domain but not opened.</li>
<li><b>Secondary source opened</b>: a non-official source (law-firm summary, library record) was read because the primary text could not be reached.</li>
<li><b>Not checked live</b>: carried from prior knowledge. As of 28 October 2026 no document is in this state.</li>
<li>Negative results are recorded with the date they were established, so that “nothing found” is distinguishable from “not looked”.</li>
</ul></div>
</div>'''

CHANGES='''
<p class="figtitle"><b>What changed in data v0.3</b> (28 October 2026)</p>
<ul class="chg">
<li><b>Data model:</b> every node carries <code>domain</code>, <code>gate_from</code>/<code>gate_to</code>, a unique <code>key</code>, optional <code>group</code>, <code>triggers</code> and <code>last_checked</code>; <code>phase</code> and stored <code>governs_phase</code> edges are gone (gate links are regenerated at build time under <code>derived</code>). Figure placement and series aggregation now come from the data; the renderer holds no layout facts.</li>
<li><b>Content:</b> the intrathecal/CNS gap is closed with four consensus and methodology references (two opened and cited in full); hepatotoxicity and nephrotoxicity each gained an FDA clinical guidance; revision history added (Q1A(R2) → consolidated Q1, E6(R2) → E6(R3), E9 + E9(R1), 2014 expedited-programs guidance → 2024 accelerated-approval draft).</li>
<li><b>Verification:</b> the four US statutes were re-verified on primary govinfo texts; ICH Q14 on the EMA page; the sponsor-investigator IND draft via its Federal Register notice; no document remains “not checked live”. EDQM newsroom and Pharmeuropa 38.2 confirmed the absence of an oligonucleotide chapter (negative result, dated).</li>
<li><b>Tooling:</b> <code>validate.py</code> (schema, integrity, unique keys, span and group consistency, orphan check, optional link report) and a CI workflow that runs it on every change and the link check quarterly.</li>
<li><b>Second pass (same day):</b> Korte et al. 2020 fully cited; USP negative result dated; EMA drug–device guideline and 21 CFR Part 4 added for device-delivered CNS programmes; accelerated assessment and conditional MA spans start at Phase 3; Rare Pediatric Disease voucher linked to the govinfo text of Pub. L. 119-75.</li>
<li><b>Page:</b> Hide now also applies to programme-type selections and collapses empty rows and lanes; “Table follows filters” shows its state and the row count; superseded documents are drawn struck through.</li>
</ul>'''

OPEN='''
<p class="figtitle" id="open"><b>Open items</b> — everything still to be checked or decided, as of 28 October 2026</p>
<div class="cols open">
<div><h3>A · Needs a practitioner or a decision</h3><ol>
<li><b>Span review.</b> All gate spans were set by one author. Priority: the quality lane (do all ICH Q texts really engage at CTA?), the paediatric lane, and the rare lane. Accelerated assessment and conditional MA were moved in this pass to start at Phase 3 (strategy) rather than at filing (request) — confirm.</li>
<li><b>Trigger coverage.</b> The six programme-type sets were seeded by one author; baseline documents that should also carry a trigger (e.g. ICH M3(R2) for intrathecal, ICH S11 for every paediatric programme) have not been reviewed.</li>
<li><b>Paediatric-oncology set</b> — review by someone who has taken a PIP through PDCO.</li>
<li><b>Node type for product precedent</b> (assessment reports and labels of approved oligonucleotides) — add or not.</li>
<li><b>Default view</b> — keep jurisdiction stripes on a mixed map, or default to one jurisdiction.</li>
<li><b>Authorship.</b> CITATION.cff names and ORCID; licence holder in LICENSE.</li>
</ol></div>
<div><h3>B · Sources not fully reached</h3><ol start="7">
<li><b>IT nerve-fibre opinion</b> (Toxicologic Pathology Forum): DOI, authors and year not found; only a library record.</li>
<li><b>Rare Pediatric Disease voucher:</b> Pub. L. 119-75 confirmed on govinfo, but the reauthorising sections (CAA 2026 §§6601–6605) were not reached; the 2029-09-30 date rests on a law-firm summary. Voucher-award sunset unknown.</li>
<li><b>PIP format guideline 2014/C 338/01:</b> EUR-Lex text not opened; EMA news of 30 Sept 2014 corroborates.</li>
<li><b>39 documents</b> are “URL on official site” without the page opened. A one-time pass opening each would move them to “source opened”; the quarterly link check catches dead links, not content drift.</li>
<li><b>Korte et al. 2020</b> (IT NHP lesions): citation from a library record; full text not read.</li>
</ol></div>
<div><h3>C · Moving targets (re-check dates)</h3><ol start="12">
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
<div><h3>D · Product and tooling</h3><ol start="21">
<li>Hide mode keeps a one-row minimum for empty lanes; decide whether empty lanes should vanish.</li>
<li>Status tints chosen to differ in lightness; not yet run through a colour-vision simulator.</li>
<li>SVG export is light-theme only.</li>
<li>Explorer and map are two pages; the merge with shared filters (Phase C) is pending.</li>
<li>CI link check is informational; decide whether a 404 on an official URL should fail the build.</li>
</ol></div>
</div>'''

AUDIT='''
<p class="figtitle"><b>Audit of data v0.2</b> (28 October 2026, before the v0.3 changes above), measured on the graph itself</p>
<div class="cols">
<div><h3>Structure</h3><ul>
<li><b>No domain dimension.</b> 50 of 92 nodes are typed <code>guideline</code>, which does not separate quality from nonclinical from clinical. 26 nodes sat in a <code>cross_cutting</code> phase bucket that carries no information. The map above introduces six domains instead.</li>
<li><b>Phase is a point, applicability is a span.</b> 64 documents had <code>governs_phase</code> edges, only 7 to more than one gate; 22 converged on “filing” and 14 on “nonclinical”, making those milestones hubs with no discriminating value. The map replaces the edges by placement across gates.</li>
<li><b>Modality is almost unused.</b> 81 of 92 nodes carry <code>all_oligo</code>; programme-type triggers (AOC, LNP, intrathecal, individualised, paediatric oncology) existed only in prose. The highlight buttons above are a first mapping and belong in the data.</li>
<li><b>Edge mix.</b> 73 of 148 relations were <code>governs_phase</code>; the remaining <code>references</code>, <code>amends</code> and <code>addresses</code> edges are the ones worth drawing, and the explorer should show only those.</li>
</ul></div>
<div><h3>Content</h3><ul>
<li><b>Intrathecal / CNS delivery</b> is a consideration with no document addressing it — the most important gap for paediatric brain-tumour programmes.</li>
<li><b>Hepatotoxicity and nephrotoxicity</b> each hang on a single document (FDA oligo nonclinical draft).</li>
<li><b>8 documents are not checked live</b>, among them the four US statutes (RACE, PREA, BPCA, Orphan Drug Act) whose links follow URL patterns rather than opened pages.</li>
<li><b>Ph. Eur. and USP</b> have no dedicated oligonucleotide chapter that could be confirmed; that negative result is itself a finding worth stating.</li>
<li><b>Two designations are drawn as applying at filing only</b> (accelerated assessment, conditional MA) although their strategy starts earlier; spans should be reviewed by someone who has run them.</li>
</ul></div>
<div><h3>Presentation (previous explorer)</h3><ul>
<li>Force layout is non-deterministic: positions differ on every load, so the view cannot serve as a reference figure.</li>
<li>Colour carried jurisdiction, but the decision-relevant variable is status: ICH is 96% in force, US documents are 27% drafts.</li>
<li>Labels averaged 45 characters; keys of ≤22 characters are needed for a figure and a citable register.</li>
</ul></div>
</div>'''

ROADMAP='''
<p class="figtitle"><b>Roadmap</b> — from reference map to maintained open resource</p>
<div class="rm">

<section><h3>Phase A · Data model v0.3 <span class="when done">done · 28 Oct 2026</span></h3>
<p>Goal: one source of truth from which both the map and the explorer are generated, with no layout decisions hidden in renderer code.</p>
<ul>
<li><b>Add <code>domain</code></b> (quality, nonclin, clinical, paed, rare, auth). Removes the <code>cross_cutting</code> bucket. <i>Acceptance:</i> zero nodes without a domain.</li>
<li><b>Replace <code>phase</code> with <code>gate_from</code> / <code>gate_to</code></b> on the eight-gate scale used above. Derive initial spans from the existing edges and the domain defaults in <code>build_figure.py</code>, then review by hand. <i>Acceptance:</i> every document has a span; <code>governs_phase</code> edges are regenerated from spans, not stored.</li>
<li><b>Add <code>key</code></b> (unique, ≤22 characters) for figure labels and citation in the register, and <b><code>group</code></b> so that series aggregation is data, not code.</li>
<li><b>Add <code>triggers</code></b>: list of programme types a document is engaged by (<code>aoc</code>, <code>lnp</code>, <code>galnac</code>, <code>intrathecal</code>, <code>individualised</code>, <code>paed_onc</code>). Seed from the overlay sets above; extend to all 73 documents.</li>
<li><b>Add <code>supersedes</code> edges</b> for revisions (Q1A(R2) → consolidated Q1; 2014 expedited-programs guidance → 2024 accelerated-approval draft; E9 → E9(R1)) and <code>last_checked</code> per document.</li>
<li><b>Validation in CI:</b> JSON schema, referential integrity, unique keys, span sanity (<code>gate_from ≤ gate_to</code>), and a link check that records HTTP status per document.</li>
</ul></section>

<section><h3>Phase B · Content completion <span class="when done">done except practitioner review · 28 Oct 2026</span></h3>
<p>Goal: close the gaps the audit found and raise every document to “source opened”.</p>
<ul>
<li><b>Intrathecal / CNS route — done.</b> Four consensus/methodology references added (see Panel 1); no binding agency guidance specific to the IT route was found, stated as a dated negative result. Device/combination aspects covered by the EMA drug–device guideline and 21 CFR Part 4, both opened. <s>Identify and add the guidance that governs IT/ICV administration: route-specific nonclinical expectations (local tolerance, CNS histopathology, CSF pharmacokinetics), the device/combination aspects of catheters and ports, and paediatric procedural safety. Add OSWG and agency precedent where it exists; record a negative result with date where it does not.</s></li>
<li><b>Class toxicities — done.</b> FDA DILI (2009) and renal-impairment PK (2024) guidances added and linked. <s>Link hepatotoxicity to the FDA drug-induced liver injury guidance and nephrotoxicity to the renal-impairment pharmacokinetics guidance (both to be verified and dated), so that each consideration rests on more than one document.</s></li>
<li><b>Verify the eight knowledge-only entries — done.</b> Zero remain; one (the 2014 PIP format guideline) rests on an EMA news item rather than the EUR-Lex text. <s>by opening the statute pages (uscode.house.gov, congress.gov) and recording section numbers. <i>Acceptance:</i> zero documents with <code>verification = knowledge</code>.</s></li>
<li><b>Pharmacopoeias — done.</b> Negative results recorded and dated for Ph. Eur. (EDQM newsroom, Pharmeuropa 38.2) and USP (standards page, Expert Committee work plan), 28 Oct 2026. <s>Check Pharmeuropa and Pharmacopeial Forum for a draft oligonucleotide chapter; if none, state the negative finding explicitly in the register rather than leaving the entries “unverified”.</s></li>
<li><b>Review spans with practitioners — open (item 1 below).</b> Accelerated assessment and conditional MA were moved to start at Phase 3 in this pass; the rest awaits a second pair of eyes.</li>
<li><b>Scope statement — done</b> (section above). <s>Document what is deliberately out of scope (China NMPA, Health Canada, TGA; pharmacovigilance and RMP; GMP inspection law) so that absence is not read as omission.</s></li>
</ul></section>

<section><h3>Phase C · Product <span class="when">weeks 4–8</span></h3>
<p>Goal: one page, three views, shared filters, stable links.</p>
<ul>
<li><b>Tabs:</b> Map (this view, default), Explore (the force graph, drawing only <code>references</code>/<code>amends</code>/<code>supersedes</code> edges), Register (Table 1 with sorting). Filters apply to all three; the active view sits in the URL hash so it can be linked.</li>
<li><b>Filters:</b> the set implemented above (jurisdiction, status, domain, verification, gate range, programme type, search, dim/hide) plus a saved-filter preset per programme type.</li>
<li><b>Export:</b> copy SVG (done), copy filtered register as CSV, and a print stylesheet that renders Figure 1, Panel 1 and Table 1 on A4.</li>
<li><b>Accessibility:</b> keyboard focus for bars, colour choices checked for the common colour-vision deficiencies (status hues are chosen to differ in lightness, not only in hue).</li>
</ul></section>

<section><h3>Phase D · Release and governance <span class="when">weeks 6–10</span></h3>
<p>Goal: citable, correctable, maintained.</p>
<ul>
<li><b>Repository</b> with the generator, data, schema, CONTRIBUTING and an issue template per correction (one document per issue: URL, number, date, status). CI runs the validation above on every change.</li>
<li><b>Zenodo deposit</b> with a versioned DOI; CITATION.cff completed; the DOI shown on the page.</li>
<li><b>Re-verification cadence:</b> quarterly link and status check; a changelog that records every status transition (draft → final, in force → superseded) with the date it was noticed.</li>
<li><b>Companion article:</b> a regulatory map for oligonucleotide therapeutics with a paediatric-oncology worked example. Figure 1 is this map, Panel 1 the considerations, Table 1 the register, the JSON the supplement. The map’s value to a reviewer is that it is generated, so the figure cannot drift from the data.</li>
<li><b>Outreach</b> to the groups that would use and correct it: oligonucleotide therapeutics societies, paediatric trial networks and strategy forums, regulatory-science working groups.</li>
</ul></section>

<section><h3>Open decisions</h3><p>Consolidated with everything else still unverified in <a href="#open">Open items</a> at the end of the page.</p></section>
</div>'''

page=f'''<title>Oligo Regulatory Map</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap">
<style>
/* Journal-figure treatment with colour for orientation: status = bar fill (six tints differing in lightness as
   well as hue), jurisdiction = saturated stripe + tag. One red accent reserved for highlights. */
:root{{--bg:#ffffff;--ink:#111111;--ink2:#555555;--ink3:#8a8a8a;--rule:#1a1a1a;--hair:#d9d9d9;
  --lane:#fafafa;--lane-alt:#f3f3f3;--accent:#c8102e;--accent-soft:#fbe9ec;--mask:rgba(0,0,0,.05);
  --st-in_force:#dce8f2;--st-in_force-b:#4f7ea8;--st-draft:#fff0cf;--st-draft-b:#c98f12;
  --st-pending:#ece4f8;--st-pending-b:#7b5cb8;--st-programme:#e2f2e4;--st-programme-b:#3f8f52;
  --st-guidance:#f0f0f0;--st-guidance-b:#8a8a8a;--st-verify:#fde6e9;--st-verify-b:#c8102e;--st-mixed:#e9eef2;--st-mixed-b:#6b8093;
  --r-ICH:#3f6fb0;--r-EU:#1f9d8f;--r-US:#c6603a;--r-JP:#9a5bb8;--r-UK:#4e8d4a;--r-INTL:#7d8287;
  --serif:"Source Serif 4",Georgia,"Times New Roman",serif;--sans:"Helvetica Neue",Helvetica,Arial,sans-serif}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#121212;--ink:#ececec;--ink2:#b5b5b5;--ink3:#8c8c8c;
  --rule:#e6e6e6;--hair:#333;--lane:#171717;--lane-alt:#1e1e1e;--accent:#ff4d5e;--accent-soft:#3a1a1f;--mask:rgba(255,255,255,.06);
  --st-in_force:#1f3447;--st-in_force-b:#7fb0dc;--st-draft:#3d2e0c;--st-draft-b:#e4b24a;--st-pending:#2c2240;--st-pending-b:#b59be6;
  --st-programme:#1c3322;--st-programme-b:#7cc78e;--st-guidance:#262626;--st-guidance-b:#9a9a9a;--st-verify:#3a1a1f;--st-verify-b:#ff6b7a;
  --st-mixed:#232b32;--st-mixed-b:#9db0c2;--r-ICH:#6f9fe0;--r-EU:#39c4b4;--r-US:#e8865e;--r-JP:#c084e0;--r-UK:#78bf72;--r-INTL:#aab2b5;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#121212;--ink:#ececec;--ink2:#b5b5b5;--ink3:#8c8c8c;--rule:#e6e6e6;--hair:#333;--lane:#171717;--lane-alt:#1e1e1e;
  --accent:#ff4d5e;--accent-soft:#3a1a1f;--mask:rgba(255,255,255,.06);--st-in_force:#1f3447;--st-in_force-b:#7fb0dc;--st-draft:#3d2e0c;--st-draft-b:#e4b24a;
  --st-pending:#2c2240;--st-pending-b:#b59be6;--st-programme:#1c3322;--st-programme-b:#7cc78e;--st-guidance:#262626;--st-guidance-b:#9a9a9a;
  --st-verify:#3a1a1f;--st-verify-b:#ff6b7a;--st-mixed:#232b32;--st-mixed-b:#9db0c2;--r-ICH:#6f9fe0;--r-EU:#39c4b4;--r-US:#e8865e;--r-JP:#c084e0;--r-UK:#78bf72;--r-INTL:#aab2b5;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--serif);font-size:15px;line-height:1.5;
  padding-block:28px 56px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
.wrap{{max-width:1180px;margin:0 auto}}
h1{{font-family:var(--sans);font-size:22px;letter-spacing:-.01em;margin:0 0 4px;text-wrap:balance}}
h3{{font-family:var(--sans);font-size:13.5px;margin:0 0 6px}}
.byline{{font-family:var(--sans);font-size:12.5px;color:var(--ink2);margin:0 0 22px}}
.figtitle{{font-family:var(--sans);font-size:14px;margin:26px 0 8px}} .figtitle b{{font-weight:700}}
code{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.9em;background:var(--lane-alt);padding:0 4px;border-radius:3px}}
/* filters */
.filters{{font-family:var(--sans);font-size:12px;border:1px solid var(--hair);border-radius:6px;padding:10px 12px;margin:0 0 10px;
  display:grid;grid-template-columns:1fr 1fr;gap:8px 18px}}
.frow{{display:flex;flex-wrap:wrap;gap:5px;align-items:center;min-width:0}}
.frow .lab{{color:var(--ink2);min-width:92px;font-weight:700;font-size:11px;letter-spacing:.03em;text-transform:uppercase}}
.fchip,.ov,.tbtn{{font:inherit;color:var(--ink);background:transparent;border:1px solid var(--hair);border-radius:14px;padding:3px 9px;cursor:pointer;line-height:1.3}}
.fchip[aria-pressed="false"]{{opacity:.42;text-decoration:line-through}}
.fchip .sw{{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:5px;vertical-align:-1px}}
.ov[aria-pressed="true"]{{border-color:var(--accent);background:var(--accent-soft)}}
.tbtn{{border-radius:6px}}
.frow input[type=search],.frow select{{font:inherit;color:var(--ink);background:var(--bg);border:1px solid var(--hair);border-radius:6px;padding:4px 8px}}
.frow input[type=search]{{min-width:200px;flex:1}}
.fwide{{grid-column:1 / -1}}
.count{{margin-left:auto;color:var(--ink2);font-variant-numeric:tabular-nums}}
.seg{{display:inline-flex;border:1px solid var(--hair);border-radius:6px;overflow:hidden}}
.seg button{{font:inherit;color:var(--ink);background:transparent;border:0;padding:3px 9px;cursor:pointer}}
.seg button[aria-pressed="true"]{{background:var(--lane-alt);font-weight:700}}
/* figure */
.figbox{{border-top:1.5px solid var(--rule);border-bottom:1.5px solid var(--rule);padding:12px 0 6px;overflow-x:auto}}
svg.fig{{display:block;font-family:var(--sans);max-width:none}}
.spine{{stroke:var(--rule);stroke-width:1.2;fill:none}} .grid{{stroke:var(--hair);stroke-width:.6}}
.gate{{font-size:11px;font-weight:700;fill:var(--ink)}} .gate-sub{{font-size:9px;fill:var(--ink2)}} .eop2{{fill:var(--accent)}}
.lane{{fill:var(--lane)}} .lane.alt{{fill:var(--lane-alt)}}
.lane-lab{{font-size:10.5px;font-weight:700;fill:var(--ink);letter-spacing:.02em}}
.colmask{{fill:var(--mask);opacity:0;pointer-events:none}} .colmask.out{{opacity:1}}
.chip{{stroke-width:.9}}
.chip.st-in_force{{fill:var(--st-in_force);stroke:var(--st-in_force-b)}}
.chip.st-draft{{fill:var(--st-draft);stroke:var(--st-draft-b);stroke-dasharray:3 2}}
.chip.st-pending{{fill:var(--st-pending);stroke:var(--st-pending-b)}}
.chip.st-programme{{fill:var(--st-programme);stroke:var(--st-programme-b)}}
.chip.st-guidance{{fill:var(--st-guidance);stroke:var(--st-guidance-b);stroke-dasharray:1 2}}
.chip.st-verify{{fill:var(--st-verify);stroke:var(--st-verify-b);stroke-dasharray:3 2}}
.chip.st-mixed{{fill:var(--st-mixed);stroke:var(--st-mixed-b)}}
.chip.st-superseded{{fill:var(--st-guidance);stroke:var(--st-guidance-b)}} .bar.st-superseded .k{{text-decoration:line-through}}
.tbtn[aria-pressed="true"]{{background:var(--accent-soft);border-color:var(--accent)}}
.chip.law{{stroke-width:1.5}}
.hatch-bg{{fill:var(--bg)}} .hatch-ln{{stroke:var(--hair);stroke-width:1}}
.stripe{{pointer-events:none}}
.r-ICH{{fill:var(--r-ICH)}} .r-EU{{fill:var(--r-EU)}} .r-US{{fill:var(--r-US)}} .r-JP{{fill:var(--r-JP)}} .r-UK{{fill:var(--r-UK)}} .r-INTL{{fill:var(--r-INTL)}}
.key{{font-size:9.5px;fill:var(--ink)}} .reg{{font-size:8px;font-weight:700;letter-spacing:.04em}} .sep{{fill:var(--ink3)}}
svg.fig a{{text-decoration:none}} .k{{cursor:pointer}} .k:hover{{fill:var(--accent)}}
.bar.hi .chip{{stroke:var(--accent);stroke-width:2}} .k.hi{{font-weight:700}}
.bar.lo,.k.lo{{opacity:.22}} .bar.off,.k.off,.sep.off,.lanegrp.off{{display:none}}
/* legend */
.legend{{font-size:13.5px;margin:10px 0 0}} .legend .abbr{{font-size:12.5px;color:var(--ink2);margin-top:6px}}
.keyrow{{font-family:var(--sans);font-size:11.5px;display:flex;flex-wrap:wrap;gap:6px 14px;margin:8px 0 0;color:var(--ink2)}}
.keyrow span{{display:inline-flex;align-items:center;gap:5px}}
.sw{{display:inline-block;width:14px;height:10px;border-radius:2px;border:1px solid}}
.swd{{display:inline-block;width:10px;height:10px;border-radius:50%}}
/* panel, table, sections */
.panel{{border:1px solid var(--rule);padding:14px 18px;margin:30px 0 0}} .panel h2{{font-family:var(--sans);font-size:14px;margin:0 0 8px}}
.panel ol{{margin:0;padding-left:20px}} .panel li{{margin:0 0 7px;font-size:14px}} .panel li b{{font-weight:600}} .panel li i{{color:var(--ink2)}} .gap{{color:var(--accent)}}
table{{border-collapse:collapse;width:100%;min-width:900px;table-layout:fixed;font-family:var(--sans);font-size:12px;margin-top:8px}}
thead th{{text-align:left;font-weight:700;border-top:1.5px solid var(--rule);border-bottom:1px solid var(--rule);padding:7px 8px 6px}}
tbody td{{padding:6px 8px;vertical-align:top;border-bottom:1px solid var(--hair)}} tbody tr:last-child td{{border-bottom:1.5px solid var(--rule)}}
tbody tr.off{{display:none}}
td.k{{font-weight:600}} td.mono{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;overflow-wrap:anywhere}} .note2{{color:var(--ink2);font-size:11px}}
.rdot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:0}}
.stchip{{display:inline-block;font-size:11px;font-weight:700;padding:1px 7px;border-radius:10px;border:1px solid}}
.stchip.st-in_force{{background:var(--st-in_force);border-color:var(--st-in_force-b)}} .stchip.st-draft{{background:var(--st-draft);border-color:var(--st-draft-b)}}
.stchip.st-pending{{background:var(--st-pending);border-color:var(--st-pending-b)}} .stchip.st-programme{{background:var(--st-programme);border-color:var(--st-programme-b)}}
.stchip.st-guidance{{background:var(--st-guidance);border-color:var(--st-guidance-b)}} .stchip.st-superseded{{background:var(--st-guidance);border-color:var(--st-guidance-b);text-decoration:line-through}} .stchip.st-verify{{background:var(--st-verify);border-color:var(--st-verify-b)}}
.tablewrap{{overflow-x:auto;margin-top:28px}} .fn{{font-size:12.5px;color:var(--ink2);margin-top:6px}}
a{{color:var(--ink);text-decoration:underline;text-decoration-color:var(--ink3);text-underline-offset:2px}}
.cols{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;font-size:13.5px}} .cols ul{{margin:0;padding-left:18px}} .cols li{{margin-bottom:6px}}
.rm section{{border-top:1px solid var(--hair);padding:12px 0 6px}} .rm ul{{margin:4px 0 0;padding-left:20px}} .rm li{{margin-bottom:6px;font-size:14px}}
.rm p{{margin:0 0 4px;font-size:14px;color:var(--ink2)}} .rm s{{color:var(--ink3)}}
.when.done{{color:var(--st-programme-b);font-weight:700}} .open ol{{margin:0;padding-left:20px}} .open li{{margin-bottom:6px;font-size:13.5px}} .chg{{font-size:14px;padding-left:20px}} .chg li{{margin-bottom:6px}} .when{{font-weight:400;color:var(--ink2);margin-left:8px;font-size:12px}}
.note{{font-size:13px;color:var(--ink2);margin:26px 0 0;border-top:1px solid var(--hair);padding-top:10px}}
@media (max-width:900px){{.cols{{grid-template-columns:1fr}} .filters{{grid-template-columns:1fr}}}}
@media (max-width:760px){{body{{font-size:14px}} h1{{font-size:19px}} .frow .lab{{min-width:100%}}}}
</style>
<div class="wrap">
<h1>Regulatory requirements for oligonucleotide therapeutics</h1>
<p class="byline">Development map · ICH, EU, US, Japan, UK · data v{esc(g["meta"]["version"])}, {esc(g["meta"]["generated"])} · {len(docs)} documents, {len(cons)} oligonucleotide-specific considerations</p>

<p class="figtitle"><b>Figure 1:</b> Regulatory documents mapped to development gates and regulatory domains</p>
<div class="filters" id="filters">
  <div class="frow"><span class="lab">Jurisdiction</span>{F_REGION}</div>
  <div class="frow"><span class="lab">Status</span>{F_STATUS}</div>
  <div class="frow"><span class="lab">Domain</span>{F_DOMAIN}</div>
  <div class="frow"><span class="lab">Verification</span>{F_VERIF}</div>
  <div class="frow"><span class="lab">Gates</span><select id="gFrom" aria-label="From gate">{GATE_OPTS}</select><span>to</span><select id="gTo" aria-label="To gate">{GATE_OPTS}</select></div>
  <div class="frow"><span class="lab">Search</span><input id="q" type="search" placeholder="key, title or reference…" autocomplete="off"></div>
  <div class="frow fwide"><span class="lab">Programme type</span>{OVBTN}
    <span class="seg" role="group" aria-label="Non-matching documents"><button id="mDim" aria-pressed="true">Dim</button><button id="mHide" aria-pressed="false">Hide</button></span>
    <button class="tbtn" id="syncTbl" aria-pressed="true">Table follows filters</button>
    <button class="tbtn" id="reset">Reset</button><button class="tbtn" id="copySvg">Copy SVG</button>
    <span class="count" id="count"></span></div>
</div>
<div class="figbox">{SVG}</div>
<div class="keyrow">
  <span><b>Status</b></span>
  <span><i class="sw" style="background:var(--st-in_force);border-color:var(--st-in_force-b)"></i>In force</span>
  <span><i class="sw" style="background:var(--st-draft);border-color:var(--st-draft-b);border-style:dashed"></i>Draft</span>
  <span><i class="sw" style="background:var(--st-pending);border-color:var(--st-pending-b)"></i>Pending adoption</span>
  <span><i class="sw" style="background:var(--st-programme);border-color:var(--st-programme-b);border-radius:6px"></i>Programme / designation</span>
  <span><i class="sw" style="background:var(--st-guidance);border-color:var(--st-guidance-b);border-style:dotted"></i>Non-binding consensus</span>
  <span><i class="sw" style="background:var(--st-verify);border-color:var(--st-verify-b);border-style:dashed"></i>Unverified</span>
  <span><i class="sw" style="background:var(--st-guidance);border-color:var(--st-guidance-b)"></i><s>Superseded</s></span>
  <span><i class="sw" style="background:var(--st-mixed);border-color:var(--st-mixed-b)"></i>Series with mixed status</span>
</div>
<div class="keyrow">
  <span><b>Jurisdiction</b></span>
  {"".join(f'<span><i class="swd" style="background:var(--r-{r})"></i>{r}</span>' for r in REGIONS)}
  <span style="margin-left:auto">Bold outline = binding legal act · rounded = designation or programme</span>
</div>
<p class="legend">Each bar is one document or one series of documents with the same applicability, placed in its regulatory domain and spanning the development gates at which it applies. Bar colour encodes status; the stripe at the left edge and the tag before each key encode the issuing jurisdiction. The red diamond marks the end-of-phase-2 interaction, where paediatric plan obligations (PIP in the EU, iPSP in the US) cluster. Programme-type buttons highlight the documents additionally engaged by that programme; the paediatric-oncology set reflects RACE Act and Paediatric Regulation obligations for molecularly targeted agents. Hover a key for the full title, reference and status; click to open the source. “Dim” keeps non-matching documents visible at low opacity; “Hide” removes them, treats a programme-type selection as a filter, and closes up empty rows and lanes.</p>
<p class="legend abbr">AOC=antibody–oligonucleotide conjugate. ASO=antisense oligonucleotide. CMC=chemistry, manufacturing and controls. CTA=clinical trial application. CTD=common technical document. EoP2=end of phase 2. GL=guideline. iASO=individualised ASO. IMPD=investigational medicinal product dossier. IND=investigational new drug application. iPSP=initial paediatric study plan. LNP=lipid nanoparticle. MA=marketing authorisation. MRCT=multi-regional clinical trial. OSWG=Oligonucleotide Safety Working Group. PIP=paediatric investigation plan. RDEP=Rare Disease Evidence Principles. RPD=rare paediatric disease. TK=toxicokinetics.</p>

<div class="panel"><h2>Panel 1: Oligonucleotide-specific considerations and where the documents address them</h2><ol>{PANEL}</ol></div>

<p class="figtitle"><b>Table 1:</b> Document register with reference, status and verification</p>
<div class="tablewrap"><table id="tbl"><colgroup><col style="width:13%"><col style="width:29%"><col style="width:9%"><col style="width:10%"><col style="width:15%"><col style="width:7%"><col style="width:11%"><col style="width:6%"></colgroup>
<thead><tr><th>Key</th><th>Document</th><th>Domain</th><th>Issuer</th><th>Reference</th><th>Date</th><th>Status</th><th>Checked</th></tr></thead><tbody>{TABLE}</tbody></table></div>
<p class="fn">Keys match the bars in figure 1; the dot before each key gives the jurisdiction. “Checked” records how the entry was verified in October 2026: source opened=official page or PDF read; URL on official site=document located on the issuing body’s domain without opening it; not checked live=taken from prior knowledge.</p>

{SCOPE}
{CHANGES}
{AUDIT}
{ROADMAP}
{OPEN}

<p class="note">{esc(g["meta"]["disclaimer"])} Data: CC BY 4.0. Layout generated deterministically from the graph data; the same input always yields the same figure.</p>
</div>
<script>
(function(){{
const OV={OVJSON}; const NG={len(GATES)}; const CH={CH}, CGAP={CGAP}, PAD={LANEPAD}, TOP={TOP};
const svg=document.querySelector('svg.fig'), H0=+svg.getAttribute('height');
const bars=[...document.querySelectorAll('.bar')], keys=[...document.querySelectorAll('.k[data-id]')],
      lanes=[...document.querySelectorAll('.lanegrp')], rows=[...document.querySelectorAll('#tbl tbody tr')],
      masks=[...document.querySelectorAll('.colmask')], vlines=[...document.querySelectorAll('.vline')];
const S={{region:new Set(),status:new Set(),domain:new Set(),verif:new Set(),from:0,to:NG-1,q:'',ov:null,hide:false,sync:true}};
document.querySelectorAll('.fchip').forEach(b=>S[b.dataset.f].add(b.dataset.v));
const gFrom=document.getElementById('gFrom'),gTo=document.getElementById('gTo'); gTo.value=NG-1;
const docOf={{}}; keys.forEach(t=>{{const bar=t.closest('.bar');docOf[t.dataset.id]={{t,bar,region:t.dataset.region,status:t.dataset.status,verif:t.dataset.verif,dom:bar.dataset.dom,a:+bar.dataset.a,b:+bar.dataset.b,s:t.dataset.s}};}});
function passesFilters(d){{
  if(!S.region.has(d.region)||!S.status.has(d.status)||!S.domain.has(d.dom))return false;
  if(!S.verif.has(d.verif)&&d.verif!=='none')return false;
  if(d.b<S.from||d.a>S.to)return false;
  if(S.q&&!d.s.includes(S.q))return false;
  return true;
}}
// In Hide mode a programme-type selection acts as a filter; in Dim mode it is a highlight over the filter result.
function relayout(shown){{
  let y=TOP, h;
  lanes.forEach(l=>{{
    const lb=l.querySelectorAll('.bar'); const vis=[...lb].filter(b=>shown.has(b));
    const laneOn=S.domain.has(l.dataset.dom);
    l.classList.toggle('off',!laneOn);
    if(!laneOn)return;
    // first-fit rows for visible bars, keeping original ordering
    const rowsF=[]; vis.forEach(b=>{{const a=+b.dataset.a,bb=+b.dataset.b; let ri=rowsF.findIndex(r=>r.every(([ra,rb])=>bb<ra||a>rb));
      if(ri<0){{rowsF.push([[a,bb]]);ri=rowsF.length-1;}}else rowsF[ri].push([a,bb]);
      const ny=y+PAD+ri*(CH+CGAP); b.setAttribute('transform','translate(0,'+(ny-(+b.dataset.y))+')');}});
    h=PAD*2+Math.max(1,rowsF.length)*(CH+CGAP);
    const bg=l.querySelector('.lanebg'); bg.setAttribute('y',y); bg.setAttribute('height',h);
    const lab=l.querySelector('.lane-lab'); lab.setAttribute('y',y+16); lab.querySelectorAll('tspan').forEach((t,i)=>{{if(i===0)t.removeAttribute('y');}});
    y+=h;
  }});
  const Hn=y+8; svg.setAttribute('height',Hn); svg.setAttribute('viewBox','0 0 '+svg.viewBox.baseVal.width+' '+Hn);
  vlines.forEach(v=>v.setAttribute('y2',Hn-6)); masks.forEach(m=>m.setAttribute('height',Hn-TOP));
}}
function restoreLayout(){{
  lanes.forEach(l=>{{l.classList.remove('off'); const bg=l.querySelector('.lanebg'); bg.setAttribute('y',l.dataset.y0); bg.setAttribute('height',l.dataset.h);
    l.querySelector('.lane-lab').setAttribute('y',+l.dataset.y0+16); l.querySelectorAll('.bar').forEach(b=>b.removeAttribute('transform'));}});
  svg.setAttribute('height',H0); svg.setAttribute('viewBox','0 0 '+svg.viewBox.baseVal.width+' '+H0);
  vlines.forEach(v=>v.setAttribute('y2',H0-6)); masks.forEach(m=>m.setAttribute('height',H0-TOP));
}}
function apply(){{
  const ov=S.ov?new Set(OV[S.ov]):null;
  const vis=new Set(); Object.keys(docOf).forEach(id=>{{const d=docOf[id]; if(passesFilters(d)&&!(S.hide&&ov&&!ov.has(id)))vis.add(id);}});
  const shownBars=new Set();
  bars.forEach(b=>{{const ids=b.dataset.ids.split(' ');const any=ids.some(i=>vis.has(i));
    b.classList.toggle('off',S.hide&&!any); b.classList.toggle('lo',!any);
    if(!(S.hide&&!any))shownBars.add(b);
    const hi=!!ov&&ids.some(i=>vis.has(i)&&ov.has(i)); b.classList.toggle('hi',hi);
    if(ov&&any&&!hi)b.classList.add('lo');
    let seen=false; ids.forEach(id=>{{const v=!S.hide||vis.has(id);const s=b.querySelector('.sep[data-sep-for="'+id+'"]');
      if(s)s.classList.toggle('off',!(v&&seen)); if(v)seen=true;}});
    const regs=[...new Set(ids.filter(i=>!S.hide||vis.has(i)).map(i=>docOf[i].region))];
    const st=[...b.querySelectorAll('.stripe')]; const y0=+st[0].dataset.y0,h=+st[0].dataset.h; let k=0;
    st.forEach(r=>{{const on=regs.includes(r.dataset.region); r.style.display=on?'':'none';
      if(on){{r.setAttribute('y',y0+k*(h/Math.max(1,regs.length)));r.setAttribute('height',h/Math.max(1,regs.length));k++;}}}});}});
  keys.forEach(t=>{{const id=t.dataset.id,v=vis.has(id);
    t.classList.toggle('off',S.hide&&!v); t.classList.toggle('lo',!S.hide&&!v);
    t.classList.toggle('hi',!!ov&&ov.has(id)&&v);
    if(ov&&v&&!ov.has(id))t.classList.add('lo');}});
  masks.forEach(m=>{{const c=+m.dataset.col;m.classList.toggle('out',c<S.from||c>S.to);}});
  if(S.hide)relayout(shownBars); else restoreLayout();
  rows.forEach(r=>r.classList.toggle('off',S.sync&&!vis.has(r.dataset.id)));
  const total=Object.keys(docOf).length;
  document.getElementById('count').textContent=vis.size+' of '+total+' documents'+(S.sync?' · table '+vis.size+' rows':' · table all rows');
}}
document.querySelectorAll('.fchip').forEach(b=>b.onclick=()=>{{const on=b.getAttribute('aria-pressed')!=='true';
  b.setAttribute('aria-pressed',on);on?S[b.dataset.f].add(b.dataset.v):S[b.dataset.f].delete(b.dataset.v);apply();}});
document.querySelectorAll('.ov[data-ov]').forEach(b=>b.onclick=()=>{{S.ov=b.getAttribute('aria-pressed')==='true'?null:b.dataset.ov;
  document.querySelectorAll('.ov[data-ov]').forEach(x=>x.setAttribute('aria-pressed',x.dataset.ov===S.ov));apply();}});
gFrom.onchange=()=>{{S.from=+gFrom.value;if(S.to<S.from){{S.to=S.from;gTo.value=S.to;}}apply();}};
gTo.onchange=()=>{{S.to=+gTo.value;if(S.from>S.to){{S.from=S.to;gFrom.value=S.from;}}apply();}};
document.getElementById('q').oninput=e=>{{S.q=e.target.value.trim().toLowerCase();apply();}};
const mDim=document.getElementById('mDim'),mHide=document.getElementById('mHide');
mDim.onclick=()=>{{S.hide=false;mDim.setAttribute('aria-pressed',true);mHide.setAttribute('aria-pressed',false);apply();}};
mHide.onclick=()=>{{S.hide=true;mDim.setAttribute('aria-pressed',false);mHide.setAttribute('aria-pressed',true);apply();}};
const syncB=document.getElementById('syncTbl'); syncB.onclick=()=>{{S.sync=!S.sync;syncB.setAttribute('aria-pressed',S.sync);
  syncB.textContent=S.sync?'Table follows filters':'Table shows all';apply();}};
document.getElementById('reset').onclick=()=>{{
  document.querySelectorAll('.fchip').forEach(b=>{{b.setAttribute('aria-pressed',true);S[b.dataset.f].add(b.dataset.v);}});
  S.from=0;S.to=NG-1;gFrom.value=0;gTo.value=NG-1;S.q='';document.getElementById('q').value='';S.ov=null;
  document.querySelectorAll('.ov[data-ov]').forEach(x=>x.setAttribute('aria-pressed',false));apply();}};
document.getElementById('copySvg').onclick=async e=>{{const b=e.currentTarget,o=b.textContent;
  try{{await navigator.clipboard.writeText(svg.outerHTML);b.textContent='SVG copied';}}catch{{b.textContent='Select & copy manually';}}
  setTimeout(()=>b.textContent=o,1500);}};
apply();
}})();
</script>
'''
open(os.path.join(PKG,"figure.html"),"w").write(page)

# standalone SVG with colours resolved (light theme) for manuscript use
LIGHT={"--bg":"#ffffff","--ink":"#111111","--ink2":"#555555","--ink3":"#8a8a8a","--rule":"#1a1a1a","--hair":"#d9d9d9",
 "--lane":"#fafafa","--lane-alt":"#f3f3f3","--accent":"#c8102e","--mask":"rgba(0,0,0,.05)",
 "--st-in_force":"#dce8f2","--st-in_force-b":"#4f7ea8","--st-draft":"#fff0cf","--st-draft-b":"#c98f12","--st-pending":"#ece4f8","--st-pending-b":"#7b5cb8",
 "--st-programme":"#e2f2e4","--st-programme-b":"#3f8f52","--st-guidance":"#f0f0f0","--st-guidance-b":"#8a8a8a","--st-verify":"#fde6e9","--st-verify-b":"#c8102e",
 "--st-mixed":"#e9eef2","--st-mixed-b":"#6b8093","--r-ICH":"#3f6fb0","--r-EU":"#1f9d8f","--r-US":"#c6603a","--r-JP":"#9a5bb8","--r-UK":"#4e8d4a","--r-INTL":"#7d8287"}
css='''.spine{stroke:var(--rule);stroke-width:1.2;fill:none}.grid{stroke:var(--hair);stroke-width:.6}.colmask{fill:none}
.gate{font-size:11px;font-weight:700;fill:var(--ink)}.gate-sub{font-size:9px;fill:var(--ink2)}.eop2{fill:var(--accent)}
.lane{fill:var(--lane)}.lane.alt{fill:var(--lane-alt)}.lane-lab{font-size:10.5px;font-weight:700;fill:var(--ink);letter-spacing:.02em}
.chip{stroke-width:.9}.chip.st-in_force{fill:var(--st-in_force);stroke:var(--st-in_force-b)}.chip.st-draft{fill:var(--st-draft);stroke:var(--st-draft-b);stroke-dasharray:3 2}
.chip.st-pending{fill:var(--st-pending);stroke:var(--st-pending-b)}.chip.st-programme{fill:var(--st-programme);stroke:var(--st-programme-b)}
.chip.st-guidance{fill:var(--st-guidance);stroke:var(--st-guidance-b);stroke-dasharray:1 2}.chip.st-verify{fill:var(--st-verify);stroke:var(--st-verify-b);stroke-dasharray:3 2}
.chip.st-mixed{fill:var(--st-mixed);stroke:var(--st-mixed-b)}.chip.law{stroke-width:1.5}.hatch-bg{fill:var(--bg)}.hatch-ln{stroke:var(--hair);stroke-width:1}
.r-ICH{fill:var(--r-ICH)}.r-EU{fill:var(--r-EU)}.r-US{fill:var(--r-US)}.r-JP{fill:var(--r-JP)}.r-UK{fill:var(--r-UK)}.r-INTL{fill:var(--r-INTL)}
.key{font-size:9.5px;fill:var(--ink)}.reg{font-size:8px;font-weight:700;letter-spacing:.04em}.sep{fill:var(--ink3)}text{font-family:Helvetica,Arial,sans-serif}'''
for k,v in LIGHT.items(): css=css.replace(f"var({k})",v)
s=SVG.replace('<svg class="fig"','<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" class="fig"',1)
s=s.replace('<defs>',f'<style>{css}</style><rect width="{W}" height="{H}" fill="#ffffff"/><defs>',1)
open(os.path.join(PKG,"figure1.svg"),"w").write(s)
print("figure.html",len(page),"bytes · figure1.svg · rows",rows_per_lane,"canvas",W,"x",H)
