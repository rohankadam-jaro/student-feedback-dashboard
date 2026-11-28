# Student Feedback Dashboard (all universities)

Single page: filters -> videos -> reviews, for DPU, BVDU, Symbiosis, Amrita, Amity, CU, DSU, LIBA, Parul, MUJ, Dr. MGR.

- `public/index.html` the dashboard
- `public/feedback.json`, `public/videos.json` data (regenerate with `portal/scripts/build_feedback.py`)

No access restriction is configured; contains student names, so keep the repo private. Deploy: `vercel --prod`.

## Data set (`data/`)
- `data/<University>.json` raw feedback per university, untouched source (keys: n name, p program, c company, d domain, de designation, e experience yrs, f feedback, r rating)
- `data/all_feedback.csv` cleaned, all universities combined (6,085 rows); `Company_Original` keeps the raw spelling
- `data/company_mapping.csv` every raw company spelling -> its standard name, for review
- `public/feedback.json` the cleaned data the page loads (adds `u` = university)

## Rebuild after data changes
`python scripts/build_feedback.py` cleans `data/*.json` and rewrites the three generated files. It standardises
company names (case, Ltd/Pvt suffixes, spacing, plurals, typos, known aliases like TCS -> Tata Consultancy Services),
programs (Online MBA -> MBA), job titles (spelling: Mannager -> Manager; Sr./Asst./Jr./Dy. expanded; HR/AVP kept upper), names and experience values. Add a word to `SPELL` to fix another title typo. Add a line to `ALIASES` to force a merge.
