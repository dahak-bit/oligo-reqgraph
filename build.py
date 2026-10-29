#!/usr/bin/env python3
"""Builder for the open oligonucleotide regulatory-requirements graph.
Defines nodes + edges, validates referential integrity, emits JSON/CSV/schema.
URLs/identifiers marked confidence=medium are to be reconciled against the
verified inventory produced by the research pass.
"""
import json, csv, sys, os

OUT = os.path.dirname(os.path.abspath(__file__))  # package layout: outputs sit next to this script

# region: ICH | EU | US | JP | UK | INTL
# kind:   legal_act | guideline | pharmacopoeia | programme | milestone | consideration
# phase:  discovery | nonclinical | clinical | filing | lifecycle | cross_cutting
# modality tags: aso, sirna, aptamer, conjugate, lnp, all_oligo

N = []  # nodes
def node(id, label, kind, region, phase, ref=None, date=None, status="in_force",
         url=None, scope="", oligo="", confidence="high", modality=None):
    N.append(dict(id=id, label=label, kind=kind, region=region, phase=phase,
                  ref=ref, date=date, status=status, url=url, scope=scope,
                  oligo_note=oligo, confidence=confidence,
                  modality=modality or ["all_oligo"]))

# ---------- Milestones (the development spine) ----------
node("m-discovery","Discovery & lead optimisation","milestone","INTL","discovery",
     scope="Sequence/chemistry selection, in vitro screening, candidate nomination.",
     oligo="Hybridisation-based target ID; chemistry (PS, 2'-MOE, cEt, GalNAc) set here.")
node("m-nonclinical","IND/CTA-enabling nonclinical package","milestone","INTL","nonclinical",
     scope="Pivotal tox, safety pharmacology, genotox, TK before first-in-human.")
node("m-cta-ind","CTA / IND submission","milestone","INTL","clinical",
     scope="Authorisation to begin human trials.")
node("m-phase1","First-in-human / Phase 1","milestone","INTL","clinical",
     scope="Safety, tolerability, PK in humans.")
node("m-phase2","Phase 2","milestone","INTL","clinical",
     scope="Dose-finding, proof of concept.")
node("m-eop2","End-of-Phase-2 interaction","milestone","INTL","clinical",
     scope="Pivotal-design alignment; paediatric plan triggers cluster here.")
node("m-phase3","Phase 3 / pivotal","milestone","INTL","clinical",
     scope="Confirmatory efficacy & safety.")
node("m-filing","MAA / NDA / BLA submission","milestone","INTL","filing",
     scope="Marketing application dossier (CTD).")
node("m-approval","Marketing authorisation","milestone","INTL","filing",
     scope="Approval decision.")
node("m-lifecycle","Post-approval / pharmacovigilance","milestone","INTL","lifecycle",
     scope="Variations, PSUR/PBRER, paediatric & RMP commitments.")

MILES = ["m-discovery","m-nonclinical","m-cta-ind","m-phase1","m-phase2",
         "m-eop2","m-phase3","m-filing","m-approval","m-lifecycle"]

# ---------- ICH guidelines ----------
node("ich-m3r2","ICH M3(R2) — Nonclinical safety for clinical trials","guideline","ICH","nonclinical",
     ref="ICH M3(R2)", date="2009", url="https://www.ich.org/page/multidisciplinary-guidelines",
     scope="Timing/extent of nonclinical studies relative to clinical phases.",
     oligo="Default backbone; oligos not biotech products, so M3 (not S6) frames timing.")
node("ich-s1","ICH S1A/S1B(R1)/S1C(R2) — Carcinogenicity","guideline","ICH","nonclinical",
     ref="ICH S1", date="2022", url="https://www.ich.org/page/safety-guidelines",
     scope="Need for and design of carcinogenicity studies.")
node("ich-s2r1","ICH S2(R1) — Genotoxicity","guideline","ICH","nonclinical",
     ref="ICH S2(R1)", date="2011", url="https://www.ich.org/page/safety-guidelines",
     scope="Standard genotoxicity battery.",
     oligo="Standard battery often of limited value; hybridisation-based genotox is sequence-specific.")
node("ich-s3a","ICH S3A — Toxicokinetics","guideline","ICH","nonclinical",
     ref="ICH S3A", date="1994", url="https://www.ich.org/page/safety-guidelines",
     scope="Systemic exposure in toxicity studies.")
node("ich-s5r3","ICH S5(R3) — Reproductive & developmental toxicity","guideline","ICH","nonclinical",
     ref="ICH S5(R3)", date="2020", url="https://www.ich.org/page/safety-guidelines",
     scope="DART study design.")
node("ich-s6r1","ICH S6(R1) — Preclinical safety of biotech products","guideline","ICH","nonclinical",
     ref="ICH S6(R1)", date="2011", url="https://www.ich.org/page/safety-guidelines",
     scope="Applies to the antibody/protein component of conjugates, not the oligo itself.",
     oligo="Relevant only for antibody-oligonucleotide conjugates (AOC) / protein carriers.",
     modality=["conjugate"])
node("ich-s7a","ICH S7A — Safety pharmacology","guideline","ICH","nonclinical",
     ref="ICH S7A", date="2001", url="https://www.ich.org/page/safety-guidelines",
     scope="Core battery (CV, CNS, respiratory).")
node("ich-s7b","ICH S7B — Delayed ventricular repolarisation (QT)","guideline","ICH","nonclinical",
     ref="ICH S7B", date="2005", url="https://www.ich.org/page/safety-guidelines",
     scope="In vitro IKr and in vivo QT assessment.")
node("ich-s9","ICH S9 — Nonclinical evaluation for anticancer pharmaceuticals","guideline","ICH","nonclinical",
     ref="ICH S9", date="2009", url="https://www.ich.org/page/safety-guidelines",
     scope="Reduced nonclinical package for advanced-cancer indications.",
     oligo="Directly relevant for paediatric-oncology oligonucleotides.")
node("ich-s11","ICH S11 — Nonclinical safety for paediatric development","guideline","ICH","nonclinical",
     ref="ICH S11", date="2020", url="https://www.ich.org/page/safety-guidelines",
     scope="When/what juvenile animal studies are needed.",
     oligo="Central for paediatric oligonucleotide programmes.")
node("ich-q2r2","ICH Q2(R2) — Analytical procedure validation","guideline","ICH","cross_cutting",
     ref="ICH Q2(R2)", date="2023", url="https://www.ich.org/page/quality-guidelines",
     scope="Validation of analytical methods.")
node("ich-q3a","ICH Q3A(R2) — Impurities in new drug substances","guideline","ICH","cross_cutting",
     ref="ICH Q3A(R2)", date="2006", url="https://www.ich.org/page/quality-guidelines",
     scope="Reporting/identification/qualification thresholds for impurities.",
     oligo="Thresholds designed for small molecules; oligo process impurities (n±1, shortmers) need tailored justification.")
node("ich-q3d","ICH Q3D(R2) — Elemental impurities","guideline","ICH","cross_cutting",
     ref="ICH Q3D(R2)", date="2022", url="https://www.ich.org/page/quality-guidelines",
     scope="Elemental impurity limits.")
node("ich-q6a","ICH Q6A — Specifications","guideline","ICH","filing",
     ref="ICH Q6A", date="1999", url="https://www.ich.org/page/quality-guidelines",
     scope="Setting specifications for new drug substances/products.")
node("ich-q11","ICH Q11 — Development & manufacture of drug substances","guideline","ICH","cross_cutting",
     ref="ICH Q11", date="2012", url="https://www.ich.org/page/quality-guidelines",
     scope="CMC development incl. starting-material justification.",
     oligo="Starting-material concept contentious for synthetic oligos (amidites).")
node("ich-m7r2","ICH M7(R2) — Mutagenic impurities","guideline","ICH","cross_cutting",
     ref="ICH M7(R2)", date="2023", url="https://www.ich.org/page/multidisciplinary-guidelines",
     scope="Assessment/control of DNA-reactive impurities.")
node("ich-e6r3","ICH E6(R3) — Good Clinical Practice","guideline","ICH","clinical",
     ref="ICH E6(R3)", date="2025", url="https://www.ich.org/page/efficacy-guidelines",
     scope="GCP for trial conduct.")
node("ich-e8r1","ICH E8(R1) — General considerations for clinical studies","guideline","ICH","clinical",
     ref="ICH E8(R1)", date="2021", url="https://www.ich.org/page/efficacy-guidelines",
     scope="Quality-by-design of clinical programmes.")
node("ich-e11r1","ICH E11(R1) — Paediatric clinical investigation","guideline","ICH","clinical",
     ref="ICH E11(R1)", date="2017", url="https://www.ich.org/page/efficacy-guidelines",
     scope="Conduct of paediatric clinical trials.")
node("ich-e11a","ICH E11A — Paediatric extrapolation","guideline","ICH","clinical",
     ref="ICH E11A", date="2024", url="https://www.ich.org/page/efficacy-guidelines",
     scope="Framework for extrapolating adult data to children.",
     oligo="Key lever to shrink paediatric oligo programmes.")
node("ich-e17","ICH E17 — Multi-regional clinical trials","guideline","ICH","clinical",
     ref="ICH E17", date="2017", url="https://www.ich.org/page/efficacy-guidelines",
     scope="Design of MRCTs.")
node("ich-m4","ICH M4 — Common Technical Document (CTD)","guideline","ICH","filing",
     ref="ICH M4", date="2016", url="https://www.ich.org/page/multidisciplinary-guidelines",
     scope="Dossier structure for marketing applications.")

# ---------- Oligonucleotide-specific guidance ----------
node("fda-oligo-clinpharm","FDA — Clinical pharmacology considerations for oligonucleotide therapeutics","guideline","US","clinical",
     ref="Final guidance · Docket FDA-2022-D-0235", date="2024-06", status="in_force",
     url="https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-pharmacology-considerations-development-oligonucleotide-therapeutics",
     scope="QT, immunogenicity, hepatic/renal impairment, DDI for oligos.",
     oligo="The single most oligo-specific clin-pharm reference.", confidence="high")
node("fda-aso-ind-clin","FDA — IND submissions for individualised ASO products (clinical)","guideline","US","clinical",
     ref="FDA guidance", date="2021",
     url="https://www.fda.gov/regulatory-information/search-fda-guidance-documents",
     scope="Clinical/IND expectations for n-of-1 ASOs.",
     oligo="Pathway for bespoke ASOs (Milasen-type).", modality=["aso"], confidence="high")
node("fda-aso-nonclin","FDA — Nonclinical testing of individualised ASO products","guideline","US","nonclinical",
     ref="FDA guidance", date="2021",
     url="https://www.fda.gov/regulatory-information/search-fda-guidance-documents",
     scope="Minimal nonclinical package for n-of-1 ASOs (SDLT diseases).",
     oligo="Risk-based, abbreviated tox for individualised ASOs.", modality=["aso"], confidence="high")
node("fda-individualized-2026","FDA — Framework to accelerate individualised ASO therapies","guideline","US","cross_cutting",
     ref=None, date="2026", status="verify",
     url=None,
     scope="Reported 2026 framework for faster individualised-therapy pathways.",
     oligo="To be verified against FDA.gov before relying on it.", modality=["aso"], confidence="low")
node("ema-oligo-quality","EMA — Quality considerations for synthetic oligonucleotides","guideline","EU","cross_cutting",
     ref=None, date=None, status="verify",
     url="https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines",
     scope="EMA quality expectations for oligonucleotide actives.",
     oligo="Confirm current status (guideline vs concept paper) before citing.", confidence="low")
node("pheur-oligo","Ph. Eur. — Oligonucleotide general chapter / monographs","pharmacopoeia","EU","cross_cutting",
     ref=None, date=None, status="verify",
     url="https://www.edqm.eu/en/european-pharmacopoeia",
     scope="Compendial quality standards for oligonucleotides.", confidence="low")
node("usp-oligo","USP — Oligonucleotide quality chapters","pharmacopoeia","US","cross_cutting",
     ref=None, date=None, status="verify",
     url="https://www.usp.org/",
     scope="USP general chapters on oligonucleotide-based therapeutics.", confidence="low")
node("pmda-oligo","MHLW/PMDA — Points to consider for oligonucleotide therapeutics","guideline","JP","cross_cutting",
     ref=None, date="2020", status="verify",
     url="https://www.pmda.go.jp/english/",
     scope="Japan nonclinical/quality points-to-consider for oligos.", confidence="low")
node("oswg","OSWG — Oligonucleotide Safety Working Group recommendations","guideline","INTL","nonclinical",
     ref="OSWG white papers", date="2012-2019", status="guidance",
     url="https://www.nucleicacidtherapeutics.org/",
     scope="Consensus nonclinical safety recommendations (genotox, immunostim, class effects).",
     oligo="De-facto field standard; cited by regulators.", confidence="medium")

# ---------- Delivery / excipient ----------
node("fda-novel-excipient","FDA — Novel Excipient Review Pilot Program","programme","US","cross_cutting",
     ref=None, date="2021", status="programme",
     url="https://www.fda.gov/drugs/",
     scope="Pathway to review novel excipients (e.g. LNP lipids) ahead of an application.",
     oligo="Relevant for LNP-formulated siRNA/mRNA-adjacent delivery.", modality=["lnp"], confidence="medium")

# ---------- Paediatric framework ----------
node("eu-paed-reg","Regulation (EC) No 1901/2006 — Paediatric Regulation","legal_act","EU","cross_cutting",
     ref="Reg (EC) 1901/2006", date="2006",
     url="https://eur-lex.europa.eu/eli/reg/2006/1901/oj",
     scope="Mandatory PIP; rewards (SPC extension) and obligations.",
     oligo="Triggers a PIP for most new oligonucleotide actives.")
node("eu-pip-guidance","EMA — PIP format & content guidance","guideline","EU","clinical",
     ref="2014/C 338/01", date="2014",
     url="https://www.ema.europa.eu/en/human-regulatory-overview/research-development/paediatric-medicines-research-development",
     scope="How to compile a Paediatric Investigation Plan.")
node("eu-stepwise-pip","EMA — Stepwise PIP pilot","programme","EU","clinical",
     ref=None, date="2023-2025", status="programme",
     url="https://www.ema.europa.eu/en/human-regulatory-overview/research-development/paediatric-medicines-research-development/paediatric-investigation-plans",
     scope="Iterative PIP submission piloted by EMA.",
     oligo="Reduces early lock-in; useful for first-in-class oligos.", confidence="medium")
node("eu-pharma-package","EU pharmaceutical legislation reform (pharma package)","legal_act","EU","cross_cutting",
     ref=None, date="2026", status="pending",
     url="https://health.ec.europa.eu/medicinal-products/pharmaceutical-strategy-europe_en",
     scope="Reform moving PIP earlier, formalising iterative PIPs, changing orphan incentives.",
     oligo="Changes the timing of paediatric obligations; transition to ~2028.", confidence="medium")
node("us-prea","Pediatric Research Equity Act (PREA)","legal_act","US","cross_cutting",
     ref="PREA", date="2003",
     url="https://www.fda.gov/drugs/development-resources/pediatric-research-equity-act-prea",
     scope="Mandatory paediatric assessments for certain applications.")
node("us-bpca","Best Pharmaceuticals for Children Act (BPCA)","legal_act","US","cross_cutting",
     ref="BPCA", date="2002",
     url="https://www.fda.gov/drugs/development-resources/best-pharmaceuticals-children-act-bpca",
     scope="Voluntary paediatric studies with exclusivity incentive.")
node("us-race","RACE for Children Act (FDARA Title V)","legal_act","US","cross_cutting",
     ref="FDARA Title V", date="2017", status="in_force",
     url="https://www.fda.gov/about-fda/oncology-center-excellence/pediatric-oncology",
     scope="Molecularly targeted oncology drugs must study paediatric cancers when target is relevant.",
     oligo="Directly pulls paediatric-oncology oligos into mandatory study.")
node("fda-paed-target-list","FDA — Relevant molecular targets list (RACE)","guideline","US","discovery",
     ref="Relevant Molecular Target List (XLSX)", date=None,
     url="https://www.fda.gov/media/161463/download?attachment",
     scope="Targets that trigger / waive paediatric oncology studies under FDARA.",
     oligo="Check your oligo's target here at discovery; a listed target means paediatric study obligations.",
     confidence="high")
node("fda-ipsp","FDA — iPSP (initial Pediatric Study Plan) guidance","guideline","US","clinical",
     ref=None, date=None,
     url="https://www.fda.gov/regulatory-information/search-fda-guidance-documents",
     scope="Format/content and timing of the iPSP.", confidence="medium")

# ---------- Orphan / expedited ----------
node("eu-orphan-reg","Regulation (EC) No 141/2000 — Orphan Regulation","legal_act","EU","cross_cutting",
     ref="Reg (EC) 141/2000", date="2000",
     url="https://eur-lex.europa.eu/eli/reg/2000/141/oj",
     scope="Orphan designation criteria and 10-year market exclusivity.",
     oligo="Many oligo indications are rare → orphan-eligible.")
node("eu-prime","EMA — PRIME (PRIority MEdicines)","programme","EU","clinical",
     ref=None, date="2016", status="programme",
     url="https://www.ema.europa.eu/en/human-regulatory-overview/research-development/prime-priority-medicines",
     scope="Enhanced early support for high-unmet-need medicines.", confidence="medium")
node("eu-camp","Conditional marketing authorisation","programme","EU","filing",
     ref="Reg (EC) 507/2006", date="2006", status="programme",
     url="https://www.ema.europa.eu/en/human-regulatory-overview/marketing-authorisation/conditional-marketing-authorisation",
     scope="Approval on less complete data with specific obligations.")
node("eu-accelerated","EMA — Accelerated assessment","programme","EU","filing",
     ref=None, date=None, status="programme",
     url="https://www.ema.europa.eu/en/human-regulatory-overview/marketing-authorisation/accelerated-assessment",
     scope="Shortened review timetable for major-interest medicines.", confidence="medium")
node("us-oda","Orphan Drug Act","legal_act","US","cross_cutting",
     ref="ODA", date="1983",
     url="https://www.fda.gov/industry/medical-products-rare-diseases-and-conditions/designating-orphan-product-drugs-and-biological-products",
     scope="Orphan designation; 7-year exclusivity, tax credits.")
node("us-breakthrough","FDA — Breakthrough Therapy designation","programme","US","clinical",
     ref=None, date="2012", status="programme",
     url="https://www.fda.gov/patients/fast-track-breakthrough-therapy-accelerated-approval-priority-review",
     scope="Intensive guidance for substantial-improvement candidates.")
node("us-fast-track","FDA — Fast Track designation","programme","US","clinical",
     ref=None, date=None, status="programme",
     url="https://www.fda.gov/patients/fast-track-breakthrough-therapy-accelerated-approval-priority-review",
     scope="Rolling review, more frequent interaction.")
node("us-accel-approval","FDA — Accelerated Approval","programme","US","filing",
     ref=None, date=None, status="programme",
     url="https://www.fda.gov/patients/fast-track-breakthrough-therapy-accelerated-approval-priority-review",
     scope="Approval on surrogate endpoints with confirmatory obligation.")
node("us-rpd-prv","FDA — Rare Pediatric Disease Priority Review Voucher","programme","US","filing",
     ref=None, date=None, status="verify",
     url="https://www.fda.gov/industry/medical-products-rare-diseases-and-conditions/rare-pediatric-disease-designation-and-voucher-programs",
     scope="Transferable priority-review voucher (authority sunset status to verify).",
     oligo="High-value for rare paediatric oligo programmes; confirm current authorisation.", confidence="low")

# ---------- Trial authorisation ----------
node("eu-ctr","Regulation (EU) No 536/2014 — Clinical Trials Regulation","legal_act","EU","clinical",
     ref="Reg (EU) 536/2014", date="2022",
     url="https://eur-lex.europa.eu/eli/reg/2014/536/oj",
     scope="Single EU trial application via CTIS.")
node("us-ind","21 CFR Part 312 — Investigational New Drug","legal_act","US","clinical",
     ref="21 CFR 312", date=None,
     url="https://www.ecfr.gov/current/title-21/chapter-I/subchapter-D/part-312",
     scope="US IND requirements to begin clinical investigation.")
node("uk-mhra-cta","UK MHRA — Clinical Trial Authorisation / combined review","legal_act","UK","clinical",
     ref=None, date=None,
     url="https://www.gov.uk/guidance/clinical-trials-for-medicines-apply-for-authorisation-in-the-uk",
     scope="UK trial authorisation (MHRA + ethics combined review).", confidence="medium")

# ---------- Oligo-specific considerations ----------
node("c-hyb-offtarget","Hybridisation-dependent off-target effects","consideration","INTL","discovery",
     scope="Sequence-complementary off-target binding.",
     oligo="Bioinformatic + in vitro screening expected; shapes nonclinical design.")
node("c-immunostim","Immunostimulation (TLR / pro-inflammatory)","consideration","INTL","nonclinical",
     scope="Innate-immune activation (CpG/TLR9), complement.",
     oligo="Class effect; informs species selection and monitoring.")
node("c-hepatotox","Hepatotoxicity","consideration","INTL","nonclinical",
     scope="Dose-limiting liver findings for several chemistries.")
node("c-nephro","Renal accumulation / nephrotoxicity","consideration","INTL","nonclinical",
     scope="Proximal-tubule accumulation, especially PS backbones.")
node("c-thrombocytopenia","Thrombocytopenia (platelet class effect)","consideration","INTL","clinical",
     scope="Platelet declines seen with some 2'-MOE/PS ASOs.", modality=["aso"])
node("c-impurities","Oligonucleotide impurity control","consideration","INTL","cross_cutting",
     scope="n-1/n+1, shortmers, depurination, process-related impurities.",
     oligo="Small-molecule thresholds (Q3A) fit poorly; needs tailored strategy.")
node("c-delivery","Delivery & conjugation","consideration","INTL","discovery",
     scope="GalNAc, antibody conjugates (AOC), LNP, peptide carriers.",
     oligo="Carrier dictates which additional guidelines (S6, excipient) apply.")
node("c-cns-delivery","CNS delivery / intrathecal administration","consideration","INTL","nonclinical",
     scope="IT/ICV dosing, neurotoxicity, local tolerance.",
     oligo="Relevant for medulloblastoma/DMG oligos; adds local-tolerance studies.")
node("c-clinpharm","Clinical pharmacology profile","consideration","INTL","clinical",
     scope="Tissue PK, low CYP involvement, hepatic/renal impairment, QT, immunogenicity.")

# ===================== EDGES =====================
E = []
def edge(src, dst, rel):
    E.append(dict(source=src, target=dst, rel=rel))

# development spine: prerequisite_for chain
for a, b in zip(MILES, MILES[1:]):
    edge(a, b, "prerequisite_for")

# guideline -> milestone (governs_phase)
gov = {
 "m-nonclinical":["ich-m3r2","ich-s1","ich-s2r1","ich-s3a","ich-s5r3","ich-s6r1",
                  "ich-s7a","ich-s7b","ich-s9","ich-s11","oswg","fda-aso-nonclin","pmda-oligo"],
 "m-cta-ind":["ich-m3r2","eu-ctr","us-ind","uk-mhra-cta","fda-aso-ind-clin","ich-e8r1"],
 "m-phase1":["ich-e6r3","ich-e8r1","ich-e9","fda-oligo-clinpharm","c-clinpharm"],
 "m-phase2":["ich-e6r3","ich-e9","fda-oligo-clinpharm"],
 "m-eop2":["eu-pip-guidance","fda-ipsp","ich-e11a","eu-stepwise-pip"],
 "m-phase3":["ich-e6r3","ich-e9","ich-e17","ich-e11r1"],
 "m-filing":["ich-m4","ich-q6a","ich-q2r2","ich-q3a","ich-q3d","ich-m7r2","ich-q11",
             "eu-camp","eu-accelerated","us-accel-approval","us-rpd-prv"],
 "m-approval":["eu-paed-reg","us-prea","us-race"],
 "m-lifecycle":["eu-paed-reg"],
 "m-discovery":["c-hyb-offtarget","c-delivery","fda-paed-target-list"],
}
# ich-e9 node missing; add it
node("ich-e9","ICH E9 — Statistical principles for clinical trials","guideline","ICH","clinical",
     ref="ICH E9", date="1998", url="https://www.ich.org/page/efficacy-guidelines",
     scope="Statistical design and analysis.")
KIND = {}
def _kind(i):
    if not KIND:
        for n in N: KIND[n["id"]] = n["kind"]
    return KIND.get(i)
for mile, gs in gov.items():
    for g in gs:
        edge(g, mile, "informs" if _kind(g) == "consideration" else "governs_phase")

# connect otherwise-orphaned nodes
edge("pheur-oligo","c-impurities","addresses")
edge("usp-oligo","c-impurities","addresses")
edge("ema-oligo-quality","c-impurities","addresses")
edge("ema-oligo-quality","m-filing","governs_phase")
edge("pheur-oligo","m-filing","governs_phase")
edge("usp-oligo","m-filing","governs_phase")
edge("fda-individualized-2026","m-cta-ind","governs_phase")
edge("fda-individualized-2026","fda-aso-ind-clin","references")
edge("eu-pharma-package","eu-orphan-reg","amends")
edge("us-bpca","m-phase3","supports")
edge("c-immunostim","m-nonclinical","informs")
edge("c-thrombocytopenia","m-phase1","informs")
edge("c-impurities","m-filing","informs")

# programmes incentivise / attach to milestones
edge("eu-prime","m-phase1","supports")
edge("eu-orphan-reg","m-discovery","supports")
edge("us-oda","m-discovery","supports")
edge("us-breakthrough","m-phase2","supports")
edge("us-fast-track","m-cta-ind","supports")
edge("eu-pharma-package","eu-paed-reg","amends")

# applies_to: considerations <-> guidelines
edge("oswg","c-immunostim","addresses")
edge("oswg","c-hyb-offtarget","addresses")
edge("fda-oligo-clinpharm","c-clinpharm","addresses")
edge("fda-oligo-clinpharm","c-thrombocytopenia","addresses")
edge("ich-q3a","c-impurities","addresses")
edge("ich-q11","c-impurities","addresses")
edge("ich-q6a","c-impurities","addresses")
edge("ich-s6r1","c-delivery","addresses")
edge("fda-novel-excipient","c-delivery","addresses")
edge("c-cns-delivery","m-nonclinical","informs")
edge("c-delivery","m-discovery","informs")
edge("c-hepatotox","m-nonclinical","informs")
edge("c-nephro","m-nonclinical","informs")

# paediatric cross-refs
edge("ich-e11a","eu-pip-guidance","references")
edge("ich-e11a","fda-ipsp","references")
edge("ich-s11","m-nonclinical","governs_phase")
edge("us-race","fda-paed-target-list","references")
edge("eu-paed-reg","eu-pip-guidance","references")
edge("us-prea","fda-ipsp","references")
edge("us-race","us-rpd-prv","references")

# oncology package
edge("ich-s9","m-nonclinical","governs_phase")

# ===================== v0.2 RECONCILIATION =====================
# Pulls verified fields from the research inventory (inventory/inventory.json).
# Mapping: graph node id -> inventory id. Fields taken: ref (document_number),
# date, status_note (full status text), confidence, verification provenance, url.
INV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source-inventory.json")
INV = {e["id"]: e for e in json.load(open(INV_PATH))}

def _prov(v):
    v = (v or "").strip()
    if v.startswith("V-PAGE") or v.startswith("Negative result") or v.startswith("USP oligonucleotide") or "V-PAGE" in v.split(";")[0]:
        return "page"
    if v.startswith("V-SEARCH") or v.startswith("DOI URL V-SEARCH") or v.startswith("PubMed ID V-SEARCH") \
       or v.startswith("Title") or v.startswith("PDF URL V-SEARCH") or v.startswith("URL V-SEARCH") \
       or v.startswith("Step 2 PDF V-SEARCH") or v.startswith("EMA Step 2b PDF V-SEARCH") \
       or v.startswith("Q&A URL V-SEARCH") or v.startswith("Volume 10 page V-SEARCH") or v.startswith("EMA page V-PAGE"):
        return "search"
    return "knowledge"

def _status_short(s):
    s = (s or "").lower()
    if s.startswith("draft"): return "draft"
    if s.startswith("unknown"): return "verify"
    if s.startswith("pilot"): return "programme"
    if s.startswith("published white paper"): return "guidance"
    if s.startswith("adopted by council"): return "pending"
    return "in_force"

NBY = {n["id"]: n for n in N}
KEEP_URL = {"fda-oligo-clinpharm", "fda-paed-target-list", "eu-prime"}  # better landing pages already verified

MAP = {
 "ich-m3r2":"ICH-M3R2","ich-s2r1":"ICH-S2R1","ich-s3a":"ICH-S3A","ich-s5r3":"ICH-S5R3",
 "ich-s6r1":"ICH-S6R1","ich-s7a":"ICH-S7A","ich-s7b":"ICH-S7B","ich-s9":"ICH-S9","ich-s11":"ICH-S11",
 "ich-q2r2":"ICH-Q2R2","ich-q3a":"ICH-Q3AR2","ich-q3d":"ICH-Q3DR2","ich-q6a":"ICH-Q6A","ich-q11":"ICH-Q11",
 "ich-m7r2":"ICH-M7R2","ich-e6r3":"ICH-E6R3","ich-e8r1":"ICH-E8R1","ich-e9":"ICH-E9",
 "ich-e11r1":"ICH-E11R1","ich-e11a":"ICH-E11A","ich-e17":"ICH-E17","ich-m4":"ICH-M4",
 "fda-oligo-clinpharm":"FDA-OLIGO-CLINPHARM","fda-aso-ind-clin":"FDA-iASO-CLIN","fda-aso-nonclin":"FDA-iASO-NONCLIN",
 "fda-individualized-2026":"FDA-PLAUSIBLE-MECH","ema-oligo-quality":"EMA-OLIGO-GL",
 "pheur-oligo":"PHEUR-OLIGO","usp-oligo":"USP-OLIGO","pmda-oligo":"JP-OLIGO-NONCLIN","oswg":"OSWG-ADME-2023",
 "fda-novel-excipient":"FDA-NOVEL-EXCIPIENT-PILOT","eu-paed-reg":"EU-REG-1901-2006","eu-pip-guidance":"EU-PIP-FORMAT-GL",
 "eu-stepwise-pip":"EMA-SPIP-REPORT","eu-pharma-package":"EU-PHARMA-PACKAGE-2026","us-prea":"US-PREA","us-bpca":"US-BPCA",
 "us-race":"US-RACE-ACT","fda-paed-target-list":"FDA-PED-MOL-TARGET-LIST","fda-ipsp":"FDA-iPSP-GL",
 "eu-orphan-reg":"EU-REG-141-2000","eu-prime":"EMA-PRIME","eu-camp":"EU-REG-507-2006","eu-accelerated":"EMA-ACCEL-ASSESS-GL",
 "us-oda":"US-ODA","us-breakthrough":"FDA-EXPEDITED-2014","us-fast-track":"FDA-EXPEDITED-2014",
 "us-accel-approval":"FDA-AA-DRAFT-2024","us-rpd-prv":"US-RPD-PRV","eu-ctr":"EU-CTR-536-2014",
 "us-ind":"US-21CFR312","uk-mhra-cta":"UK-MHRA-CTA-GUIDANCE",
}
for nid, iid in MAP.items():
    n, e = NBY[nid], INV[iid]
    if e.get("document_number"): n["ref"] = e["document_number"]
    if e.get("date"): n["date"] = e["date"]
    n["status_note"] = e.get("status")
    n["confidence"] = e.get("confidence") or n["confidence"]
    n["verification"] = _prov(e.get("verification"))
    if nid not in KEEP_URL and e.get("official_url"): n["url"] = e["official_url"]
    st = _status_short(e.get("status"))
    if n["kind"] == "programme" and st == "in_force": st = "programme"
    n["status"] = st

def upd(nid, **kw): NBY[nid].update(kw)

# --- corrections where the inventory changes what the node *is* ---
upd("fda-individualized-2026",
    label="FDA — Plausible Mechanism framework for individualised therapies",
    scope="Evidence framework for individualised genome-editing and RNA therapies (explicitly ASOs): single externally controlled investigation with natural-history control, platform protocols, traditional or accelerated approval.",
    oligo_note="The 2026 FDA pathway for bespoke oligonucleotides; builds on the three 2021 individualised-ASO drafts. Docket number not stated in the PDF.")
upd("ema-oligo-quality",
    label="EMA — Guideline on development and manufacture of oligonucleotides (draft)",
    scope="First EU quality guideline specific to synthetic oligonucleotides: starting materials, impurities, specifications, manufacturing process.",
    oligo_note="Consultation closed Jan 2025; adoption not yet announced. Preceded by concept paper EMA/CHMP/QWP/735423/2022.")
upd("pheur-oligo",
    label="Ph. Eur. — texts applicable to synthetic oligonucleotides",
    scope="No dedicated oligonucleotide chapter found; general monograph 2034 'Substances for pharmaceutical use' and general methods apply.",
    oligo_note="No oligo-specific purity limits in Ph. Eur.; rely on the EMA draft guideline. Check Pharmeuropa before citing.")
upd("usp-oligo",
    label="USP — oligonucleotide standards programme",
    scope="Phosphoramidite Reference Standards and an oligonucleotide standards programme; chapters <1125>–<1130> cover nucleic-acid analytics, not therapeutic oligo quality.",
    oligo_note="No dedicated general chapter number verifiable; monitor Pharmacopeial Forum.")
upd("pmda-oligo",
    label="MHLW/PMDA — Guideline for preclinical safety assessment of oligonucleotide therapeutics",
    scope="Japanese nonclinical safety guideline specific to oligonucleotides.",
    oligo_note="One of only two binding-style national oligo-specific nonclinical texts worldwide (with the FDA 2024 draft).")
upd("oswg",
    label="OSWG — Oligonucleotide Safety Working Group white papers",
    ref="Nucleic Acid Ther 2013–2023; Nat Biotechnol 2012",
    date="2012–2023",
    scope="Consensus papers: off-target hybridisation (2012), exaggerated pharmacology (2013), safety pharmacology and reprotox (2014), genotoxicity (2016), formulated oligos (2017), ADME (2023).",
    oligo_note="Non-binding but the de-facto field standard; regulators cite them. Linked: 2023 ADME paper.")
upd("us-rpd-prv",
    scope="Transferable priority-review voucher for rare paediatric disease approvals.",
    oligo_note="Lapsed Dec 2024, reauthorised by Pub. L. 119-75 (3 Feb 2026) with designations through 30 Sep 2029. High value for rare paediatric oligo programmes.")
upd("eu-pharma-package",
    scope="Reform replacing Directive 2001/83/EC and Reg 726/2004, moving PIPs earlier, formalising iterative PIPs, changing orphan incentives.",
    oligo_note="Council adopted 28 Sep 2026; Parliament adoption and OJ publication pending. Applies ~24 months after entry into force.")
upd("eu-stepwise-pip", label="EMA — Stepwise PIP (pilot report & routine use)",
    oligo_note="Pilot 2023–2025 reviewed in Feb 2026; EMA plans to integrate stepwise PIPs into routine practice.")
upd("fda-paed-target-list", ref="Docket FDA-2018-N-3633 · Relevant/Non-Relevant lists", date="2026-02-17", verification="page")
upd("fda-aso-ind-clin", label="FDA — IND submissions for individualised ASO products (clinical, draft)")
upd("fda-aso-nonclin", label="FDA — Nonclinical testing of individualised ASO products (draft)")
upd("ich-e9", label="ICH E9 / E9(R1) — Statistical principles & estimands")
upd("ich-s1", ref="ICH S1A · S1B(R1) · S1C(R2)", date="1995–2022",
    url=INV["ICH-S1BR1"]["official_url"], status_note="in force (Step 4/5)", verification="search")
upd("uk-mhra-cta", label="UK — Clinical trial authorisation (SI 2004/1031 as amended by SI 2025/538)",
    scope="UK trials regime; substantially amended regulations in force from 28 Apr 2026.")
upd("us-accel-approval", oligo_note="Dec 2024 draft guidance would replace the accelerated-approval section of the 2014 expedited-programs guidance.")
upd("eu-camp", url=INV["EMA-CMA-GL"]["official_url"])

# --- new nodes from the inventory ---
def from_inv(nid, iid, label, kind, region, phase, scope=None, oligo="", modality=None, short=None):
    e = INV[iid]
    node(nid, label, kind, region, phase, ref=e.get("document_number"), date=e.get("date"),
         status=_status_short(e.get("status")) if kind!="programme" else "programme",
         url=e.get("official_url"), scope=scope or e.get("scope") or "", oligo=oligo or e.get("oligo_applicability") or "",
         confidence=e.get("confidence") or "medium", modality=modality)
    N[-1]["status_note"] = e.get("status"); N[-1]["verification"] = _prov(e.get("verification"))
    if short: SHORT_EXTRA[nid] = short
SHORT_EXTRA = {}

from_inv("fda-oligo-nonclin","FDA-OLIGO-NONCLIN","FDA — Nonclinical safety assessment of oligonucleotide-based therapeutics (draft)",
         "guideline","US","nonclinical",
         scope="FDA's first general nonclinical guidance specific to oligonucleotides: species selection, off-target, immunostimulation, class toxicities, study design.",
         oligo="The central US nonclinical reference for any oligo IND; draft since Nov 2024.", short="Oligo nonclinical (draft)")
from_inv("fda-aso-admin","FDA-iASO-ADMIN","FDA — IND submissions for individualised ASO products (administrative, draft)",
         "guideline","US","clinical", modality=["aso"], short="iASO administrative (draft)")
from_inv("jp-oligo-quality","JP-OLIGO-QUAL","MHLW/PMDA — Points to consider for quality of oligonucleotide therapeutics",
         "guideline","JP","cross_cutting", short="JP oligo quality")
from_inv("fda-fdara-pedonc","FDA-FDARA-PED-ONC-GL","FDA — FDARA guidance on paediatric studies of molecularly targeted oncology drugs",
         "guideline","US","clinical",
         oligo="Operational rules for RACE Act obligations; decisive for paediatric-oncology oligos.", short="FDARA paed-onc guidance")
from_inv("ema-fih","EMA-FIH-GL","EMA — First-in-human and early clinical trials: risk identification & mitigation",
         "guideline","EU","clinical", short="EMA first-in-human")
from_inv("ema-impd-q","EMA-IMPD-QUALITY-GL","EMA — Quality documentation for investigational medicinal products (IMPD-Q)",
         "guideline","EU","clinical", short="EMA IMPD quality")
from_inv("fda-adc-clinpharm","FDA-ADC-CLINPHARM","FDA — Clinical pharmacology considerations for antibody-drug conjugates",
         "guideline","US","clinical",
         oligo="Closest FDA analogue for antibody–oligonucleotide conjugates (AOC).", modality=["conjugate"], short="ADC clin-pharm")
from_inv("ema-mab-gl","EMA-MAB-GL","EMA — Monoclonal antibodies: development, production, characterisation, specification",
         "guideline","EU","cross_cutting",
         oligo="Applies to the antibody component of AOCs.", modality=["conjugate"], short="EMA mAb quality")
from_inv("fda-nanomaterials","FDA-NANOMATERIALS","FDA — Drug products containing nanomaterials",
         "guideline","US","cross_cutting", oligo="Applies to LNP-formulated siRNA.", modality=["lnp"], short="Nanomaterials")
from_inv("fda-liposome","FDA-LIPOSOME","FDA — Liposome drug products: CMC, PK and labelling",
         "guideline","US","cross_cutting", oligo="Reference point for lipid-based oligo formulations.", modality=["lnp"], short="Liposome products")
from_inv("ich-q14","ICH-Q14","ICH Q14 — Analytical procedure development","guideline","ICH","cross_cutting")
from_inv("ich-m10","ICH-M10","ICH M10 — Bioanalytical method validation","guideline","ICH","clinical",
         oligo="Governs oligo PK assays (hybridisation ELISA, LC-MS); ligand-binding vs chromatographic choice matters.")
from_inv("ich-q3c","ICH-Q3CR9","ICH Q3C(R9) — Residual solvents","guideline","ICH","cross_cutting",
         oligo="Oligo solid-phase synthesis uses large solvent volumes (e.g. acetonitrile); Q3C limits apply directly.")
from_inv("ich-e14s7b","ICH-E14S7B-QA","ICH E14/S7B Q&As — QT/QTc integrated risk assessment","guideline","ICH","clinical",
         oligo="Basis for the QT approach in FDA's oligo clin-pharm guidance.", short="E14/S7B Q&A")
from_inv("ich-q1","ICH-Q1-NEW","ICH Q1 — Stability testing (consolidated, draft)","guideline","ICH","cross_cutting",
         scope="Consolidation of Q1A–F into one stability guideline; Q1A(R2) remains in force until adoption.")
from_inv("fda-rare-dis","FDA-RARE-DIS-GL-2023","FDA — Rare diseases: considerations for drug development","guideline","US","clinical",
         short="Rare-disease guidance")
from_inv("fda-rdep","FDA-RDEP-2025","FDA — Rare Disease Evidence Principles (RDEP)","programme","US","filing",
         oligo="Evidence pathway for very small populations; relevant to ultra-rare and n-of-few oligo programmes.", short="RDEP")
from_inv("eu-reg-726","EU-REG-726-2004","Regulation (EC) No 726/2004 — Centralised procedure","legal_act","EU","filing",
         scope="Centralised authorisation; legal basis for accelerated assessment (Art 14(9)) and conditional MA (Art 14-a).")
from_inv("fda-sponsor-inv-ind","FDA-SPONSOR-INVESTIGATOR-IND","FDA — INDs prepared by sponsor-investigators (draft)",
         "guideline","US","clinical",
         oligo="Route for academic investigators running their own oligo IND (incl. n-of-1 ASOs).", short="Sponsor-investigator IND")

# --- edges for new nodes ---
for g, m in [("fda-oligo-nonclin","m-nonclinical"),("fda-aso-admin","m-cta-ind"),("jp-oligo-quality","m-filing"),
             ("fda-fdara-pedonc","m-eop2"),("ema-fih","m-phase1"),("ema-fih","m-cta-ind"),("ema-impd-q","m-cta-ind"),
             ("fda-adc-clinpharm","m-phase1"),("ema-mab-gl","m-filing"),("fda-nanomaterials","m-filing"),
             ("fda-liposome","m-filing"),("ich-q14","m-filing"),("ich-m10","m-phase1"),("ich-q3c","m-filing"),
             ("ich-e14s7b","m-phase1"),("ich-q1","m-filing"),("fda-rare-dis","m-phase2"),("eu-reg-726","m-filing"),
             ("fda-sponsor-inv-ind","m-cta-ind")]:
    edge(g, m, "governs_phase")
for c in ["c-immunostim","c-hyb-offtarget","c-hepatotox","c-nephro","c-thrombocytopenia"]:
    edge("fda-oligo-nonclin", c, "addresses")
for c in ["c-hyb-offtarget","c-immunostim"]:
    edge("pmda-oligo", c, "addresses")
edge("fda-oligo-nonclin","oswg","references")
edge("jp-oligo-quality","c-impurities","addresses")
edge("ema-impd-q","c-impurities","addresses")
edge("ich-q3c","c-impurities","addresses")
edge("fda-adc-clinpharm","c-delivery","addresses")
edge("ema-mab-gl","c-delivery","addresses")
edge("fda-nanomaterials","c-delivery","addresses")
edge("fda-liposome","c-delivery","addresses")
edge("ich-m10","c-clinpharm","addresses")
edge("ich-e14s7b","c-clinpharm","addresses")
edge("ich-e14s7b","ich-s7b","references")
edge("fda-oligo-clinpharm","ich-e14s7b","references")
edge("ich-q14","ich-q2r2","references")
edge("fda-fdara-pedonc","us-race","references")
edge("fda-fdara-pedonc","fda-paed-target-list","references")
edge("fda-individualized-2026","fda-aso-nonclin","references")
edge("fda-individualized-2026","fda-aso-admin","references")
edge("fda-rdep","m-filing","supports")
edge("fda-rare-dis","us-oda","references")
edge("eu-camp","eu-reg-726","references")
edge("eu-accelerated","eu-reg-726","references")
edge("eu-pharma-package","eu-reg-726","amends")
edge("fda-sponsor-inv-ind","us-ind","references")

# ===================== v0.3 DATA MODEL =====================
# domain · gate_from/gate_to (8-gate scale) · key · group · triggers · last_checked · supersedes edges
GATES=[("discovery","Discovery"),("nonclinical","Nonclinical"),("cta","CTA / IND"),("p1","Phase 1"),
       ("p2","Phase 2"),("p3","Phase 3"),("filing","Filing & approval"),("post","Post-approval")]
DOMAINS=[("quality","Quality & CMC"),("nonclin","Nonclinical safety"),("clinical","Clinical & pharmacology"),
         ("paed","Paediatric"),("rare","Rare, expedited & individualised"),("auth","Trial & marketing authorisation"),
         ("spine","Development gate"),("consideration","Oligonucleotide consideration")]
CHECK_DATE="2026-10-28"

# --- Phase B: new documents (verified 2026-10-28) ---
node("cns-goyenvalle-2023","Goyenvalle et al. — Considerations in the preclinical safety assessment of ASOs (incl. CNS local delivery)",
     "guideline","INTL","nonclinical",ref="Nucleic Acid Ther 2023;33(1) · doi:10.1089/nat.2022.0061",date="2023",status="guidance",
     url="https://journals.sagepub.com/doi/full/10.1089/nat.2022.0061",
     scope="Review with a dedicated section on toxicities associated with CNS local delivery: intrathecal and intracerebroventricular dosing, CSF and brain exposure, rodent neurotoxicity.",
     oligo="Closest thing to a field standard for IT/ICV ASO nonclinical design; non-binding.",confidence="high")
node("cns-berman-booty-2023","Toxicologic Pathology Forum — Procedure-related effects of direct CNS delivery of oligonucleotides (rodent, dog, NHP)",
     "guideline","INTL","nonclinical",ref="Toxicol Pathol 2023;51(6):375–389 · doi:10.1177/01926233231218953",date="2023",status="guidance",
     url="https://journals.sagepub.com/doi/10.1177/01926233231218953",
     scope="Interpretation of functional and histopathologic findings in vehicle-dosed control animals after ICV (mouse) and IT (rat, dog, NHP) oligonucleotide administration.",
     oligo="Separates procedure artefacts from test-article neurotoxicity in IT studies — the question regulators ask first.",confidence="high")
node("cns-ijt-2020","Procedure-related spinal cord lesions after lumbar intrathecal bolus of oligonucleotides in cynomolgus monkeys",
     "guideline","INTL","nonclinical",ref="Int J Toxicol 2020;39(6):510–517 · PMID 32856507",date="2020",status="guidance",
     url="https://pubmed.ncbi.nlm.nih.gov/32856507/",
     scope="Diagnosing procedure-related spinal cord lesions in NHP IT bolus studies so that the maximum tolerated dose is not misattributed.",
     oligo="NHP IT methodology reference.",confidence="medium")
node("cns-toxpath-nfd","Toxicologic Pathology Forum — Adverse versus non-adverse nerve fibre degeneration in intrathecal oligonucleotide studies",
     "guideline","INTL","nonclinical",ref=None,date=None,status="guidance",url=None,
     scope="Opinion on classifying nerve fibre degeneration in nonclinical toxicity studies of oligonucleotides delivered into the intrathecal space.",
     oligo="Lead from a library record; DOI and year still to be confirmed before citing.",confidence="medium")
node("fda-dili-2009","FDA — Drug-induced liver injury: premarketing clinical evaluation","guideline","US","clinical",
     ref="Docket FDA-2008-D-0128",date="2009-07",status="in_force",
     url="https://www.fda.gov/regulatory-information/search-fda-guidance-documents/drug-induced-liver-injury-premarketing-clinical-evaluation",
     scope="How to detect, evaluate and report hepatotoxicity signals in clinical development (Hy's law).",
     oligo="The clinical counterpart to the hepatotoxicity class effect; applies to 2'-MOE/cEt programmes in particular.",confidence="high")
node("fda-renal-pk-2024","FDA — Pharmacokinetics in patients with impaired renal function","guideline","US","clinical",
     ref="Docket FDA-2010-D-0133",date="2024-03",status="in_force",
     url="https://www.fda.gov/regulatory-information/search-fda-guidance-documents/pharmacokinetics-patients-impaired-renal-function-study-design-data-analysis-and-impact-dosing-and",
     scope="Design and analysis of renal-impairment PK studies and dosing impact.",
     oligo="Relevant because PS oligonucleotides accumulate in proximal tubule and are renally cleared; cross-referenced by the FDA oligo clin-pharm guidance.",confidence="high")
# superseded / revision nodes for supersedes edges
node("ich-q1ar2","ICH Q1A(R2) — Stability testing of new drug substances and products","guideline","ICH","cross_cutting",
     ref="ICH Q1A(R2)",date="2003-02-06",status="in_force",url="https://database.ich.org/sites/default/files/Q1A_R2_Guideline.pdf",
     scope="Stability study design; in force until the consolidated Q1 is adopted.",confidence="high")
node("ich-e9r1","ICH E9(R1) — Estimands and sensitivity analysis (addendum)","guideline","ICH","clinical",
     ref="ICH E9(R1)",date="2019-11-20",status="in_force",url="https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf",
     scope="Estimand framework; addendum to E9.",confidence="high")
node("ich-e6r2","ICH E6(R2) — Good Clinical Practice (superseded)","guideline","ICH","clinical",
     ref="ICH E6(R2)",date="2016-11-09",status="superseded",url="https://database.ich.org/sites/default/files/E6_R2_Addendum.pdf",
     scope="Previous GCP text; replaced by E6(R3).",confidence="high")
node("fda-expedited-2014","FDA — Expedited programs for serious conditions (drugs and biologics)","guideline","US","clinical",
     ref="Final guidance (May 2014)",date="2014-05",status="in_force",url="https://www.fda.gov/media/86377/download",
     scope="Fast Track, Breakthrough, Accelerated Approval, Priority Review in one guidance.",
     oligo="Accelerated-approval section to be replaced by the Dec 2024 draft once finalised.",confidence="high")
NBY={n["id"]:n for n in N}
for i,v in {"cns-goyenvalle-2023":"page","cns-berman-booty-2023":"page","cns-ijt-2020":"search","cns-toxpath-nfd":"search",
            "fda-dili-2009":"page","fda-renal-pk-2024":"page","ich-q1ar2":"search","ich-e9r1":"search","ich-e6r2":"search","fda-expedited-2014":"search"}.items():
    NBY[i]["verification"]=v; NBY[i]["status_note"]=NBY[i].get("status_note") or NBY[i]["status"]
NBY["ich-e9"]["label"]="ICH E9 — Statistical principles for clinical trials"

# --- Phase B: statutes re-verified on primary sources (govinfo) ---
upd("us-prea",ref="Pub. L. 108-155 · FD&C Act §505B · 21 U.S.C. 355c",date="2003-12-03",verification="page",
    url="https://www.govinfo.gov/content/pkg/PLAW-108publ155/html/PLAW-108publ155.htm",status_note="in force (as amended by FDAAA 2007, FDASIA 2012, FDARA 2017)")
upd("us-bpca",ref="Pub. L. 107-109 · FD&C Act §505A · 21 U.S.C. 355a",date="2002-01-04",verification="page",
    url="https://www.govinfo.gov/content/pkg/PLAW-107publ109/html/PLAW-107publ109.htm",status_note="in force")
upd("us-race",ref="Pub. L. 115-52 (FDARA 2017) §504",date="2017-08-18",verification="page",
    url="https://www.govinfo.gov/content/pkg/PLAW-115publ52/html/PLAW-115publ52.htm",status_note="in force (applies to applications submitted on/after 2020-08-18)")
upd("us-oda",ref="Pub. L. 97-414 · FD&C Act §526 · 21 U.S.C. 360bb",date="1983-01-04",verification="page",
    url="https://www.govinfo.gov/content/pkg/USCODE-2021-title21/pdf/USCODE-2021-title21-chap9-subchapV-partB-sec360bb.pdf",status_note="in force")
upd("us-rpd-prv",ref="FD&C Act §529 · 21 U.S.C. 360ff · reauthorised by Pub. L. 119-75 (CAA 2026, §§6601–6605)",date="2026-02-03",verification="secondary",
    status_note="in force — designations authorised through 2029-09-30 (programme had lapsed 2024-12-20); primary text in the Consolidated Appropriations Act, 2026")
upd("pheur-oligo",status_note="negative result re-confirmed 2026-10-28: no oligonucleotide item in EDQM Ph. Eur. newsroom (latest item 2025-04-14) or Pharmeuropa 38.2 (2026-04-02); general monograph 2034 applies",verification="page")
# knowledge-only entries upgraded 2026-10-28
upd("eu-pip-guidance",verification="search",
    status_note="in force since 2014-09-30 (EMA news of that date confirms OJ publication of the revised Commission guideline; EUR-Lex text not opened in this check)")
upd("ich-q14",ref="ICH Q14 · EMA/CHMP/ICH/195040/2022 (Step 5, Rev. 1)",date="2023-11-01",verification="page",
    url="https://www.ema.europa.eu/en/documents/scientific-guideline/ich-q14-guideline-analytical-procedure-development-step-5-revision-1_en.pdf",
    status_note="in force (EU effective 2024-06-14)")
upd("ich-m10",verification="search",url="https://www.fda.gov/media/179296/download",status_note="in force (Step 4 2022-05-24; FDA copy updated Jan 2025)")
upd("fda-sponsor-inv-ind",ref="Docket FDA-2015-D-1484",date="2015-05",verification="page",
    url="https://www.govinfo.gov/content/pkg/FR-2015-05-15/html/2015-11685.htm",status_note="draft (notice of availability 80 FR, 2015-05-15); still draft")

# --- Phase B continued (28 Oct 2026, second pass) ---
upd("cns-ijt-2020",label="Korte et al. — Procedure-related spinal cord lesions after lumbar intrathecal bolus of oligonucleotides in cynomolgus monkeys",
    ref="Int J Toxicol 2020;39(6):510–517 · doi:10.1177/1091581820951098 · PMID 32856507",url="https://doi.org/10.1177/1091581820951098",
    verification="secondary",status_note="published (library record opened; full text not read)",confidence="high")
upd("usp-oligo",status_note="negative result re-confirmed 2026-10-28: USP oligonucleotide standards page lists phosphoramidite Reference Standards and education only; the Peptides & Oligonucleotides Expert Committee work plan names no oligonucleotide general chapter",
    verification="page")
upd("us-rpd-prv",url="https://www.govinfo.gov/content/pkg/PLAW-119publ75/html/PLAW-119publ75.htm",
    status_note="in force — designations authorised through 2029-09-30 (programme had lapsed 2024-12-20). Pub. L. 119-75 confirmed on govinfo (3 Feb 2026); the reauthorising sections (CAA 2026 §§6601–6605, Division J) were not reached in this check — dates rest on a law-firm summary")
# designation spans reviewed: strategy for accelerated assessment / conditional MA starts with the pivotal programme, formal request pre-submission
node("ema-ddc-gl","EMA — Quality documentation for medicinal products used with a medical device","guideline","EU","cross_cutting",
     ref="EMA/CHMP/QWP/BWP/259165/2019",date="2021-07-22",status="in_force",
     url="https://www.ema.europa.eu/en/documents/scientific-guideline/guideline-quality-documentation-medicinal-products-when-used-medical-device-first-version_en.pdf",
     scope="Quality documentation for integral, co-packaged and referenced drug–device combinations; in effect since 2022-01-01.",
     oligo="Applies where an oligonucleotide is given through a named device (implanted reservoir, port, pump) or supplied with one; not to plain lumbar puncture.",
     confidence="high",modality=["all_oligo"])
node("us-21cfr4","21 CFR Part 4 — Regulation of combination products","legal_act","US","cross_cutting",
     ref="21 CFR 4 (Subpart A cGMP; Subpart B postmarketing safety reporting)",date=None,status="in_force",
     url="https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-4",
     scope="cGMP and postmarketing safety reporting for drug–device combination products.",
     oligo="US counterpart for device-delivered oligonucleotides (ICV reservoirs, implanted pumps).",confidence="high")
NBY={n["id"]:n for n in N}
NBY["ema-ddc-gl"]["verification"]="page"; NBY["ema-ddc-gl"]["status_note"]="in force (adopted 2021-07-22, effective 2022-01-01)"
NBY["us-21cfr4"]["verification"]="page"; NBY["us-21cfr4"]["status_note"]="in force"

# --- domain / gates / key / group ---
# id -> (domain, gate_from, gate_to, key)
P={
"ich-q2r2":("quality",2,6,"ICH Q2(R2)"),"ich-q3a":("quality",2,6,"ICH Q3A(R2)"),"ich-q3c":("quality",2,6,"ICH Q3C(R9)"),
"ich-q3d":("quality",2,6,"ICH Q3D(R2)"),"ich-q6a":("quality",6,6,"ICH Q6A"),"ich-q11":("quality",2,6,"ICH Q11"),
"ich-q14":("quality",2,6,"ICH Q14"),"ich-q1":("quality",2,7,"ICH Q1 (consol.)"),"ich-q1ar2":("quality",2,7,"ICH Q1A(R2)"),"ich-m7r2":("quality",2,6,"ICH M7(R2)"),
"pheur-oligo":("quality",2,6,"Ph. Eur. gen. texts"),"usp-oligo":("quality",2,6,"USP oligo prog."),
"ema-oligo-quality":("quality",2,6,"EMA oligo GL"),"jp-oligo-quality":("quality",2,6,"JP oligo quality"),
"ema-impd-q":("quality",2,5,"EMA IMPD-Q"),"ema-mab-gl":("quality",2,6,"EMA mAb GL"),
"fda-nanomaterials":("quality",2,6,"FDA nanomaterials"),"fda-liposome":("quality",2,6,"FDA liposomes"),
"fda-novel-excipient":("quality",1,2,"FDA excipient pilot"),
"ema-ddc-gl":("quality",2,6,"EMA drug–device GL"),"us-21cfr4":("auth",2,7,"21 CFR 4 combination"),
"ich-m3r2":("nonclin",1,5,"ICH M3(R2)"),"ich-s9":("nonclin",1,5,"ICH S9 (oncology)"),"ich-s2r1":("nonclin",1,2,"ICH S2(R1)"),
"ich-s3a":("nonclin",1,1,"ICH S3A TK"),"ich-s5r3":("nonclin",1,5,"ICH S5(R3)"),"ich-s6r1":("nonclin",1,2,"ICH S6(R1) · AOC"),
"ich-s7a":("nonclin",1,1,"ICH S7A"),"ich-s7b":("nonclin",1,1,"ICH S7B"),"ich-s1":("nonclin",5,6,"ICH S1 carc."),
"oswg":("nonclin",0,2,"OSWG papers"),"fda-oligo-nonclin":("nonclin",1,2,"FDA oligo nonclin."),
"pmda-oligo":("nonclin",1,2,"JP oligo nonclin."),"fda-aso-nonclin":("nonclin",1,2,"FDA iASO nonclin."),
"cns-goyenvalle-2023":("nonclin",0,2,"CNS delivery review"),"cns-berman-booty-2023":("nonclin",1,2,"IT procedure effects"),
"cns-ijt-2020":("nonclin",1,1,"IT NHP lesions"),"cns-toxpath-nfd":("nonclin",1,2,"IT nerve-fibre opinion"),
"ich-e6r3":("clinical",3,5,"ICH E6(R3) GCP"),"ich-e6r2":("clinical",3,5,"ICH E6(R2)"),"ich-e8r1":("clinical",2,5,"ICH E8(R1)"),
"ich-e9":("clinical",3,6,"ICH E9"),"ich-e9r1":("clinical",3,6,"ICH E9(R1)"),
"ich-e17":("clinical",5,5,"ICH E17 MRCT"),"ich-m10":("clinical",3,6,"ICH M10 bioanalysis"),"ich-e14s7b":("clinical",3,4,"E14/S7B Q&A"),
"fda-oligo-clinpharm":("clinical",3,6,"FDA oligo clin-pharm"),"fda-adc-clinpharm":("clinical",3,6,"FDA ADC clin-pharm"),
"ema-fih":("clinical",2,3,"EMA first-in-human"),"fda-dili-2009":("clinical",3,6,"FDA DILI"),"fda-renal-pk-2024":("clinical",3,6,"FDA renal PK"),
"eu-paed-reg":("paed",3,7,"EU Reg 1901/2006"),"eu-pip-guidance":("paed",3,4,"PIP format GL"),"eu-stepwise-pip":("paed",3,5,"Stepwise PIP"),
"us-prea":("paed",4,6,"PREA"),"us-bpca":("paed",5,7,"BPCA"),"us-race":("paed",0,6,"RACE Act"),
"fda-paed-target-list":("paed",0,0,"FDA target list"),"fda-ipsp":("paed",4,5,"FDA iPSP GL"),
"fda-fdara-pedonc":("paed",4,5,"FDARA paed-onc GL"),"ich-e11r1":("paed",3,5,"ICH E11(R1)"),"ich-e11a":("paed",3,5,"ICH E11A extrapol."),
"ich-s11":("paed",1,2,"ICH S11 juvenile"),
"eu-orphan-reg":("rare",0,6,"EU Reg 141/2000"),"us-oda":("rare",0,6,"Orphan Drug Act"),"eu-prime":("rare",2,4,"PRIME"),
"us-breakthrough":("rare",3,5,"Breakthrough"),"us-fast-track":("rare",2,3,"Fast Track"),"eu-accelerated":("rare",5,6,"Accel. assessment"),
"eu-camp":("rare",5,6,"Conditional MA"),"us-accel-approval":("rare",6,6,"Accel. approval"),"us-rpd-prv":("rare",6,6,"RPD voucher"),
"fda-expedited-2014":("rare",2,6,"FDA expedited GL"),
"fda-rare-dis":("rare",1,5,"FDA rare-disease GL"),"fda-rdep":("rare",5,6,"RDEP"),
"fda-individualized-2026":("rare",2,6,"Plausible Mechanism"),"fda-aso-ind-clin":("rare",2,3,"FDA iASO clinical"),
"fda-aso-admin":("rare",2,2,"FDA iASO admin."),
"eu-ctr":("auth",2,5,"EU CTR 536/2014"),"us-ind":("auth",2,5,"21 CFR 312 IND"),"uk-mhra-cta":("auth",2,5,"UK CTA regime"),
"fda-sponsor-inv-ind":("auth",2,2,"Sponsor-inv. IND"),"ich-m4":("auth",6,6,"ICH M4 CTD"),
"eu-reg-726":("auth",6,7,"EU Reg 726/2004"),"eu-pharma-package":("auth",0,7,"EU pharma package"),
}
GROUPS=[  # (group id, domain, members in display order)
 ("g-ich-quality","quality",["ich-q1ar2","ich-q1","ich-q2r2","ich-q3a","ich-q3c","ich-q3d","ich-q11","ich-q14","ich-m7r2"]),
 ("g-oligo-quality","quality",["ema-oligo-quality","jp-oligo-quality","pheur-oligo","usp-oligo"]),
 ("g-carrier-quality","quality",["ema-mab-gl","fda-nanomaterials","fda-liposome","ema-ddc-gl"]),
 ("g-eu-expedited","rare",["eu-accelerated","eu-camp"]),
 ("g-safety-pharm","nonclin",["ich-s7a","ich-s7b"]),
 ("g-genotox-biotech","nonclin",["ich-s2r1","ich-s6r1"]),
 ("g-oligo-nonclin","nonclin",["fda-oligo-nonclin","pmda-oligo"]),
 ("g-m3-s5","nonclin",["ich-m3r2","ich-s5r3"]),
 ("g-cns-it","nonclin",["cns-berman-booty-2023","cns-toxpath-nfd"]),
 ("g-stats","clinical",["ich-e9","ich-e9r1","ich-m10"]),
 ("g-gcp","clinical",["ich-e6r3","ich-e6r2"]),
 ("g-organ-impairment","clinical",["fda-dili-2009","fda-renal-pk-2024"]),
 ("g-e11","paed",["ich-e11r1","ich-e11a"]),
 ("g-ipsp","paed",["fda-ipsp","fda-fdara-pedonc"]),
 ("g-iaso","rare",["fda-aso-admin","fda-aso-ind-clin"]),
 ("g-cta","auth",["eu-ctr","us-ind","uk-mhra-cta"]),
]
TRIGGERS={
 "paed_onc":["ich-s9","ich-s11","us-race","fda-paed-target-list","fda-fdara-pedonc","eu-paed-reg","eu-pip-guidance","eu-stepwise-pip",
             "fda-ipsp","ich-e11r1","ich-e11a","us-rpd-prv","eu-orphan-reg","us-oda","us-prea"],
 "aoc":["ich-s6r1","ema-mab-gl","fda-adc-clinpharm","ema-oligo-quality","fda-oligo-nonclin","fda-oligo-clinpharm"],
 "lnp":["fda-nanomaterials","fda-liposome","fda-novel-excipient","oswg","ema-oligo-quality","ich-q3c"],
 "galnac":["fda-oligo-clinpharm","fda-dili-2009","fda-oligo-nonclin","ema-oligo-quality"],
 "intrathecal":["ema-fih","ich-s7a","ich-s11","fda-oligo-nonclin","pmda-oligo","fda-oligo-clinpharm",
                "cns-goyenvalle-2023","cns-berman-booty-2023","cns-ijt-2020","cns-toxpath-nfd","ema-ddc-gl","us-21cfr4"],
 "individualised":["fda-aso-admin","fda-aso-nonclin","fda-aso-ind-clin","fda-individualized-2026","fda-sponsor-inv-ind","fda-rdep","fda-rare-dis"],
}
MS_GATE={"m-discovery":0,"m-nonclinical":1,"m-cta-ind":2,"m-phase1":3,"m-phase2":4,"m-eop2":4,"m-phase3":5,"m-filing":6,"m-approval":6,"m-lifecycle":7}
CONS_GATE={"c-hyb-offtarget":(0,1),"c-immunostim":(1,3),"c-hepatotox":(1,5),"c-nephro":(1,5),"c-thrombocytopenia":(3,5),
           "c-impurities":(2,6),"c-delivery":(0,2),"c-cns-delivery":(1,3),"c-clinpharm":(3,6)}
grp_of={}
for gid,dom,members in GROUPS:
    for m in members: grp_of[m]=gid
trig_of={}
for t,ids in TRIGGERS.items():
    for i in ids: trig_of.setdefault(i,[]).append(t)

for n in N:
    i=n["id"]
    if n["kind"]=="milestone":
        n["domain"]="spine"; n["gate_from"]=n["gate_to"]=MS_GATE[i]; n["key"]=None; n["group"]=None; n["triggers"]=[]
    elif n["kind"]=="consideration":
        n["domain"]="consideration"; n["gate_from"],n["gate_to"]=CONS_GATE[i]; n["key"]=None; n["group"]=None; n["triggers"]=[]
    else:
        assert i in P, f"no placement for {i}"
        dom,a,b,key=P[i]; n["domain"]=dom; n["gate_from"]=a; n["gate_to"]=b; n["key"]=key; n["group"]=grp_of.get(i); n["triggers"]=trig_of.get(i,[])
    n["last_checked"]=CHECK_DATE if n.get("verification") in ("page","search","secondary") else None
    n.pop("phase",None)
for i in P: assert i in NBY, f"placement for unknown node {i}"
for gid,dom,members in GROUPS:
    for m in members: assert NBY[m]["domain"]==dom,(gid,m)

# --- edges: drop stored governs_phase (derived from spans), add Phase B links and supersedes/amends ---
E=[e for e in E if e["rel"]!="governs_phase"]
for s in ("cns-goyenvalle-2023","cns-berman-booty-2023","cns-ijt-2020","cns-toxpath-nfd"): edge(s,"c-cns-delivery","addresses")
edge("cns-goyenvalle-2023","c-hepatotox","addresses"); edge("cns-goyenvalle-2023","c-immunostim","addresses")
edge("fda-dili-2009","c-hepatotox","addresses"); edge("fda-renal-pk-2024","c-nephro","addresses")
edge("fda-oligo-clinpharm","fda-renal-pk-2024","references"); edge("fda-oligo-clinpharm","fda-dili-2009","references")
edge("ich-q1","ich-q1ar2","supersedes"); edge("ich-e6r3","ich-e6r2","supersedes"); edge("ich-e9r1","ich-e9","amends")
edge("us-accel-approval","fda-expedited-2014","supersedes")
for p in ("us-breakthrough","us-fast-track"): edge(p,"fda-expedited-2014","references")
edge("eu-pharma-package","eu-paed-reg","amends")
edge("ema-ddc-gl","c-cns-delivery","addresses"); edge("us-21cfr4","c-cns-delivery","addresses")
edge("ema-ddc-gl","c-delivery","addresses")
# derived gate links (not part of the semantic edge set; kept for tooling)
DERIVED=[]
for n in N:
    if n["kind"] in ("milestone","consideration"): continue
    for m,gi in MS_GATE.items():
        if n["gate_from"]<=gi<=n["gate_to"] and m!="m-eop2" and m!="m-approval": DERIVED.append(dict(source=n["id"],target=m,rel="applies_at"))

# ===================== VALIDATE =====================
ids = [n["id"] for n in N]
dup = {i for i in ids if ids.count(i) > 1}
assert not dup, f"duplicate node ids: {dup}"
idset = set(ids)
bad = [(e["source"], e["target"]) for e in E if e["source"] not in idset or e["target"] not in idset]
assert not bad, f"edges referencing missing nodes: {bad}"

deg = {i: 0 for i in idset}
for e in E + DERIVED:
    deg[e["source"]] += 1; deg[e["target"]] += 1
orph = [i for i, d in deg.items() if d == 0]
assert not orph, f"orphan nodes: {orph}"

# dedupe edges
seen = set(); E2 = []
for e in E:
    k = (e["source"], e["target"], e["rel"])
    if k not in seen:
        seen.add(k); E2.append(e)
E = E2

# ---- short labels for graph display ----
import re as _re
CODE_RE = _re.compile(r'^(ICH |Regulation|21 CFR|FDARA|PREA|BPCA|RACE|Ph\. Eur\.|USP|MHLW)')
SHORT = {
 "m-nonclinical":"Nonclinical package","m-cta-ind":"CTA / IND","m-filing":"MAA / NDA / BLA",
 "m-discovery":"Discovery","m-lifecycle":"Post-approval","m-approval":"Authorisation",
 "m-eop2":"End-of-Phase-2","m-phase1":"Phase 1 (FIH)","m-phase2":"Phase 2","m-phase3":"Phase 3",
 "c-hyb-offtarget":"Off-target (hybridis.)","c-cns-delivery":"CNS delivery",
 "c-clinpharm":"Clin-pharm profile","c-thrombocytopenia":"Thrombocytopenia",
 "c-immunostim":"Immunostimulation","c-nephro":"Nephrotoxicity","c-hepatotox":"Hepatotoxicity",
 "c-impurities":"Impurity control","c-delivery":"Delivery & conjugation",
 "fda-paed-target-list":"Paed. target list","us-rpd-prv":"Rare-Paediatric PRV",
 "fda-novel-excipient":"Novel Excipient Pilot",
}
SHORT.update(SHORT_EXTRA)
SHORT.update({"fda-individualized-2026":"Plausible Mechanism (draft)",
              "ema-oligo-quality":"EMA oligo guideline (draft)",
              "pheur-oligo":"Ph. Eur. (general texts)","usp-oligo":"USP oligo standards",
              "pmda-oligo":"JP oligo nonclinical","fda-aso-ind-clin":"iASO clinical (draft)",
              "fda-aso-nonclin":"iASO nonclinical (draft)","uk-mhra-cta":"UK CTA regime",
              "eu-stepwise-pip":"Stepwise PIP","ich-e9":"ICH E9 / E9(R1)",
              "oswg":"OSWG white papers","us-prea":"PREA","us-bpca":"BPCA",
              "us-race":"RACE for Children Act"})
def short_of(n):
    if n["id"] in SHORT: return SHORT[n["id"]]
    lab=n["label"]
    if " — " in lab:
        pre,post=lab.split(" — ",1)
        if CODE_RE.match(pre): return pre
        return post if len(post)<=30 else post[:28]+"…"
    return lab if len(lab)<=30 else lab[:28]+"…"
for n in N: n["short"]=short_of(n)
for n in N:
    if n.get("key") is None: n["key"]=n["short"]
keys=[n["key"] for n in N]
assert len(keys)==len(set(keys)), f"duplicate keys: {[k for k in keys if keys.count(k)>1]}"
# ensure shorts are reasonably distinct
from collections import Counter as _C
dupes={k:v for k,v in _C(n["short"] for n in N).items() if v>1}
assert not dupes, f"duplicate short labels: {dupes}"

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT,"nodes.json"),"w") as f: json.dump(N,f,indent=2,ensure_ascii=False)
with open(os.path.join(OUT,"edges.json"),"w") as f: json.dump(E,f,indent=2,ensure_ascii=False)
graph = {"meta":{"title":"Oligonucleotide Regulatory Requirements Graph",
                 "version":"0.4.0","data_model":"0.3","generated":"2026-10-28",
                 "gates":[{"id":g,"label":l,"index":i} for i,(g,l) in enumerate(GATES)],
                 "domains":[{"id":d,"label":l} for d,l in DOMAINS],
                 "groups":[{"id":gid,"domain":dom,"members":m} for gid,dom,m in GROUPS],
                 "triggers":{"paed_onc":"Paediatric oncology","aoc":"Antibody–oligo conjugate","lnp":"LNP-formulated","galnac":"GalNAc–siRNA (hepatic)","intrathecal":"Intrathecal / CNS","individualised":"Individualised ASO"},
                 "changes":"0.2.0: reconciled against a verified source inventory (107 documents); corrected status/dates/document numbers; added verification provenance and 19 documents.",
                 "license_data":"CC BY 4.0","license_code":"MIT",
                 "disclaimer":"Reference map, not regulatory advice. Verify every document against the issuing body before relying on it.",
                 "node_count":len(N),"edge_count":len(E)},
         "nodes":N,"edges":E,"derived":{"applies_at":DERIVED}}
with open(os.path.join(OUT,"graph.json"),"w") as f: json.dump(graph,f,indent=2,ensure_ascii=False)

with open(os.path.join(OUT,"nodes.csv"),"w",newline="") as f:
    w=csv.writer(f); w.writerow(["id","key","label","kind","domain","gate_from","gate_to","group","region","ref","date","status","status_note","confidence","verification","last_checked","url","scope","oligo_note","modality","triggers"])
    for n in N: w.writerow([n["id"],n["key"],n["label"],n["kind"],n["domain"],n["gate_from"],n["gate_to"],n.get("group"),n["region"],n["ref"],n["date"],n["status"],n.get("status_note"),n["confidence"],n.get("verification"),n.get("last_checked"),n["url"],n["scope"],n["oligo_note"],";".join(n["modality"]),";".join(n["triggers"])])
with open(os.path.join(OUT,"edges.csv"),"w",newline="") as f:
    w=csv.writer(f); w.writerow(["source","target","rel"])
    for e in E: w.writerow([e["source"],e["target"],e["rel"]])

from collections import Counter
print("nodes:",len(N)," edges:",len(E))
print("by kind:",dict(Counter(n["kind"] for n in N)))
print("by region:",dict(Counter(n["region"] for n in N)))
print("verify/low:",[n["id"] for n in N if n["confidence"]=="low" or n["status"]=="verify"])
