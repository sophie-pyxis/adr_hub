"""
Test suite for squads API endpoints.
"""

import pytest


def test_create_squad(client, test_squad_data):
    """Test creating a new squad."""
    response = client.post("/api/squads/", json=test_squad_data)

    assert response.status_code == 201
    data = response.json()

    assert data["squad_code"] == test_squad_data["squad_code"]
    assert data["name"] == test_squad_data["name"]
    assert data["tech_lead"] == test_squad_data["tech_lead"]
    assert data["status"] == test_squad_data["status"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_squad_duplicate_code(client, test_squad_data):
    """Test creating squad with duplicate squad_code."""
    # Create first squad
    response1 = client.post("/api/squads/", json=test_squad_data)
    assert response1.status_code == 201

    # Try to create second squad with same code
    response2 = client.post("/api/squads/", json=test_squad_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_create_squad_invalid_code(client):
    """Test creating squad with invalid squad_code."""
    invalid_data = {
        "squad_code": "ab",  # Too short (less than 3 characters)
        "name": "AI Engineering Squad",
        "tech_lead": "Carlos Mendes",
        "status": "active",
    }

    response = client.post("/api/squads/", json=invalid_data)
    assert response.status_code == 422  # FastAPI returns 422 for validation errors
    # Check that the error is about squad_code
    error_detail = response.json()["detail"]
    # The error detail is a list for validation errors
    if isinstance(error_detail, list):
        assert any("squad_code" in str(error).lower() for error in error_detail)
    else:
        assert "squad_code" in error_detail.lower()


def test_list_squads(client, test_squad_data):
    """Test listing all squads."""
    # Create a squad first
    create_response = client.post("/api/squads/", json=test_squad_data)
    assert create_response.status_code == 201

    # List squads
    response = client.get("/api/squads/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    squad = data[0]
    assert squad["squad_code"] == test_squad_data["squad_code"]
    assert squad["name"] == test_squad_data["name"]


def test_list_squads_filter_by_status(client):
    """Test listing squads filtered by status."""
    # Create active squad
    active_squad = {
        "squad_code": "active-squad",
        "name": "Active Squad",
        "tech_lead": "Tech Lead 1",
        "status": "active",
    }
    client.post("/api/squads/", json=active_squad)

    # Create discontinued squad
    discontinued_squad = {
        "squad_code": "discontinued-squad",
        "name": "Discontinued Squad",
        "tech_lead": "Tech Lead 2",
        "status": "discontinued",
        "discontinued_reason": "Project completed",
    }
    client.post("/api/squads/", json=discontinued_squad)

    # List active squads
    response = client.get("/api/squads/?status=active")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["squad_code"] == "active-squad"
    assert data[0]["status"] == "active"


def test_get_squad(client, test_squad_data):
    """Test getting a squad by code."""
    # Create squad first
    create_response = client.post("/api/squads/", json=test_squad_data)
    assert create_response.status_code == 201

    # Get squad
    response = client.get(f"/api/squads/{test_squad_data['squad_code']}")
    assert response.status_code == 200

    data = response.json()
    assert data["squad_code"] == test_squad_data["squad_code"]
    assert data["name"] == test_squad_data["name"]


def test_get_squad_not_found(client):
    """Test getting a non-existent squad."""
    response = client.get("/api/squads/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_squad(client, test_squad_data):
    """Test updating a squad."""
    # Create squad first
    create_response = client.post("/api/squads/", json=test_squad_data)
    assert create_response.status_code == 201

    # Update squad
    update_data = {
        "name": "Updated AI Engineering Squad",
        "tech_lead": "Updated Tech Lead",
    }

    response = client.patch(
        f"/api/squads/{test_squad_data['squad_code']}", json=update_data
    )
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["tech_lead"] == update_data["tech_lead"]
    assert data["squad_code"] == test_squad_data["squad_code"]  # Unchanged


def test_update_squad_status_to_discontinued(client, test_squad_data):
    """Test updating squad status to discontinued with reason."""
    # Create squad first
    create_response = client.post("/api/squads/", json=test_squad_data)
    assert create_response.status_code == 201

    # Try to update to discontinued without reason
    update_data = {"status": "discontinued"}
    response = client.patch(
        f"/api/squads/{test_squad_data['squad_code']}", json=update_data
    )
    assert response.status_code == 400  # Service validation returns 400
    assert "discontinued_reason" in response.json()["detail"].lower()

    # Update with reason
    update_data["discontinued_reason"] = "Project completed"
    response = client.patch(
        f"/api/squads/{test_squad_data['squad_code']}", json=update_data
    )
    assert response.status_code == 200
    assert response.json()["status"] == "discontinued"


def test_delete_squad(client, test_squad_data):
    """Test soft deleting a squad."""
    # Create squad first
    create_response = client.post("/api/squads/", json=test_squad_data)
    assert create_response.status_code == 201

    # Delete squad
    response = client.delete(f"/api/squads/{test_squad_data['squad_code']}")
    assert response.status_code == 204

    # Verify squad is marked as discontinued
    get_response = client.get(f"/api/squads/{test_squad_data['squad_code']}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "discontinued"
    assert "deleted_at" in get_response.json()


def test_delete_squad_not_found(client):
    """Test deleting a non-existent squad."""
    response = client.delete("/api/squads/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
