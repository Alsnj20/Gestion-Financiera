"""Integration tests for API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_register_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/register", json={
            "name": "Test User",
            "phone": "+51999888777",
            "email": "test@example.com",
            "password": "password123",
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["email"] == "test@example.com"


@pytest.mark.anyio
async def test_login_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First register
        await client.post("/auth/register", json={
            "name": "Login Test",
            "phone": "+51999888778",
            "email": "login@example.com",
            "password": "password123",
        })

        # Then login
        response = await client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


@pytest.mark.anyio
async def test_login_wrong_password():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First register
        await client.post("/auth/register", json={
            "name": "Wrong Pass",
            "phone": "+51999888779",
            "email": "wrong@example.com",
            "password": "password123",
        })

        # Then login with wrong password
        response = await client.post("/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401


@pytest.mark.anyio
async def test_refresh_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        register_response = await client.post("/auth/register", json={
            "name": "Refresh Test",
            "phone": "+51999888780",
            "email": "refresh@example.com",
            "password": "password123",
        })
        refresh_token = register_response.json()["refresh_token"]

        # Refresh
        response = await client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        assert "access_token" in response.json()


@pytest.mark.anyio
async def test_create_account_authenticated():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        register_response = await client.post("/auth/register", json={
            "name": "Account Test",
            "phone": "+51999888781",
            "email": "account@example.com",
            "password": "password123",
        })
        token = register_response.json()["access_token"]
        user_id = register_response.json()["user_id"]

        # Create account
        response = await client.post("/accounts", json={
            "user_id": user_id,
            "name": "Mi Cuenta",
            "type": "BANK",
            "currency": "PEN",
            "initial_balance": 1000,
        }, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 201


@pytest.mark.anyio
async def test_create_transaction_with_balance_update():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        register_response = await client.post("/auth/register", json={
            "name": "Balance Test",
            "phone": "+51999888782",
            "email": "balance@example.com",
            "password": "password123",
        })
        token = register_response.json()["access_token"]
        user_id = register_response.json()["user_id"]

        # Create account
        account_response = await client.post("/accounts", json={
            "user_id": user_id,
            "name": "Cuenta Balance",
            "type": "BANK",
            "currency": "PEN",
            "initial_balance": 1000,
        }, headers={"Authorization": f"Bearer {token}"})
        account_id = account_response.json()["id"]

        # Create income transaction
        income_response = await client.post("/transactions", json={
            "user_id": user_id,
            "account_id": account_id,
            "type": "INCOME",
            "amount": 500,
            "concepto": "Salario",
        }, headers={"Authorization": f"Bearer {token}"})
        assert income_response.status_code == 201

        # Create expense transaction
        expense_response = await client.post("/transactions", json={
            "user_id": user_id,
            "account_id": account_id,
            "type": "EXPENSE",
            "amount": 200,
            "concepto": "Compra",
        }, headers={"Authorization": f"Bearer {token}"})
        assert expense_response.status_code == 201


@pytest.mark.anyio
async def test_get_reports_summary():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        register_response = await client.post("/auth/register", json={
            "name": "Report Test",
            "phone": "+51999888783",
            "email": "report@example.com",
            "password": "password123",
        })
        token = register_response.json()["access_token"]
        user_id = register_response.json()["user_id"]

        # Get summary
        response = await client.get(
            f"/reports/summary?user_id={user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "net_balance" in data
