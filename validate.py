#!/usr/bin/env python3
"""Validation for the oligonucleotide regulatory graph.

  python validate.py graph.json            # schema + integrity + span/key checks
  python validate.py graph.json --links    # additionally HEAD/GET every URL and write link-report.json

Exit code 1 on any failure. The link check never fails the build on its own (sites block bots);
it records the HTTP status per document so a human can review drift.
"""
import json, sys, re, datetime
from collections import Counter

def fail(msgs):
    for m in msgs: print("FAIL:", m)
    sys.exit(1)

def main(path, links=False):
    g = json.load(open(path))
    errs = []
    # 1. schema
    try:
        import jsonschema
        schema = json.load(open(path.replace("graph.json", "schema.json")))
        jsonschema.validate(g, schema)
    except ImportError:
        print("note: jsonschema not installed; skipping schema validation")
    except Exception as e:
        errs.append(f"schema: {e.message if hasattr(e,'message') else e}")
    N, E = g["nodes"], g["edges"]
    ids = [n["id"] for n in N]; idset = set(ids)
    # 2. uniqueness
    for k, v in Counter(ids).items():
        if v > 1: errs.append(f"duplicate id {k}")
    keys = [n["key"] for n in N]
    for k, v in Counter(keys).items():
        if v > 1: errs.append(f"duplicate key {k!r}")
    # 3. referential integrity
    for e in E + g.get("derived", {}).get("applies_at", []):
        for end in ("source", "target"):
            if e[end] not in idset: errs.append(f"edge {e} references missing node {e[end]}")
    # 4. spans and domains
    for n in N:
        if n["gate_from"] > n["gate_to"]: errs.append(f"{n['id']}: gate_from > gate_to")
        if n["kind"] == "milestone" and n["domain"] != "spine": errs.append(f"{n['id']}: milestone must be in domain spine")
        if n["kind"] == "consideration" and n["domain"] != "consideration": errs.append(f"{n['id']}: consideration domain")
        if n["kind"] not in ("milestone", "consideration") and n["domain"] in ("spine", "consideration"):
            errs.append(f"{n['id']}: document in non-document domain")
        if n.get("verification") in ("page", "search", "secondary") and not n.get("last_checked"):
            errs.append(f"{n['id']}: verified but no last_checked")
        if n.get("last_checked"):
            try: datetime.date.fromisoformat(n["last_checked"])
            except ValueError: errs.append(f"{n['id']}: bad last_checked")
        if n["status"] == "verify" and n["confidence"] != "low": errs.append(f"{n['id']}: status verify requires confidence low")
    # 5. groups
    gm = {}
    for grp in g["meta"].get("groups", []):
        for m in grp["members"]:
            if m not in idset: errs.append(f"group {grp['id']} member {m} missing")
            elif ids and [n for n in N if n["id"] == m][0]["domain"] != grp["domain"]:
                errs.append(f"group {grp['id']} member {m} in wrong domain")
            if m in gm: errs.append(f"{m} in two groups")
            gm[m] = grp["id"]
    for n in N:
        if n.get("group") != gm.get(n["id"]): errs.append(f"{n['id']}: group field {n.get('group')} != meta.groups {gm.get(n['id'])}")
    # 6. orphans (semantic + derived)
    deg = Counter()
    for e in E + g.get("derived", {}).get("applies_at", []):
        deg[e["source"]] += 1; deg[e["target"]] += 1
    for n in N:
        if deg[n["id"]] == 0: errs.append(f"{n['id']}: no relations")
    if errs: fail(errs)
    print(f"OK: {len(N)} nodes, {len(E)} edges, {len(g.get('derived',{}).get('applies_at',[]))} derived links; "
          f"verification {dict(Counter(n.get('verification') for n in N if n['kind'] not in ('milestone','consideration')))}")
    # 7. optional link check
    if links:
        import urllib.request, urllib.error
        report = []
        for n in N:
            u = n.get("url")
            if not u: continue
            try:
                req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "oligo-reqgraph-linkcheck/0.3"})
                with urllib.request.urlopen(req, timeout=20) as r: code = r.status
            except urllib.error.HTTPError as e: code = e.code
            except Exception as e: code = f"error: {e.__class__.__name__}"
            report.append({"id": n["id"], "url": u, "status": code, "checked": datetime.date.today().isoformat()})
            print(f"  {code}  {n['id']}")
        json.dump(report, open("link-report.json", "w"), indent=2)
        print("link-report.json written")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "graph.json", links="--links" in sys.argv)
