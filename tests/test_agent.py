from lark.agent import respond


def test_budget_is_required_before_a_plan():
    result = respond("Boston to Lisbon for two, 5 nights in June")
    assert result["plan"] is None
    assert result["status"] == "asking"
    assert "cost" in result["reply"].lower()


def test_budget_follow_up_builds_a_fitting_lisbon_trip():
    first = respond("Boston to Lisbon for two, 5 nights in June")
    result = respond("$3200", first["state"])
    plan = result["plan"]
    assert plan is not None
    assert plan["fits"] is True
    assert plan["city"] == "Lisbon"
    assert plan["travelers"] == 2
    assert plan["nights"] == 5
    assert plan["total"] <= 3200
    assert plan["flights"] and plan["stays"] and len(plan["activities"]) >= 2


def test_one_sentence_lisbon_trip():
    result = respond("Two of us, Boston to Lisbon, 5 nights in June, $3200")
    assert result["plan"]["fits"] is True
    assert result["plan"]["origin"] == "Boston"


def test_new_orleans_weekend_fits():
    result = respond("Solo from Chicago, a weekend in New Orleans, under $900")
    plan = result["plan"]
    assert plan["city"] == "New Orleans"
    assert plan["travelers"] == 1
    assert plan["nights"] == 2
    assert plan["fits"] is True
    assert plan["total"] <= 900


def test_tokyo_food_trip():
    result = respond("From San Francisco to Tokyo in April, 6 nights, two people, food first, $4500")
    plan = result["plan"]
    assert plan["city"] == "Tokyo"
    assert plan["nights"] == 6
    assert plan["travelers"] == 2
    assert plan["fits"] is True
    assert plan["meal_rate"] >= 58
    assert "food" in result["state"]["vibes"]


def test_cheaper_remix_drops_the_total():
    first = respond("Two of us, Boston to Lisbon, 5 nights in June, $3200")
    cheaper = respond("Make it cheaper", first["state"])
    assert cheaper["plan"]["total"] <= first["plan"]["total"]
    assert cheaper["plan"]["fits"] is True


def test_unknown_city_does_not_invent_a_trip():
    result = respond("Take me to Bali in March, $4000 from Boston, 6 nights")
    assert result["plan"] is None
    assert "Bali" in result["reply"]


def test_same_city_is_refused():
    result = respond("Lisbon to Lisbon, $2000, a week in May")
    assert result["plan"] is None


def test_per_person_budget_multiplies():
    result = respond("Boston to Lisbon, two people, 4 nights in October, $1800 per person")
    assert result["plan"]["budget"] == 3600
    assert result["plan"]["travelers"] == 2
