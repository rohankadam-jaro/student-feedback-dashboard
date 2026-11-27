"""Merge each university's public/td.json into portal/public/feedback.json and
pull testimonial videos out of Symbiosis/public/testimonials.html into videos.json."""
import json, re, pathlib
root = pathlib.Path(__file__).resolve().parents[2]
out = root / "portal" / "public"
UNIS = {"DPU":"DPU","BVDU":"BVDU","Symbiosis":"Symbiosis","Amrita":"Amrita","Amity":"Amity",
        "CU":"CU","DSU":"DSU","LIBA":"LIBA","Parul":"Parul","MUJ":"MUJ","MGR":"Dr. MGR"}
rows = []
for folder, label in UNIS.items():
    for r in json.load(open(root/folder/"public"/"td.json", encoding="utf-8")):
        r["u"] = label; rows.append(r)
json.dump(rows, open(out/"feedback.json","w",encoding="utf-8"), ensure_ascii=False, separators=(",",":"))

html = open(root/"Symbiosis"/"public"/"testimonials.html", encoding="utf-8").read()
vids = []
for m in re.finditer(r'<div class="video-card[^"]*" data-cat="(\w+)">(.*?)\n      </div>\n', html, re.S):
    cat, b = m.groups()
    src = re.search(r'<source src="([^"]+)"', b)
    label = re.search(r'video-label">([^<]+)', b)
    sub = re.search(r'video-sub">([^<]+)', b)
    yt = re.search(r'class="video-yt-btn" href="([^"]+)"', b)
    if src and label:
        vids.append({"u":"Symbiosis","cat":cat,"src":src[1],"t":label[1],"s":sub[1] if sub else "","yt":yt[1] if yt else ""})
json.dump(vids, open(out/"videos.json","w",encoding="utf-8"), ensure_ascii=False, separators=(",",":"))
print(len(rows), "reviews;", len(vids), "videos")
