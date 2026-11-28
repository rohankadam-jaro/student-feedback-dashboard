"""Clean + merge the raw per-university feedback in data/<Uni>.json.

Writes:
  public/feedback.json      data the dashboard loads (adds u = university)
  data/all_feedback.csv     cleaned, all universities (keeps Company_Original)
  data/company_mapping.csv  every raw company spelling -> standard name, for review

Run: python scripts/build_feedback.py
"""
import collections, csv, difflib, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
UNIS = {"DPU": "DPU", "BVDU": "BVDU", "Symbiosis": "Symbiosis", "Amrita": "Amrita", "Amity": "Amity",
        "CU": "CU", "DSU": "DSU", "LIBA": "LIBA", "Parul": "Parul", "MUJ": "MUJ", "MGR": "Dr. MGR"}

JUNK = re.compile(r"(?i)^(na|n/?a|n\.a\.?|nil|none|no|null|nothing|not applicable|-+|\.+|0)$")
SUFFIX = {"ltd", "limited", "pvt", "private", "pvtltd", "llp", "inc", "corp", "corporation", "co", "company",
          "plc", "llc", "opc", "p", "lt", "ltdd", "pltd"}
WEAK_TAIL = {"india", "technology", "solution", "service", "group", "global", "consulting"}

# key regex -> standard name (checked against the normalised key)
ALIASES = [
    (r"^axis ?bank", "Axis Bank"), (r"^axis ?max ?life", "Axis Max Life Insurance"),
    (r"^max ?life", "Max Life Insurance"), (r"^icici bank", "ICICI Bank"),
    (r"^icici prudential life", "ICICI Prudential Life Insurance"), (r"^icici prudential (mutual|amc|asset)", "ICICI Prudential AMC"),
    (r"^icici lombard", "ICICI Lombard"), (r"^(sbi|state bank of india)( bank)?$", "State Bank of India"),
    (r"^sbi life", "SBI Life Insurance"), (r"^sbi card", "SBI Card"), (r"^hdfc bank", "HDFC Bank"),
    (r"^hdfc life", "HDFC Life"), (r"^hdfc ergo", "HDFC ERGO"),
    (r"^kotak (mahindra )?bank|^kotak mahindra$|^kotak$", "Kotak Mahindra Bank"), (r"^kotak (mahindra )?life", "Kotak Life Insurance"),
    (r"^kotak securitie", "Kotak Securities"),
    (r"^yes bank", "Yes Bank"), (r"^idfc", "IDFC FIRST Bank"), (r"^indusind", "IndusInd Bank"),
    (r"^bajaj finance", "Bajaj Finance"), (r"^bajaj finserv", "Bajaj Finserv"), (r"^bajaj allianz life", "Bajaj Allianz Life Insurance"),
    (r"^bajaj allianz general", "Bajaj Allianz General Insurance"), (r"^bajaj allianz$", "Bajaj Allianz"),
    (r"^bank of america", "Bank of America"), (r"^deutsche bank", "Deutsche Bank"), (r"^dcb bank", "DCB Bank"),
    (r"^accenture", "Accenture"), (r"^deloitte", "Deloitte"), (r"^concentrix", "Concentrix"),
    (r"^amazon", "Amazon"), (r"^flipkart", "Flipkart"), (r"^(tcs|tata consultancy)", "Tata Consultancy Services"),
    (r"^wipro", "Wipro"), (r"^capgemini", "Capgemini"), (r"^cognizant", "Cognizant"), (r"^genpact", "Genpact"),
    (r"^tech ?mahindra", "Tech Mahindra"), (r"^infosys", "Infosys"), (r"^(hcl|hcltech)\b", "HCLTech"),
    (r"^ibm\b", "IBM"), (r"^adp$", "ADP"), (r"^(ey|ernst and young|ernst young)\b", "EY"), (r"^kpmg", "KPMG"),
    (r"^(pwc|pricewaterhouse)", "PwC"), (r"^wns\b", "WNS"), (r"^eclerx", "eClerx"), (r"^teleperformance", "Teleperformance"),
    (r"^reliance jio|^jio\b", "Reliance Jio"), (r"^reliance retail", "Reliance Retail"), (r"^reliance industries", "Reliance Industries"),
    (r"^(airtel|bharti airtel)", "Bharti Airtel"), (r"^vodafone", "Vodafone Idea"), (r"^salesforce", "Salesforce"),
    (r"^tata motors", "Tata Motors"), (r"^tata steel", "Tata Steel"), (r"^tata power", "Tata Power"),
    (r"^(l and t|lnt|larsen)", "Larsen & Toubro"), (r"^mahindra and mahindra", "Mahindra & Mahindra"),
    (r"^air india", "Air India"), (r"^astrazeneca", "AstraZeneca"), (r"^hexaware", "Hexaware"), (r"^teamlease", "TeamLease"),
    (r"^policy ?bazaar", "Policybazaar"), (r"^apollo hospital", "Apollo Hospitals"), (r"^alstom", "Alstom"),
    (r"^bosch", "Bosch"), (r"^sun pharma", "Sun Pharma"), (r"^dr reddy", "Dr. Reddy's"), (r"^mott macdonald", "Mott MacDonald"),
    (r"^lodha", "Lodha"), (r"^anz\b", "ANZ"), (r"^cbre\b", "CBRE"), (r"^ust\b", "UST"), (r"^indian army", "Indian Army"),
    (r"^indian navy", "Indian Navy"), (r"^indian air ?force", "Indian Air Force"), (r"^ltimindtree|^lti\b|^mindtree", "LTIMindtree"),
    (r"^byju", "BYJU'S"), (r"^zomato", "Zomato"), (r"^swiggy", "Swiggy"), (r"^paytm", "Paytm"), (r"^d ?mart$|^avenue supermarts", "DMart"),
    (r"^bajaj auto$", "Bajaj Auto"), (r"^trichy srm", "Trichy SRM Medical College Hospital & Research Centre"),
    (r"^(self employed|self employee|self|own business|business)$", "Self-employed"), (r"^freelanc", "Freelancer"),
]
PROGRAMS = {
    "MBA": "MBA", "Online MBA": "MBA", "Online MBA Programme": "MBA", "MBA (General Management)": "MBA (General Management)",
    "Executive MBA": "Executive MBA", "MBAwx": "MBA (Working Executives)", "Online BBA": "BBA", "BBA": "BBA",
    "MCA": "MCA", "Online MCA": "MCA", "Online MCA Program": "MCA", "MCA (Artificial Intelligence)": "MCA (Artificial Intelligence)",
    "MCA (Cyber Security)": "MCA (Cyber Security)", "BCA": "BCA", "Online BCA": "BCA",
    "BCA(Data Science & Artificial Intelligence)": "BCA (Data Science & AI)", "Online PGDM": "PGDM",
    "BCOM": "B.Com", "Online BCOM": "B.Com", "MCOM": "M.Com", "Online MCOM": "M.Com", "Online Mcom": "M.Com",
    "M.Com (General)": "M.Com", "BA": "BA", "MA ( MASS COMMUNICATION)": "MA (Mass Communication)",
    "Online MA.JMC": "MA (Journalism & Mass Communication)", "MSc": "M.Sc", "MSC (DATA SCIENCE)": "M.Sc (Data Science)",
    "M.sc Data Science and AI": "M.Sc (Data Science & AI)", "MSC ( COMPUTER SCIENCE)": "M.Sc (Computer Science)",
    "MSC (ECO)": "M.Sc (Economics)", "BSC (ECO)": "B.Sc (Economics)", "M.Sc.Statistics": "M.Sc (Statistics)",
}


# job-title word fixes (curated: auto fuzzy matching wrongly merged real words like resolution/solution)
SPELL = {w: fix for fix, ws in {
    "executive": "exceutive excutive excustive excetuive execuitive exective exicutive excecutive",
    "manager": "mamager mannager managar mager manger maneger", "officer": "offier offficer", "doctor": "docter",
    "physiotherapist": "physiotherapish", "coordinator": "cordiantor coodinatore cordinator", "senior": "seniore sernior seinor",
    "optometrist": "optomertist", "software": "sofware sodtware", "developer": "devloper", "development": "devlopment",
    "sales": "salse", "nursing": "nirsing", "recruiter": "recuiter", "department": "deparment", "business": "bussniess buisness",
    "analyst": "annalyst anaylst analist analysist", "consultant": "cunsultant", "customer": "cutomer", "technical": "technicial",
    "operation": "opration", "supervisor": "supervisior", "administration": "adminstration", "specialist": "specalist speacialist",
    "success": "sucess", "management": "manangement", "trainee": "teainee traniee", "engineer": "enineer enginner",
    "assistant": "assitant asst ast", "associate": "asscoiate assosciate", "proprietor": "proprietar", "research": "reasearch",
    "counsellor": "councellor", "ordinator": "oridinator", "senior": "sr snr", "junior": "jr", "deputy": "dy",
}.items() for w in ws.split()}
ACRONYMS = {"hr", "avp", "vp", "agm", "dgm", "gm", "ceo", "cfo", "coo", "cto", "qa", "qc", "rm", "sme", "tl", "it", "mis",
            "bpo", "kyc", "crm", "sap", "ui", "ux", "ai", "ml", "rmo", "bdm", "bde", "asm", "tsm", "hod", "ehs", "hse",
            "pmo", "erp", "seo", "icu", "opd", "scm"}


def _fix_word(w, last):
    low = w.lower()
    if low == "assistance" and not last:  # "Assistance Manager" -> "Assistant Manager"
        low = "assistant"
    if low in SPELL or low == "assistant":
        return SPELL.get(low, low).capitalize(), True
    if low in ACRONYMS:
        return low.upper(), False
    return w, False


def clean_title(s):
    """Fix spelling, expand Sr/Asst/Jr/Dy, keep acronyms upper: 'Sr. excutive' -> 'Senior Executive'."""
    s = re.sub(r"\s*/\s*", "/", re.sub(r"\s+-\s*|\s*-\s+", " - ", squash(s)))
    s = re.sub(r"(?i)\b(sr|snr|jr|asst|ast|dy)[.-](?=\w)", r"\1. ", s)  # "Sr.Manager"/"SR-EXECUTIVE" -> "Sr. ..."
    toks = s.split()
    out = []
    for i, t in enumerate(toks):
        pre, core, post = re.match(r"^([(\[]*)(.*?)([.,:)\]]*)$", t).groups()
        parts = []
        for p in core.split("/"):
            fixed, expanded = _fix_word(p, i == len(toks) - 1)
            parts.append(fixed)
            if expanded:
                post = post.replace(".", "")  # "Sr." -> "Senior"
        out.append(pre + "/".join(parts) + post)
    return " ".join(out).strip(" -/,")


def squash(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().strip(".,;:-'\"").strip()


def singular(t):
    if len(t) <= 4 or t.endswith(("ss", "us", "is")):
        return t
    return t[:-3] + "y" if t.endswith("ies") else t[:-1] if t.endswith("s") else t


def key_of(s):
    k = s.lower().replace("&", " and ")
    k = re.sub(r"^(m/s\.?|the)\s+", "", k)
    toks = re.sub(r"[^a-z0-9]+", " ", k).split()
    while toks and toks[-1] in SUFFIX:
        toks.pop()
    return " ".join(singular(t) for t in toks)


SMALL = {"of", "and", "the", "for", "in", "at", "on", "&"}


def nice_case(s):
    """Title-case words, keep short all-caps acronyms (ABB, SRM) and mixed brands (eClerx, HCLTech)."""
    out = []
    for i, w in enumerate(s.split()):
        if w.lower() in SMALL and i:
            out.append(w.lower())
        elif w.isupper() and len(re.sub(r"[^A-Za-z]", "", w)) <= 4:
            out.append(w)
        elif w.isupper() or w.islower():
            out.append(w[:1].upper() + w[1:].lower())
        else:
            out.append(w)
    return " ".join(out)


def strip_suffix_display(s):
    toks = re.sub(r"^(?i:m/s\.?|the)\s+", "", s).split()
    while toks and re.sub(r"[^a-z]", "", toks[-1].lower()) in SUFFIX:
        toks.pop()
    return " ".join(toks).strip(" ,.-(")


def best_display(variants):
    """variants: Counter of cleaned spellings. Prefer proper mixed case, then frequency."""
    def score(item):
        s, n = item
        words_capped = all(w[0].isupper() or not w[0].isalpha() or w.lower() in {"of", "and", "the", "for"} for w in s.split())
        return (not (s.isupper() and len(s) > 5) and not s.islower(), words_capped, n)
    return nice_case(max(variants.items(), key=score)[0])


def build_company_map(raws):
    # group key ignores spaces too ("Axismax Life" == "Axis Max Life"); rep keeps a spaced form
    counts = collections.Counter()
    variants = collections.defaultdict(collections.Counter)
    rep, alias_of, raw_key = {}, {}, {}
    for raw, n in raws.items():
        s = squash(raw)
        k = key_of(s) if s and not JUNK.match(s) else ""
        g = k.replace(" ", "")
        raw_key[raw] = g or None
        if not g:
            continue
        counts[g] += n
        variants[g][strip_suffix_display(s) or s] += n
        rep.setdefault(g, k)
        if g not in alias_of:
            for rx, name in ALIASES:
                if re.search(rx, k):
                    alias_of[g] = name
                    break

    # merge "x india" / "x technologies" into "x" when "x" exists
    parent = {}
    for g, k in rep.items():
        toks = k.split()
        if len(toks) > 1 and toks[-1] in WEAK_TAIL and "".join(toks[:-1]) in counts:
            parent[g] = "".join(toks[:-1])
    # typo merge: rare key very close to a common one ("axis nank" -> "axis bank")
    common = [g for g, n in counts.items() if n >= 3]
    for g, n in counts.items():
        k = rep[g]
        if n <= 2 and g not in parent and g not in alias_of and len(g) >= 6:
            # same first word + same word count keeps unrelated names apart
            first, nt = k.split()[0], len(k.split())
            pool = {rep[c]: c for c in common if c != g and rep[c].split()[0] == first and len(rep[c].split()) == nt}
            m = difflib.get_close_matches(k, list(pool), n=1, cutoff=0.85)
            if m:
                parent[g] = pool[m[0]]

    def root(k):
        while k in parent:
            k = parent[k]
        return k

    # display comes from the root's own spellings, so "Morningstar India" folds into "Morningstar"
    final = {k: alias_of.get(k) or alias_of.get(root(k)) or best_display(variants[root(k)]) for k in counts}
    return {raw: (final[k] if k else "") for raw, k in raw_key.items()}


def build_title_map(values):
    """Job titles: spelling + abbreviation fixes, then one display per case/punctuation-insensitive key."""
    def tkey(s):
        return " ".join(re.sub(r"[^a-z0-9&]+", " ", s.lower()).split())
    cleaned = {v: clean_title(v) if squash(v) and not JUNK.match(squash(v)) else "" for v in values}
    groups = collections.defaultdict(collections.Counter)
    for v, n in values.items():
        if cleaned[v]:
            groups[tkey(cleaned[v])][cleaned[v]] += n
    disp = {k: best_display(c) for k, c in groups.items()}
    return {v: disp[tkey(cleaned[v])] if cleaned[v] else "" for v in values}


def exp_years(e):
    try:
        y = float(e)
    except (TypeError, ValueError):
        return None
    return (int(y) if y.is_integer() else y) if y > 0 else None


def main():
    rows = []
    for folder, label in UNIS.items():
        for r in json.load(open(ROOT / "data" / f"{folder}.json", encoding="utf-8")):
            rows.append(dict(r, u=label))
    raw_counts = collections.Counter(r["c"] for r in rows)
    cmap = build_company_map(raw_counts)
    dmap = build_title_map(collections.Counter(r["de"] for r in rows))

    out = []
    for r in rows:
        out.append({
            "u": r["u"], "n": nice_case(squash(r["n"])), "p": PROGRAMS.get(squash(r["p"]), squash(r["p"])),
            "c": cmap[r["c"]], "co": squash(r["c"]), "d": squash(r["d"]), "de": dmap[r["de"]],
            "e": exp_years(r["e"]), "f": re.sub(r"\s+", " ", r["f"]).strip(), "r": r["r"],
        })

    page = [{k: v for k, v in o.items() if k != "co"} for o in out]
    json.dump(page, open(ROOT / "public" / "feedback.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    with open(ROOT / "data" / "all_feedback.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["University", "Name", "Program", "Company", "Company_Original", "Domain", "Designation", "Experience_Years", "Rating", "Feedback"])
        for o in out:
            w.writerow([o["u"], o["n"], o["p"], o["c"], o["co"], o["d"], o["de"], "" if o["e"] is None else o["e"], o["r"], o["f"]])
    with open(ROOT / "data" / "company_mapping.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Company_Original", "Company_Standard", "Reviews"])
        for raw, n in sorted(raw_counts.items(), key=lambda x: (cmap[x[0]].lower(), -x[1])):
            w.writerow([raw, cmap[raw], n])
    print(f"{len(out)} reviews | companies {len(raw_counts)} raw -> {len(set(cmap.values()) - {''})} standard")


def _selfcheck():
    m = build_company_map(collections.Counter({"AXIS BANK": 3, "Axis Bank Ltd.": 2, "Axis Nank": 1, "Axis Max life insurance company": 1,
                                               "Axis Max Life Insurance Company Ltd": 1, "NA": 1, "Genpact India Pvt Ltd": 1,
                                               "Bank of India": 2, "Noble hospital": 4, "Intas Pharmaceutical Ltd": 2,
                                               "Intas Pharmaceuticals": 3, "Axismax Life insurance": 1, "Kotak Life Insurance": 1,
                                               "Kotak Mahindra Bank Ltd": 2}))
    assert m["Intas Pharmaceutical Ltd"] == m["Intas Pharmaceuticals"], m
    assert m["Axismax Life insurance"] == "Axis Max Life Insurance"
    assert m["Kotak Life Insurance"] != m["Kotak Mahindra Bank Ltd"] == "Kotak Mahindra Bank"
    assert m["AXIS BANK"] == m["Axis Bank Ltd."] == m["Axis Nank"] == "Axis Bank", m
    assert m["Axis Max life insurance company"] == m["Axis Max Life Insurance Company Ltd"] == "Axis Max Life Insurance"
    assert m["NA"] == "" and m["Genpact India Pvt Ltd"] == "Genpact" and m["Bank of India"] == "Bank of India"
    assert m["Noble hospital"] == "Noble Hospital"
    assert exp_years("2.0") == 2 and exp_years("") is None and exp_years(0) is None
    t = build_title_map(collections.Counter({"Assistance Mannager": 1, "Assistant Manager": 5, "Sr. excutive": 1,
                                             "Senior Executive": 3, "hr manager": 1, "Sr.Manager": 1, "Senior Manager": 2, "Asst. Manager - HR": 1, "Resolution Analyst": 1, "NA": 1}))
    assert t["Assistance Mannager"] == "Assistant Manager" and t["Sr. excutive"] == "Senior Executive", t
    assert t["hr manager"] == "HR Manager" and t["Asst. Manager - HR"] == "Assistant Manager - HR", t
    assert t["Resolution Analyst"] == "Resolution Analyst" and t["NA"] == "" and t["Sr.Manager"] == "Senior Manager", t


if __name__ == "__main__":
    _selfcheck()
    main()
