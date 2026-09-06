from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from modules.users.presentation.router import router as users_router
from modules.accounts.presentation.router import router as accounts_router
from modules.accounts.presentation.router import user_accounts_router as user_accounts_router
from modules.transactions.presentation.router import router as transactions_router
from modules.categories.presentation.router import router as categories_router
from modules.tags.presentation.router import router as tags_router
from modules.payment_methods.presentation.router import router as payment_methods_router
from modules.budgets.presentation.router import router as budgets_router
from modules.limits.presentation.router import router as limits_router
from modules.notifications.presentation.router import router as notifications_router
from modules.transfers.presentation.router import router as transfers_router
from modules.loans.presentation.router import router as loans_router
from modules.debts.presentation.router import router as debts_router
from modules.recurring_expenses.presentation.router import router as recurring_expenses_router
from modules.audit_logs.presentation.router import router as audit_logs_router
from modules.conversations.presentation.router import router as conversations_router
from modules.auth.presentation.router import router as auth_router
from modules.reports.presentation.router import router as reports_router
from shared.errors import ConflictError, ValidationError

app = FastAPI(
    title="Gestión Financiera Personal API",
    version="0.1.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth routes (public)
app.include_router(auth_router)

# Protected routes
app.include_router(users_router)
app.include_router(accounts_router)
app.include_router(user_accounts_router)
app.include_router(transactions_router)
app.include_router(categories_router)
app.include_router(tags_router)
app.include_router(payment_methods_router)
app.include_router(budgets_router)
app.include_router(limits_router)
app.include_router(notifications_router)
app.include_router(transfers_router)
app.include_router(loans_router)
app.include_router(debts_router)
app.include_router(recurring_expenses_router)
app.include_router(audit_logs_router)
app.include_router(conversations_router)
app.include_router(reports_router)


@app.exception_handler(ValidationError)
async def validation_error_handler(_: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={"code": exc.code, "message": exc.message})


@app.exception_handler(ConflictError)
async def conflict_error_handler(_: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"code": exc.code, "message": exc.message})


@app.get("/health")
def health_check():
    return {"status": "ok"}
