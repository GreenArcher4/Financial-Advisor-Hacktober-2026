import pytest

from app.finance import calculate_net_returns, compare_mmfs


def test_compare_mmfs_filters_by_starting_amount():
    funds = compare_mmfs(1000)
    assert [fund["name"] for fund in funds] == [
        "Etica MMF",
        "Cytonn MMF",
        "Ziidi MMF",
    ]
    assert all(fund["min_deposit"] <= 1000 for fund in funds)


def test_compare_mmfs_does_not_expose_mutable_database_records():
    funds = compare_mmfs(100)
    funds[0]["name"] = "Changed"
    assert compare_mmfs(100)[0]["name"] == "Etica MMF"


def test_calculate_net_returns_deducts_tax_from_interest():
    result = calculate_net_returns(1000, 500, 12, 10.5)
    assert result["total_contributions_kes"] == 7000
    assert result["projected_gross_kes"] > result["projected_net_kes"] > 7000
    assert result["withholding_tax_kes"] > 0
    assert result["net_interest_kes"] == pytest.approx(
        result["projected_net_kes"] - 7000
    )
    assert result["effective_net_annual_rate_percent"] == 8.93


def test_calculate_net_returns_with_zero_rate():
    result = calculate_net_returns(1000, 500, 12, 0)
    assert result["projected_net_kes"] == 7000
    assert result["withholding_tax_kes"] == 0


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ((-1, 0, 12, 10), "Principal"),
        ((100, -1, 12, 10), "top-up"),
        ((100, 0, 0, 10), "Duration"),
        ((100, 0, 12, 101), "rate"),
    ],
)
def test_calculate_net_returns_rejects_invalid_values(args, message):
    with pytest.raises(ValueError, match=message):
        calculate_net_returns(*args)


def test_compare_mmfs_rejects_negative_budget():
    with pytest.raises(ValueError, match="negative"):
        compare_mmfs(-1)
