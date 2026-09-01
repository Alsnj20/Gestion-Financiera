from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from modules.users.presentation.router import router as users_router
from modules.accounts.presentation.router import router as accounts_router
from shared.errors import ConflictError, ValidationError

app = FastAPI(
    title="Gestión Financiera Personal API",
    version="0.1.0",
)

app.include_router(users_router)
app.include_router(accounts_router)


@app.exception_handler(ValidationError)
async def validation_error_handler(_: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={"code": exc.code, "message": exc.message})


@app.exception_handler(ConflictError)
async def conflict_error_handler(_: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"code": exc.code, "message": exc.message})


@app.get("/health")
def health_check():
    return {"status": "ok"}
