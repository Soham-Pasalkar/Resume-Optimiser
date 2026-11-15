import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_success(async_client: AsyncClient):
    """Test successful user registration creates user, profile, and returns tokens."""
    payload = {
        "email": "marcus.vance@example.com",
        "password": "Password123!",
        "full_name": "Marcus Vance",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["email"] == "marcus.vance@example.com"
    assert data["user"]["full_name"] == "Marcus Vance"
    assert data["user"]["is_active"] is True
    assert data["user"]["profile"] is not None


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(async_client: AsyncClient):
    """Test registering an existing email address fails with 400 Bad Request."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Original User",
    }
    # First registration succeeds
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email fails
    res2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    """Test logging in with valid credentials issues JWT tokens."""
    # Register first
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "login.test@example.com",
            "password": "CorrectPassword123!",
            "full_name": "Login Tester",
        },
    )

    # Login with correct password
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "login.test@example.com",
            "password": "CorrectPassword123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "login.test@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password_fails(async_client: AsyncClient):
    """Test login with wrong password returns 401 Unauthorized."""
    # Register first
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong.pwd@example.com",
            "password": "RealPassword123!",
            "full_name": "Wrong Pwd User",
        },
    )

    # Attempt login with incorrect password
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong.pwd@example.com",
            "password": "WrongPassword999!",
        },
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_token_refresh_lifecycle(async_client: AsyncClient):
    """Test refreshing an access token using a valid refresh token."""
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh.test@example.com",
            "password": "Password123!",
            "full_name": "Refresh Tester",
        },
    )
    refresh_token = reg_res.json()["refresh_token"]

    # Exchange refresh token for new access token
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_get_my_profile_authenticated(async_client: AsyncClient):
    """Test /api/v1/users/me returns authenticated user profile."""
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "me.test@example.com",
            "password": "Password123!",
            "full_name": "Profile Owner",
        },
    )
    token = reg_res.json()["access_token"]

    response = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me.test@example.com"
    assert data["full_name"] == "Profile Owner"


@pytest.mark.asyncio
async def test_get_my_profile_unauthenticated_fails(async_client: AsyncClient):
    """Test /api/v1/users/me without token fails with 401 Unauthorized."""
    response = await async_client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_profile(async_client: AsyncClient):
    """Test updating user full_name and profile metadata via PUT /api/v1/users/me."""
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "update.test@example.com",
            "password": "Password123!",
            "full_name": "Before Update",
        },
    )
    token = reg_res.json()["access_token"]

    update_payload = {
        "full_name": "After Update",
        "profile": {
            "headline": "Senior Go & Distributed Systems Engineer",
            "target_role_title": "Senior Backend Engineer",
            "target_seniority": "Senior",
            "years_of_experience": 5.5,
            "github_url": "https://github.com/marcusvance",
            "linkedin_url": "https://linkedin.com/in/marcusvance",
        },
    }

    response = await async_client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json=update_payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "After Update"
    assert data["profile"]["headline"] == "Senior Go & Distributed Systems Engineer"
    assert data["profile"]["target_seniority"] == "Senior"
    assert data["profile"]["years_of_experience"] == 5.5


@pytest.mark.asyncio
async def test_multi_tenant_isolation(async_client: AsyncClient):
    """Ensure User A cannot query or mutate User B's profile."""
    # Register User A
    res_a = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "user.a@example.com",
            "password": "PasswordA123!",
            "full_name": "User Alpha",
        },
    )
    token_a = res_a.json()["access_token"]

    # Register User B
    res_b = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "user.b@example.com",
            "password": "PasswordB123!",
            "full_name": "User Beta",
        },
    )
    token_b = res_b.json()["access_token"]

    # User A requests /me -> gets User A
    me_a = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert me_a.json()["email"] == "user.a@example.com"

    # User B requests /me -> gets User B
    me_b = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert me_b.json()["email"] == "user.b@example.com"
    assert me_a.json()["id"] != me_b.json()["id"]


@pytest.mark.asyncio
async def test_delete_account_gdpr(async_client: AsyncClient):
    """Test GDPR account deletion purges the user from the database."""
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "delete.me@example.com",
            "password": "Password123!",
            "full_name": "Delete Tester",
        },
    )
    token = reg_res.json()["access_token"]

    # Delete account
    del_res = await async_client.delete(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Subsequent /me query with deleted user's token fails with 401
    verify_res = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert verify_res.status_code == 401
