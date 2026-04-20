import os
import zipfile
import tempfile
import urllib.request

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import geopandas as gpd
import pgeocode
from sqlalchemy import create_engine, text

ENGINE = create_engine(
    "postgresql+psycopg2://liml@localhost/arizona_list",
    connect_args={"client_encoding": "utf8"},
)
OUT = "analysis/figures"
os.makedirs(OUT, exist_ok=True)

# ── Load data from PostgreSQL ──────────────────────────────────────────────
with ENGINE.connect() as conn:
    contributions = pd.read_sql(text("""
        SELECT co.contribution_id, co.amount, co.date_received,
               c.vanid, c.first, c.last, c.zip, c.city, c.county, c.state
        FROM contributions co
        JOIN contacts c ON co.vanid = c.vanid
        WHERE co.amount > 0
    """), conn)

    top10_individuals = pd.read_sql(text("""
        SELECT co.contribution_id, co.amount, co.date_received,
               co.payment_method, co.source_code,
               COALESCE(NULLIF(TRIM(c.official_name), ''),
                        NULLIF(TRIM(c.first || ' ' || c.last), ''),
                        'Unknown') AS donor_name,
               c.city, c.state, c.zip, c.type_of_contact
        FROM contributions co
        JOIN contacts c ON co.vanid = c.vanid
        WHERE co.amount > 0
        ORDER BY co.amount DESC
        LIMIT 10
    """), conn)

print(f"Loaded {len(contributions):,} contributions")

# Clean zip codes (remove .0 suffix)
contributions["zip"] = contributions["zip"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5)
contributions["zip"] = contributions["zip"].where(contributions["zip"].str.match(r"^\d{5}$"), None)
contributions = contributions.dropna(subset=["zip"])

az = contributions[contributions["state"] == "AZ"].copy()
az["year"] = pd.to_datetime(az["date_received"], errors="coerce").dt.year
az = az[az["year"].between(2010, 2026)]

# ═══════════════════════════════════════════════════════════════════════════
# 1. TOP 20 ZIP CODES — horizontal bar chart
# ═══════════════════════════════════════════════════════════════════════════
zip_summary = (
    az.groupby("zip")
    .agg(total=("amount", "sum"), count=("amount", "count"))
    .reset_index()
    .sort_values("total", ascending=False)
    .head(20)
)

fig, ax = plt.subplots(figsize=(12, 8))
bars = ax.barh(zip_summary["zip"][::-1], zip_summary["total"][::-1],
               color=plt.cm.Blues(0.4 + 0.5 * zip_summary["total"][::-1] / zip_summary["total"].max()),
               edgecolor="white", linewidth=0.5)
ax.set_xlabel("Total Contribution Amount ($)", fontsize=11)
ax.set_title("Top 20 ZIP Codes by Total Contribution Amount", fontsize=14, fontweight="bold", pad=14)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K"))

# Annotate bars
for bar, (_, row) in zip(bars[::-1], zip_summary.iterrows()):
    ax.text(bar.get_width() + zip_summary["total"].max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"${row['total']:,.0f}  ({row['count']:,})", va="center", fontsize=8)

ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/top20_zip_codes.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ Saved: top20_zip_codes.png")

# ═══════════════════════════════════════════════════════════════════════════
# 2. BUBBLE MAP — donor locations by total giving (all states, all ZIP codes)
# ═══════════════════════════════════════════════════════════════════════════
all_zip_summary = (
    contributions.groupby("zip")
    .agg(total=("amount", "sum"), count=("amount", "count"))
    .reset_index()
)

nomi = pgeocode.Nominatim("us")
geo = nomi.query_postal_code(all_zip_summary["zip"].tolist())
zip_geo = all_zip_summary.copy()
zip_geo["lat"] = geo["latitude"].values
zip_geo["lon"] = geo["longitude"].values
zip_geo = zip_geo.dropna(subset=["lat", "lon"])
zip_geo = zip_geo[(zip_geo["lon"].between(-125, -66)) & (zip_geo["lat"].between(24, 50))]

# US states basemap (cached)
_states_zip = "/tmp/us_states.zip"
if not os.path.exists(_states_zip):
    urllib.request.urlretrieve(
        "https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_state_20m.zip",
        _states_zip,
    )
_tmpdir = tempfile.mkdtemp()
with zipfile.ZipFile(_states_zip) as z:
    z.extractall(_tmpdir)
_shp = next(f for f in os.listdir(_tmpdir) if f.endswith(".shp"))
conus = gpd.read_file(os.path.join(_tmpdir, _shp))
conus = conus[~conus["STATEFP"].isin(["02", "15", "60", "66", "69", "72", "78"])]

# Marker size: log-scaled to donation total
log_total = np.log10(zip_geo["total"].clip(lower=1))
zip_geo["size"] = 2 + 80 * ((log_total - log_total.min()) / (log_total.max() - log_total.min())) ** 1.5

# Color tier by donation total
TIERS = [
    (1_000,   "#b0b7bf", 0.30, "< $1,000"),
    (10_000,  "#f4a55a", 0.65, "$1,000 – $9,999"),
    (50_000,  "#e8691e", 0.82, "$10,000 – $49,999"),
    (100_000, "#c0392b", 0.92, "$50,000 – $99,999"),
    (np.inf,  "#7b0e0e", 1.00, "≥ $100,000"),
]

def assign_tier(total):
    for threshold, color, alpha, _ in TIERS:
        if total < threshold:
            return color, alpha
    return TIERS[-1][1], TIERS[-1][2]

zip_geo[["color", "alpha"]] = zip_geo["total"].apply(
    lambda t: pd.Series(assign_tier(t))
)
zip_geo["tier_order"] = pd.cut(
    zip_geo["total"],
    bins=[0, 1_000, 10_000, 50_000, 100_000, np.inf],
    labels=[0, 1, 2, 3, 4],
).astype(int)
zip_geo = zip_geo.sort_values("tier_order")

fig, ax = plt.subplots(figsize=(15, 9.5), dpi=180)
fig.patch.set_facecolor("white")
conus.plot(ax=ax, color="#f0ede8", edgecolor="#c8c0b8", linewidth=0.6, zorder=1)

for _, row in zip_geo.iterrows():
    ax.scatter(row["lon"], row["lat"], s=row["size"], c=row["color"], alpha=row["alpha"],
               linewidths=0.4 if row["total"] >= 10_000 else 0,
               edgecolors="white", zorder=2 + row["tier_order"])

ax.set_xlim(-125, -66)
ax.set_ylim(24.5, 49.5)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("Donor Locations by Total Giving", fontsize=17, fontweight="bold",
             color="#1a1a1a", loc="left", pad=14, x=0.01)
ax.text(0.01, 0.96, f"n = {len(zip_geo):,} ZIP codes", transform=ax.transAxes,
        fontsize=9, color="#666666", va="top")

handles = [
    mpatches.Patch(facecolor=color, alpha=alpha, edgecolor="#999", linewidth=0.5, label=label)
    for _, color, alpha, label in TIERS
]
leg = ax.legend(handles=handles, title="Total Giving (per ZIP)", title_fontsize=8.5,
                fontsize=8, loc="lower left", framealpha=0.95,
                edgecolor="#cccccc", fancybox=False, borderpad=0.8)
leg._legend_box.align = "left"

plt.tight_layout(pad=0.3)
plt.savefig(f"{OUT}/donor_location_map.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close()
print("✓ Saved: donor_location_map.png")

# ═══════════════════════════════════════════════════════════════════════════
# 3. TIME SERIES — Line chart (yearly amount) + Bar chart (yearly count) + Table
# ═══════════════════════════════════════════════════════════════════════════
yearly = (
    az.groupby("year")
    .agg(total_amount=("amount", "sum"), n_donations=("amount", "count"))
    .reset_index()
    .sort_values("year")
)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle("Donation Trends Over Time (Arizona)", fontsize=14, fontweight="bold")

# Line chart — dollar amount
ax1 = axes[0]
ax1.plot(yearly["year"], yearly["total_amount"], marker="o", linewidth=2.5,
         color="#2a9d8f", markersize=7, markerfacecolor="white", markeredgewidth=2)
ax1.fill_between(yearly["year"], yearly["total_amount"], alpha=0.12, color="#2a9d8f")
ax1.set_title("Total Donation Amount by Year", fontsize=12, fontweight="bold")
ax1.set_xlabel("Year")
ax1.set_ylabel("Amount ($)")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K"))
ax1.grid(alpha=0.3)
ax1.set_xticks(yearly["year"])
ax1.tick_params(axis="x", rotation=45)
for x, y in zip(yearly["year"], yearly["total_amount"]):
    ax1.annotate(f"${y/1e3:.0f}K", (x, y), textcoords="offset points",
                 xytext=(0, 10), ha="center", fontsize=7.5)

# Bar chart — donation count
ax2 = axes[1]
colors = ["#e76f51" if y == yearly["n_donations"].max() else "#f4a261" for y in yearly["n_donations"]]
bars = ax2.bar(yearly["year"], yearly["n_donations"], color=colors, edgecolor="white", linewidth=0.5)
ax2.set_title("Number of Donations by Year", fontsize=12, fontweight="bold")
ax2.set_xlabel("Year")
ax2.set_ylabel("# Donations")
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax2.grid(axis="y", alpha=0.3)
ax2.set_xticks(yearly["year"])
ax2.tick_params(axis="x", rotation=45)
for bar, val in zip(bars, yearly["n_donations"]):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 30,
             f"{val:,}", ha="center", fontsize=8)

plt.tight_layout()
plt.savefig(f"{OUT}/donation_trends.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ Saved: donation_trends.png")

# Table
fig, ax = plt.subplots(figsize=(10, len(yearly) * 0.5 + 1.5))
ax.axis("off")
table_data = yearly.copy()
table_data["total_amount"] = table_data["total_amount"].map(lambda x: f"${x:,.0f}")
table_data["n_donations"] = table_data["n_donations"].map(lambda x: f"{x:,}")
table_data["year"] = table_data["year"].astype(int)
table = ax.table(
    cellText=table_data.values,
    colLabels=["Year", "Total Amount", "# Donations"],
    cellLoc="center", loc="center",
    bbox=[0, 0, 1, 1],
)
table.auto_set_font_size(False)
table.set_fontsize(10)
for (r, c), cell in table.get_celld().items():
    if r == 0:
        cell.set_facecolor("#2a9d8f")
        cell.set_text_props(color="white", fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#f0f7f6")
    cell.set_edgecolor("#cccccc")
ax.set_title("Yearly Donation Summary", fontsize=13, fontweight="bold", pad=12)
plt.tight_layout()
plt.savefig(f"{OUT}/donation_trends_table.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ Saved: donation_trends_table.png")

# ═══════════════════════════════════════════════════════════════════════════
# 4. TOP 10 LARGEST INDIVIDUAL DONATIONS
# ═══════════════════════════════════════════════════════════════════════════
top10 = top10_individuals.copy()
top10["zip"] = top10["zip"].astype(str).str.replace(r"\.0$", "", regex=True)
top10["name"] = top10["donor_name"]
top10["date_received"] = pd.to_datetime(top10["date_received"], errors="coerce").dt.strftime("%Y-%m-%d")
top10["amount_fmt"] = top10["amount"].map(lambda x: f"${x:,.2f}")
top10["rank"] = range(1, 11)

fig, ax = plt.subplots(figsize=(14, 5))
ax.axis("off")
display_cols = ["rank", "name", "amount_fmt", "date_received", "city", "state", "payment_method"]
col_labels = ["Rank", "Donor Name", "Amount", "Date", "City", "State", "Payment Method"]
table = ax.table(
    cellText=top10[display_cols].values,
    colLabels=col_labels,
    cellLoc="center", loc="center",
    bbox=[0, 0, 1, 1],
)
table.auto_set_font_size(False)
table.set_fontsize(9)
for (r, c), cell in table.get_celld().items():
    if r == 0:
        cell.set_facecolor("#e76f51")
        cell.set_text_props(color="white", fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#fff3f0")
    cell.set_edgecolor("#dddddd")
    if c == 2 and r > 0:
        cell.set_text_props(fontweight="bold", color="#c0392b")
ax.set_title("Top 10 Largest Individual Donations", fontsize=13, fontweight="bold", pad=12)
plt.tight_layout()
plt.savefig(f"{OUT}/top10_donations.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ Saved: top10_donations.png")

print("\n=== Top 10 Largest Donations ===")
print(top10[["rank","name","amount","date_received","city","state"]].to_string(index=False))
