"""Generate new figures for the technical summary report."""
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
from sqlalchemy import create_engine, text

FIGURE_DIR = Path(__file__).parent / "figures"
FIGURE_DIR.mkdir(exist_ok=True)

ENGINE = create_engine(
    "postgresql+psycopg2://liml@localhost/arizona_list",
    connect_args={"client_encoding": "utf8"},
)

def run(sql):
    with ENGINE.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql))]

# ── 1. Top 20 ZIP codes (both charts use identical SQL logic) ─────────────────
# Same logic as original: contacts.zip (one row per person), AZ only, 2010-2026.
# ZIP field stored as "85718.0" — strip the .0 and zero-pad to 5 digits.
ZIP_BASE_SQL = """
    SELECT
        LPAD(SPLIT_PART(c.zip::text, '.', 1), 5, '0') AS zip,
        SUM(co.amount)  AS total_amount,
        COUNT(*)        AS gift_count
    FROM contributions co
    JOIN contacts c ON co.vanid = c.vanid
    WHERE co.amount > 0
      AND c.state = 'AZ'
      AND c.zip IS NOT NULL
      AND SPLIT_PART(c.zip::text, '.', 1) ~ '^[0-9]+$'
      AND EXTRACT(YEAR FROM co.date_received) BETWEEN 2010 AND 2026
      {extra_where}
    GROUP BY LPAD(SPLIT_PART(c.zip::text, '.', 1), 5, '0')
    ORDER BY total_amount DESC
    LIMIT 20
"""

pam_vanid_rows = run("""
    SELECT vanid FROM contacts
    WHERE lower(official_name) LIKE '%pam grissom%'
       OR (lower(last) = 'grissom' AND lower(first) LIKE 'pam%')
""")
pam_vanids = [str(r["vanid"]) for r in pam_vanid_rows]
excl_where = f"AND co.vanid NOT IN ({','.join(pam_vanids)})" if pam_vanids else ""

def zip_bar_chart(rows, title, filename):
    zips    = [r["zip"] for r in rows]
    amounts = [float(r["total_amount"]) for r in rows]
    max_amt = max(amounts)
    _, ax = plt.subplots(figsize=(12, 8))
    bar_colors = plt.cm.Blues(
        [0.4 + 0.5 * a / max_amt for a in amounts[::-1]])
    bars = ax.barh(zips[::-1], amounts[::-1], color=bar_colors, edgecolor="white", linewidth=0.5)
    for bar, amt in zip(bars, amounts[::-1]):
        ax.text(bar.get_width() + max_amt * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"${amt:,.0f}", va="center", fontsize=8)
    ax.set_xlabel("Total Contribution Amount ($)", fontsize=11)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=14)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K"))
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {filename}")

zip_all  = run(ZIP_BASE_SQL.format(extra_where=""))
zip_excl = run(ZIP_BASE_SQL.format(extra_where=excl_where))

zip_bar_chart(zip_all,  "Top 20 ZIP Codes by Total Contribution Amount",
              "top20_zip_codes.png")
zip_bar_chart(zip_excl, "Top 20 ZIP Codes by Total Contribution Amount\n(Excluding Pam Grissom)",
              "top20_zip_codes_excl_grissom.png")

# ── Helper: original small-multiples style ───────────────────────────────────
def small_multiples(pivot_data, title, fname, color, dollar=False, top_n=20, ncols=4):
    """pivot_data: dict of {(entity, year): value}"""
    # Compute totals to pick top_n
    entity_totals = {}
    for (entity, _), v in pivot_data.items():
        entity_totals[entity] = entity_totals.get(entity, 0) + v
    entities = sorted(entity_totals, key=entity_totals.get, reverse=True)[:top_n]

    all_years = sorted({yr for (_, yr) in pivot_data})

    nrows = (len(entities) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, nrows * 3), sharey=False)
    axes = axes.flatten()
    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.01)

    for i, entity in enumerate(entities):
        ax = axes[i]
        vals = [pivot_data.get((entity, y), 0) for y in all_years]
        ax.bar(all_years, vals, color=color, alpha=0.8, edgecolor="white", linewidth=0.4)
        ax.set_title(entity, fontsize=10, fontweight="bold")
        ax.tick_params(axis="x", rotation=45, labelsize=7)
        ax.tick_params(axis="y", labelsize=7)
        if dollar:
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
        ax.grid(axis="y", alpha=0.3)

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    plt.tight_layout()
    path = FIGURE_DIR / fname
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {fname}")

# ── 2. City over time ─────────────────────────────────────────────────────────
city_rows = run("""
    SELECT
        INITCAP(TRIM(a.city))                     AS city,
        EXTRACT(YEAR FROM co.date_received)::INT  AS year,
        COUNT(*)                                  AS gift_count,
        SUM(co.amount)                            AS total_amount
    FROM contributions co
    JOIN contacts c  ON co.vanid = c.vanid
    JOIN addresses a ON co.vanid = a.vanid AND a.is_best_address = TRUE
    WHERE co.amount > 0
      AND TRIM(COALESCE(a.city, '')) <> ''
      AND a.state = 'AZ'
    GROUP BY INITCAP(TRIM(a.city)), EXTRACT(YEAR FROM co.date_received)::INT
""")

city_year_count  = {(r["city"], r["year"]): r["gift_count"]       for r in city_rows}
city_year_amount = {(r["city"], r["year"]): float(r["total_amount"]) for r in city_rows}

small_multiples(city_year_count,  "Number of Donations by City Over Time (Top 20)",
                "city_donations_count.png",  color="#2a9d8f", dollar=False, top_n=20)
small_multiples(city_year_amount, "Total Donation Amount by City Over Time (Top 20)",
                "city_donations_amount.png", color="#2a9d8f", dollar=True,  top_n=20)

# ── 3. County over time ───────────────────────────────────────────────────────
county_rows = run("""
    SELECT
        INITCAP(TRIM(c.county))                   AS county,
        EXTRACT(YEAR FROM co.date_received)::INT  AS year,
        COUNT(*)                                  AS gift_count,
        SUM(co.amount)                            AS total_amount
    FROM contributions co
    JOIN contacts c ON co.vanid = c.vanid
    WHERE co.amount > 0
      AND TRIM(COALESCE(c.county, '')) <> ''
    GROUP BY INITCAP(TRIM(c.county)), EXTRACT(YEAR FROM co.date_received)::INT
""")

county_year_count  = {(r["county"], r["year"]): r["gift_count"]       for r in county_rows}
county_year_amount = {(r["county"], r["year"]): float(r["total_amount"]) for r in county_rows}

small_multiples(county_year_count,  "Number of Donations by County Over Time",
                "county_donations_count.png",  color="#e76f51", dollar=False)
small_multiples(county_year_amount, "Total Donation Amount by County Over Time",
                "county_donations_amount.png", color="#e76f51", dollar=True)

print("Done.")
