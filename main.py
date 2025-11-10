import os
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import create_document, get_documents
from schemas import (
    Advisor,
    Household,
    Client,
    Account,
    Note,
    Task,
    Communication,
    Document as Doc,
    Recommendation,
    Compliance,
    PortfolioAnalysisRequest,
    TaxOptimizationRequest,
    EstatePlanningRequest,
)

app = FastAPI(title="AI-Driven Wealth CRM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "AI Wealth CRM Backend is running"}


@app.get("/schema")
def get_schema_registry():
    """Expose schemas so the database viewer and UI can render forms automatically."""
    return {
        "collections": [
            "advisor",
            "household",
            "client",
            "account",
            "note",
            "task",
            "communication",
            "document",
            "recommendation",
            "compliance",
        ]
    }


# ----------------------------
# Generic create/list endpoints
# ----------------------------

class CreatePayload(BaseModel):
    collection: str
    data: Dict[str, Any]


@app.post("/api/create")
def api_create(payload: CreatePayload):
    collection = payload.collection.lower()
    try:
        inserted_id = create_document(collection, payload.data)
        # Write compliance log
        create_document(
            "compliance",
            {
                "action": "create_document",
                "actor_id": payload.data.get("author_id") or payload.data.get("assignee_id"),
                "resource_type": collection,
                "resource_id": inserted_id,
                "context": {"fields": list(payload.data.keys())},
                "labels": ["auto-log", "create"],
                "severity": "info",
                "timestamp": datetime.utcnow(),
            },
        )
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/list/{collection}")
def api_list(collection: str, limit: int = 50):
    try:
        docs = get_documents(collection.lower(), {}, limit)
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ----------------------------
# AI endpoints (rule-based placeholder logic for now)
# ----------------------------

@app.post("/api/ai/portfolio/analysis")
def ai_portfolio_analysis(req: PortfolioAnalysisRequest):
    # Fetch accounts/holdings for rough analysis
    accounts = []
    if req.account_ids:
        for acc_id in req.account_ids:
            results = get_documents("account", {"_id": acc_id}, 1)
            accounts.extend(results)
    elif req.household_id:
        accounts = get_documents("account", {"household_id": req.household_id}, 500)

    total = sum(a.get("balance", 0) for a in accounts)
    allocations = {"equities": 0.6, "fixed_income": 0.35, "cash": 0.05}
    rationale = "Target diversified allocation with emphasis on risk-adjusted returns."

    recommendation_id = create_document(
        "recommendation",
        {
            "category": "investment",
            "title": "Rebalance to target policy mix",
            "rationale": rationale,
            "impact_score": 0.72,
            "household_id": req.household_id,
            "details": {"current_total": total, "target_allocations": allocations},
            "status": "proposed",
        },
    )

    create_document(
        "compliance",
        {
            "action": "generate_recommendation",
            "actor_id": None,
            "resource_type": "recommendation",
            "resource_id": recommendation_id,
            "context": {"category": "investment"},
            "labels": ["ai", "portfolio"],
            "severity": "info",
            "timestamp": datetime.utcnow(),
        },
    )

    return {
        "summary": {
            "total_balance": total,
            "target_allocations": allocations,
        },
        "recommendation_id": recommendation_id,
    }


@app.post("/api/ai/tax/optimization")
def ai_tax_optimization(req: TaxOptimizationRequest):
    year = req.year
    # Placeholder: harvest losses if unrealized losses > threshold
    strategy = {
        "harvest_loss_threshold": 3000,
        "asset_location": "place bonds in tax-advantaged accounts",
        "roth_conversion": "consider partial conversions if current bracket < future",
    }

    reco_id = create_document(
        "recommendation",
        {
            "category": "tax",
            "title": f"Tax optimization opportunities for {year}",
            "rationale": "Based on standard tax-efficient investing heuristics.",
            "impact_score": 0.65,
            "details": strategy,
            "status": "proposed",
        },
    )

    create_document(
        "compliance",
        {
            "action": "generate_recommendation",
            "actor_id": None,
            "resource_type": "recommendation",
            "resource_id": reco_id,
            "context": {"category": "tax", "year": year},
            "labels": ["ai", "tax"],
            "severity": "info",
            "timestamp": datetime.utcnow(),
        },
    )

    return {"recommendation_id": reco_id, "strategy": strategy}


@app.post("/api/ai/estate/plan")
def ai_estate_plan(req: EstatePlanningRequest):
    plan = {
        "will_status": "review_needed",
        "trust_recommendation": "consider revocable living trust",
        "beneficiary_review": "ensure beneficiary designations align with goals",
    }

    reco_id = create_document(
        "recommendation",
        {
            "category": "estate",
            "title": "Estate planning review",
            "rationale": "Standard best-practice checks based on provided facts.",
            "impact_score": 0.58,
            "household_id": req.household_id,
            "details": plan,
            "status": "proposed",
        },
    )

    create_document(
        "compliance",
        {
            "action": "generate_recommendation",
            "actor_id": None,
            "resource_type": "recommendation",
            "resource_id": reco_id,
            "context": {"category": "estate"},
            "labels": ["ai", "estate"],
            "severity": "info",
            "timestamp": datetime.utcnow(),
        },
    )

    return {"recommendation_id": reco_id, "plan": plan}


# Health + DB connectivity check
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:20]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
                response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
                response["database_name"] = db.name
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
