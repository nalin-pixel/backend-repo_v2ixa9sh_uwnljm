import os
from datetime import datetime
from typing import Dict, Any, List, Optional

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


def _log_compliance(action: str, resource_type: str, resource_id: Optional[str], labels: List[str], actor_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
    try:
        create_document(
            "compliance",
            {
                "action": action,
                "actor_id": actor_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "context": context or {},
                "labels": labels,
                "severity": "info",
                "timestamp": datetime.utcnow(),
            },
        )
    except Exception:
        # Best-effort logging; do not block the main operation
        pass


@app.post("/api/create")
def api_create(payload: CreatePayload):
    collection = payload.collection.lower()
    try:
        inserted_id = create_document(collection, payload.data)
        # Write compliance log
        _log_compliance(
            action="create_document",
            resource_type=collection,
            resource_id=inserted_id,
            labels=["auto-log", "create"],
            actor_id=payload.data.get("author_id") or payload.data.get("assignee_id"),
            context={"fields": list(payload.data.keys())},
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

    _log_compliance(
        action="generate_recommendation",
        actor_id=None,
        resource_type="recommendation",
        resource_id=recommendation_id,
        context={"category": "investment"},
        labels=["ai", "portfolio"],
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

    _log_compliance(
        action="generate_recommendation",
        actor_id=None,
        resource_type="recommendation",
        resource_id=reco_id,
        context={"category": "tax", "year": year},
        labels=["ai", "tax"],
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

    _log_compliance(
        action="generate_recommendation",
        actor_id=None,
        resource_type="recommendation",
        resource_id=reco_id,
        context={"category": "estate"},
        labels=["ai", "estate"],
    )

    return {"recommendation_id": reco_id, "plan": plan}


# ----------------------------
# Demo seed endpoint
# ----------------------------

class SeedRequest(BaseModel):
    count_clients: int = 20


def _random_pick(seq: List[Any], idx: int) -> Any:
    if not seq:
        return None
    return seq[idx % len(seq)]


@app.post("/api/seed/demo")
def seed_demo(req: SeedRequest):
    try:
        existing = get_documents("client", {}, 1)
        if existing:
            # Prevent duplicating demo data if clients already exist
            return {"status": "ok", "message": "Clients already exist; skipping seed.", "created": 0}

        # Create households
        household_names = [
            "Johnson Household",
            "Patel Family",
            "Nguyen Household",
            "Garcia Family",
            "O'Connor Household",
        ]
        household_ids: List[str] = []
        risk_profiles = ["Conservative", "Moderate", "Aggressive"]
        for i, name in enumerate(household_names):
            hid = create_document(
                "household",
                {"name": name, "risk_profile": _random_pick(risk_profiles, i)},
            )
            household_ids.append(hid)
            _log_compliance("create_document", "household", hid, ["auto-log", "seed"], context={"seed": True})

        # Client names and distribution of AUM
        first_names = [
            "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn", "Peyton", "Dakota",
            "Jamie", "Cameron", "Robin", "Skyler", "Kendall", "Emerson", "Rowan", "Hayden", "Sage", "Reese",
        ]
        last_names = [
            "Smith", "Lee", "Brown", "Wilson", "Martinez", "Clark", "Lopez", "Davis", "Lewis", "Walker",
        ]
        account_types = ["taxable", "ira", "roth_ira", "401k", "529", "trust"]
        custodians = ["Fidelity", "Schwab", "Vanguard", "Pershing", "TD Ameritrade"]

        created_clients = 0
        for i in range(req.count_clients):
            fn = first_names[i % len(first_names)]
            ln = last_names[i % len(last_names)]
            email = f"{fn.lower()}.{ln.lower()}@example.com"
            hid = _random_pick(household_ids, i)

            client_id = create_document(
                "client",
                {"first_name": fn, "last_name": ln, "email": email, "household_id": hid, "kyc_status": "approved"},
            )
            created_clients += 1
            _log_compliance("create_document", "client", client_id, ["auto-log", "seed"], context={"seed": True})

            # Assign 1-3 accounts per client with varying balances (AUM)
            num_accounts = (i % 3) + 1
            for j in range(num_accounts):
                balance = float(25000 * ((i + 1) ** 1.1)) * (0.6 + 0.4 * (j / max(1, num_accounts - 1)))
                acc_type = account_types[(i + j) % len(account_types)]
                custodian = custodians[(i + j) % len(custodians)]
                masked = f"****{(1000 + (i * 7 + j) % 9000)}"

                account_id = create_document(
                    "account",
                    {
                        "client_id": client_id,
                        "household_id": hid,
                        "account_type": acc_type,
                        "custodian": custodian,
                        "account_number_masked": masked,
                        "balance": round(balance, 2),
                        "holdings": [
                            {"ticker": "VTI", "weight": 0.5},
                            {"ticker": "BND", "weight": 0.4},
                            {"ticker": "CASH", "weight": 0.1},
                        ],
                    },
                )
                _log_compliance("create_document", "account", account_id, ["auto-log", "seed"], context={"seed": True})

        return {"status": "ok", "message": "Demo data created", "created": created_clients}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
