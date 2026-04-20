import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

OUT = "analysis/figures"
os.makedirs(OUT, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────
contrib = pd.read_csv(
    "All Contributions Ever 4.9.26.xls", encoding="utf-16", sep="\t",
    usecols=["VANID", "Date Received", "Amount", "Contribution Type"],
)
db = pd.read_csv(
    "Database List 4.9.26.xls", encoding="utf-16", sep="\t",
    usecols=["VANID", "City", "County", "State/Province"],
)

# ── Clean ──────────────────────────────────────────────────────────────────
contrib["VANID"] = contrib["VANID"].astype(str)
db["VANID"] = db["VANID"].astype(str)
contrib["Amount"] = pd.to_numeric(contrib["Amount"], errors="coerce")
contrib["Date Received"] = pd.to_datetime(contrib["Date Received"], errors="coerce")
contrib = contrib[contrib["Contribution Type"] == "Monetary Contribution"].copy()
contrib = contrib.dropna(subset=["Date Received", "Amount"])
contrib["Year"] = contrib["Date Received"].dt.year

# Keep AZ only; one address per VANID (preferred = first occurrence)
az = db[db["State/Province"] == "AZ"].drop_duplicates("VANID")

df = contrib.merge(az[["VANID", "City", "County"]], on="VANID", how="inner")
df["City"] = df["City"].str.strip().str.title()
df["County"] = df["County"].str.strip().str.title()

print(f"Merged rows: {len(df):,}  |  years: {df['Year'].min()}–{df['Year'].max()}")
print(f"Unique cities: {df['City'].nunique()}  |  counties: {df['County'].nunique()}")

# ── Helper ─────────────────────────────────────────────────────────────────


def small_multiples(pivot, title, fname, dollar=False, color="steelblue", top_n=None, ncols=3):
    if top_n:
        cols = pivot.sum().nlargest(top_n).index
        pivot = pivot[cols]
    items = pivot.columns.tolist()
    n = len(items)
    nrows = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(15, nrows * 3), sharey=False)
    axes = axes.flatten()
    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.01)

    for i, item in enumerate(items):
        ax = axes[i]
        vals = pivot[item]
        ax.bar(vals.index, vals.values, color=color, alpha=0.8, edgecolor="white", linewidth=0.4)
        ax.set_title(item, fontsize=10, fontweight="bold")
        ax.tick_params(axis="x", rotation=45, labelsize=7)
        ax.tick_params(axis="y", labelsize=7)
        if dollar:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
        ax.grid(axis="y", alpha=0.3)

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    plt.tight_layout()
    path = f"{OUT}/{fname}"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


# ── City charts (small multiples, teal, top 20) ───────────────────────────
city_count  = df.groupby(["Year", "City"]).size().unstack(fill_value=0)
city_amount = df.groupby(["Year", "City"])["Amount"].sum().unstack(fill_value=0)

small_multiples(city_count,  "Number of Donations by City Over Time (Top 20)",   "city_donations_count.png",  color="#2a9d8f", top_n=20, ncols=4)
small_multiples(city_amount, "Total Donation Amount by City Over Time (Top 20)",  "city_donations_amount.png", color="#2a9d8f", top_n=20, ncols=4, dollar=True)

# ── County charts (small multiples, coral) ────────────────────────────────
cty_count  = df.groupby(["Year", "County"]).size().unstack(fill_value=0)
cty_amount = df.groupby(["Year", "County"])["Amount"].sum().unstack(fill_value=0)

small_multiples(cty_count,  "Number of Donations by County Over Time",  "county_donations_count.png",  color="#e76f51")
small_multiples(cty_amount, "Total Donation Amount by County Over Time", "county_donations_amount.png", color="#e76f51", dollar=True)

# ── Summary tables ─────────────────────────────────────────────────────────
print("\n── Top 10 Cities (all-time donations) ──")
print(df.groupby("City")["Amount"].agg(["count","sum"]).rename(
    columns={"count":"# Donations","sum":"Total $"}).nlargest(10,"Total $").to_string())

print("\n── Top 10 Counties (all-time donations) ──")
print(df.groupby("County")["Amount"].agg(["count","sum"]).rename(
    columns={"count":"# Donations","sum":"Total $"}).nlargest(10,"Total $").to_string())
