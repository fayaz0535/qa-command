from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401 — imported so every model class is registered on the ORM mapper

app = FastAPI(
    title="QA Command API",
    description="Test Execution & Defect Metrics platform — ZAIMAH TECHNOLOGIES",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://qa.zaimahtech.ae", "http://localhost:3004", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers.upload import router as upload_router
from routers.defects import router as defects_router
from routers.tests import router as tests_router
from routers.hierarchy import router as hierarchy_router
from routers.metrics import router as metrics_router
from routers.insights import router as insights_router
from routers.email import router as email_router
from routers.export import router as export_router
from routers.ado import router as ado_router

app.include_router(upload_router)
app.include_router(defects_router)
app.include_router(tests_router)
app.include_router(hierarchy_router)
app.include_router(metrics_router)
app.include_router(insights_router)
app.include_router(email_router)
app.include_router(export_router)
app.include_router(ado_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "qa-command-api", "time": datetime.utcnow().isoformat()}
