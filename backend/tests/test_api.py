import os

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "data")


def test_health(client):
    assert client.get("/api/health").json()["database"] is True


def test_register_validation_and_duplicates(client, new_user):
    bad = client.post("/api/auth/register", json={"name": "A", "email": "a@example.com", "password": "short", "confirm_password": "short"})
    assert bad.status_code == 422
    mismatch = client.post("/api/auth/register", json={"name": "A", "email": "b@example.com", "password": "Passw0rdX", "confirm_password": "Passw0rdY"})
    assert mismatch.status_code == 422 and "match" in mismatch.json()["detail"]
    dup = client.post("/api/auth/register", json={"name": "A", "email": new_user["email"], "password": "Passw0rdX", "confirm_password": "Passw0rdX"})
    assert dup.status_code == 409


def test_login_me_logout(client, new_user):
    r = client.post("/api/auth/login", json={"email": new_user["email"], "password": new_user["password"]})
    assert r.status_code == 200
    h = {"Authorization": "Bearer " + r.json()["access_token"]}
    assert client.get("/api/auth/me", headers=h).json()["email"] == new_user["email"]
    assert client.post("/api/auth/login", json={"email": new_user["email"], "password": "wrong1234"}).status_code == 401
    assert client.post("/api/auth/logout", headers=h).status_code == 204
    assert client.get("/api/auth/me", headers=h).status_code == 401  # token revoked


def test_protected_routes_require_auth(client):
    for path in ("/api/profile", "/api/history", "/api/trends", "/api/settings", "/api/logs"):
        assert client.get(path).status_code == 401


def test_onboarding_profile_and_goals(client, new_user):
    h = new_user["headers"]
    r = client.put("/api/profile", headers=h, json={"allergies": ["Peanut", "Kiwi"], "intolerances": ["Lactose"],
                                                    "dietary_preferences": ["Vegetarian"], "goals": ["reduce_sodium"],
                                                    "complete_onboarding": True})
    assert r.status_code == 200 and r.json()["onboarding_complete"] is True
    assert client.get("/api/auth/me", headers=h).json()["onboarding_complete"] is True
    goals = client.get("/api/goals", headers=h).json()
    assert [g["goal_type"] for g in goals if g["active"]] == ["reduce_sodium"]
    assert client.put("/api/profile", headers=h, json={"goals": ["cure_everything"]}).status_code == 422


def test_scan_analyze_log_history_flow(client, new_user):
    h = new_user["headers"]
    client.put("/api/profile", headers=h, json={"allergies": ["Peanut"], "intolerances": ["Lactose"],
                                                "dietary_preferences": ["Vegetarian"], "complete_onboarding": True})
    with open(os.path.join(DATA, "sample_labels", "chococrunch_biscuits.jpg"), "rb") as f:
        o = client.post("/api/ocr/extract", headers=h, files={"image": ("label.jpg", f, "image/jpeg")})
    assert o.status_code == 200, o.text
    o = o.json()
    assert "Peanut traces" in o["ingredients"]
    a = client.post("/api/analysis/analyze", headers=h, json={
        "input_method": "scan", "food_name": o["food_name"], "ingredients": o["ingredients"],
        "nutrition": {k: v for k, v in o["nutrition"].items()}, "allergen_statements": o["allergen_statements"],
        "ocr_confidence": o["confidence"]}).json()
    assert a["risk_level"] == "HIGH"
    assert "Peanut traces were detected and match your peanut allergy profile." in a["explanation"]
    assert len(a["alternatives"]) >= 2
    l = client.post("/api/logs", headers=h, json={"scan_id": a["scan_id"], "meal_type": "snack", "quantity": 2})
    assert l.status_code == 201 and l.json()["message"] == "Added to your diet history."
    assert l.json()["nutrition"]["sodium"] == 240  # 2 servings x 120 mg
    hist = client.get("/api/history?risk=HIGH", headers=h).json()
    assert hist["total"] == 1 and hist["items"][0]["food_name"] == a["food_name"]
    d = client.get(f"/api/history/{hist['items'][0]['log_id']}", headers=h).json()
    assert d["analysis"]["explanation"] == a["explanation"]
    # another user cannot read it
    other = client.post("/api/auth/register", json={"name": "O", "email": "other_x@example.com", "password": "Passw0rdX", "confirm_password": "Passw0rdX"}).json()
    oh = {"Authorization": "Bearer " + other["access_token"]}
    assert client.get(f"/api/analysis/{a['scan_id']}", headers=oh).status_code == 404
    assert client.get(f"/api/history/{d['log_id']}", headers=oh).status_code == 404


def test_upload_rejects_non_images(client, new_user):
    r = client.post("/api/ocr/extract", headers=new_user["headers"], files={"image": ("x.exe", b"MZ\x90\x00binary", "application/octet-stream")})
    assert r.status_code == 422 and "JPEG, PNG or WEBP" in r.json()["detail"]


def test_manual_requires_ingredients(client, new_user):
    r = client.post("/api/analysis/analyze", headers=new_user["headers"], json={"input_method": "manual", "food_name": "Soup", "ingredients": []})
    assert r.status_code == 422


def test_trends_insufficient_for_new_user(client, new_user):
    t = client.get("/api/trends?window=15", headers=new_user["headers"]).json()
    assert t["status"] == "insufficient" and t["alerts"] == []


def test_demo_trends_15_and_30(client, demo_headers):
    for w in (15, 30):
        t = client.get(f"/api/insights/{w}-day", headers=demo_headers).json()
        assert t["status"] == "trend"
        assert "Your recent food logs show a repeated high-sodium pattern." in [a["message"] for a in t["alerts"]]
        assert {m["key"] for m in t["metrics"]} >= {"added_sugar", "sodium", "fiber", "fruit_veg", "processed", "protein"}


def test_search_and_alternatives_exist(client, demo_headers):
    import json
    subs = json.load(open(os.path.join(DATA, "substitutions.json")))
    names = {n for group in list(subs["by_food_keyword"].values()) + list(subs["by_conflict"].values()) for n, _ in group}
    from app.data.food_catalog import all_foods
    known = {f["name"] for f in all_foods()}
    assert names <= known, names - known
    r = client.get("/api/foods/search?q=dosa", headers=demo_headers).json()
    assert any("Dosa" in x["name"] for x in r["results"])


def test_clear_history_requires_confirmation(client, new_user):
    h = new_user["headers"]
    assert client.post("/api/logs/clear", headers=h, json={"confirm_text": "nope"}).status_code == 422
    assert client.post("/api/logs/clear", headers=h, json={"confirm_text": "CLEAR"}).status_code == 200


def test_delete_account(client, new_user):
    h = new_user["headers"]
    assert client.post("/api/account/delete", headers=h, json={"password": "bad", "confirm_text": "DELETE"}).status_code == 403
    assert client.post("/api/account/delete", headers=h, json={"password": new_user["password"], "confirm_text": "DELETE"}).status_code == 204
    assert client.get("/api/auth/me", headers=h).status_code == 401


def test_demo_account_protected(client, demo_headers):
    r = client.post("/api/account/delete", headers=demo_headers, json={"password": "x", "confirm_text": "DELETE"})
    assert r.status_code == 403
