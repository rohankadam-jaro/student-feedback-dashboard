# Student Feedback Dashboard (all universities)

Single page: filters -> videos -> reviews, for DPU, BVDU, Symbiosis, Amrita, Amity, CU, DSU, LIBA, Parul, MUJ, Dr. MGR.

- `public/index.html` the dashboard
- `public/feedback.json`, `public/videos.json` data (regenerate with `portal/scripts/build_feedback.py`)

No access restriction is configured; contains student names, so keep the repo private. Deploy: `vercel --prod`.

## Data set (`data/`)
- `data/<University>.json` raw feedback per university (keys: n name, p program, c company, d domain, de designation, e experience yrs, f feedback, r rating)
- `data/all_feedback.csv` all universities combined (6,085 rows)
- `public/feedback.json` is the same data merged for the page (adds `u` = university)
