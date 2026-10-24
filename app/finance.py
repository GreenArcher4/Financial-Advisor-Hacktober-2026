"""Demo financial tools for student-friendly MMF comparisons and projections."""

from decimal import Decimal, ROUND_HALF_UP
from typing import TypedDict


class MoneyMarketFund(TypedDict):
    name: str
    gross_yield: float
    net_yield: float
    min_deposit: int
    withdrawal: str


MMF_DATABASE: tuple[MoneyMarketFund, ...] = (
    {
        "name": "Etica MMF",
        "gross_yield": 10.1,
        "net_yield": 8.59,
        "min_deposit": 100,
        "withdrawal": "T+1",
    },
    {
        "name": "Cytonn MMF",
        "gross_yield": 11.0,
        "net_yield": 9.35,
        "min_deposit": 1000,
        "withdrawal": "T+1",
    },
    {
        "name": "Sanlam MMF",
        "gross_yield": 9.5,
        "net_yield": 8.08,
        "min_deposit": 2500,
        "withdrawal": "T+2",
    },
    {
        "name": "Ziidi MMF",
        "gross_yield": 7.0,
        "net_yield": 5.95,
        "min_deposit": 100,
        "withdrawal": "Instant",
    },
)


def compare_mmfs(min_deposit: int) -> list[MoneyMarketFund]:
    """Return demo funds whose minimum investment fits the starting amount."""
    if min_deposit < 0:
        raise ValueError("Minimum deposit must not be negative.")
    return [fund.copy() for fund in MMF_DATABASE if fund["min_deposit"] <= min_deposit]


def calculate_net_returns(
    principal: float,
    monthly_topup: float,
    months: int,
    gross_rate: float,
) -> dict[str, float]:
    """Project monthly contributions with 15% withholding tax on interest."""
    if principal < 0 or monthly_topup < 0:
        raise ValueError("Principal and monthly top-up must not be negative.")
    if months < 1:
        raise ValueError("Duration must be at least one month.")
    if not 0 <= gross_rate <= 100:
        raise ValueError("Gross annual rate must be between 0 and 100.")

    principal_value = Decimal(str(principal))
    topup_value = Decimal(str(monthly_topup))
    gross_monthly_rate = Decimal(str(gross_rate)) / 1200
    net_monthly_rate = gross_monthly_rate * Decimal("0.85")
    gross_balance = principal_value
    net_balance = principal_value

    for _ in range(months):
        gross_balance = gross_balance * (1 + gross_monthly_rate) + topup_value
        net_balance = net_balance * (1 + net_monthly_rate) + topup_value

    total_contributions = principal_value + topup_value * months
    gross_interest = gross_balance - total_contributions

    def money(value: Decimal) -> float:
        return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    return {
        "total_contributions_kes": money(total_contributions),
        "projected_gross_kes": money(gross_balance),
        "withholding_tax_kes": money(gross_interest - (net_balance - total_contributions)),
        "projected_net_kes": money(net_balance),
        "net_interest_kes": money(net_balance - total_contributions),
        "effective_net_annual_rate_percent": money(Decimal(str(gross_rate)) * Decimal("0.85")),
    }
