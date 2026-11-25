# Student Feedback Dashboard (all universities)

Single page: filters -> videos -> reviews, for DPU, BVDU, Symbiosis, Amrita, Amity, CU, DSU, LIBA, Parul, MUJ, Dr. MGR.

- `public/index.html` the dashboard
- `public/feedback.json`, `public/videos.json` data (regenerate with `portal/scripts/build_feedback.py`)

No access restriction is configured; contains student names, so keep the repo private. Deploy: `vercel --prod`.
