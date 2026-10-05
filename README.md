# Second Opinion

A surgical patient's own advocate. It keeps the case in SQLite, with Token Factory embeddings for recall, so what the surgeon said last week is still there next week. It shows where hospital volume matters for the operation and where it does not, using public data only.

Live: https://uyyhnmechu.ap-southeast-2.awsapprunner.com

## NVIDIA Nemotron and Nebius Token Factory
- Nano (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`): reads the clinic letter and maps the operation to a dataset.
- Lightning (`nvidia/Nemotron-3_5-Lightning`): tool call that opens the dataset (the mapping stays authoritative).
- Super (`nvidia/nemotron-3-super-120b-a12b`): plain-language reading of the table; replies to new messages using recalled memory.
- Ultra (`nvidia/Nemotron-3-Ultra-550b-a55b`): judges whether volume decides for this operation, grounded in the studies listed in `evidence.py`.
- `Qwen3-Embedding-8B` (also on Token Factory): memory recall. No other model is used.

Every model call runs on Nebius Token Factory, which is serverless and OpenAI-compatible, so one base URL and the standard OpenAI client reached every model with no GPU and no dedicated endpoint to provision. That is what let this be built and deployed quickly, and the four Nemotron tiers let each call sit on the right-sized, right-priced model: Nano for letter reading, Lightning for tool calls, Super for explanation and replies, Ultra for the volume judgment.

Assessments for the three example cases are precomputed in `backend/cache/`. "Run it", messages and memory search call the model live (capped at 60 calls per process).

## Data
CMS Complications and Deaths and Medicare Inpatient by DRG (public domain), NJR transparency data (OGL), NOGCA 2023 tables (CC BY). Leapfrog results are not shown. Court opinions reviewed state no award amounts; none are quoted. The three patients and their letters are examples.

Docker: `docker build -t second-opinion . && docker run -p 8080:8080 -e NEBIUS_API_KEY=... second-opinion`

Stack: Python, FastAPI, SQLite, React (Vite), NVIDIA Nemotron and Qwen3-Embedding on Nebius Token Factory.

Licensed under the Apache License 2.0.

## Run
    cd backend && pip install -r requirements.txt && python3 -m uvicorn main:app --port 8009
    cd frontend && npm install && npm run build   # outputs to backend/static
Set `NEBIUS_API_KEY` in the environment. `DATA_DIR` sets where the SQLite file lives.
