import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sqlalchemy import create_engine, text

ENGINE = create_engine(
    "postgresql+psycopg2://liml@localhost/arizona_list",
    connect_args={"client_encoding": "utf8"},
)
OUT = "analysis/figures"

# ── Load ───────────────────────────────────────────────────────────────────
with ENGINE.connect() as conn:
    rows = conn.execute(text("""
        SELECT c.state,
               EXTRACT(YEAR FROM co.date_received)::int AS year,
               COUNT(DISTINCT co.vanid)                 AS donors,
               COUNT(*)                                 AS gifts,
               SUM(co.amount)                           AS total
        FROM contributions co
        JOIN contacts c ON co.vanid = c.vanid
        WHERE co.amount > 0
          AND c.state IS NOT NULL
          AND EXTRACT(YEAR FROM co.date_received) BETWEEN 2010 AND 2026
        GROUP BY c.state, EXTRACT(YEAR FROM co.date_received)::int
        ORDER BY c.state, year
    """)).fetchall()

df = pd.DataFrame([dict(r._mapping) for r in rows])
df["total"] = df["total"].astype(float)

# ── 1. Summary table — all states ranked by total ─────────────────────────
summary = (
    df.groupby("state")
    .agg(total_amount=("total", "sum"),
         total_gifts=("gifts", "sum"),
         total_donors=("donors", "sum"))
    .sort_values("total_amount", ascending=False)
    .reset_index()
)
summary["avg_gift"] = summary["total_amount"] / summary["total_gifts"]

print("═" * 60)
print(f"{'State':<8}{'Total Amount':>14}{'Gifts':>10}{'Donors':>10}{'Avg Gift':>10}")
print("─" * 60)
for _, r in summary.iterrows():
    print(f"{r['state']:<8}${r['total_amount']:>12,.0f}{r['total_gifts']:>10,.0f}"
          f"{r['total_donors']:>10,.0f}  ${r['avg_gift']:>8,.0f}")

# ── 2. Bar chart — top 15 states by total amount ──────────────────────────
top15 = summary.head(15)

fig, ax = plt.subplots(figsize=(12, 6))
colors = ["#2a9d8f" if s == "AZ" else "#a8dadc" for s in top15["state"]]
bars = ax.bar(top15["state"], top15["total_amount"], color=colors, edgecolor="white")
for bar, val in zip(bars, top15["total_amount"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + top15["total_amount"].max() * 0.01,
            f"${val/1e6:.1f}M" if val >= 1e6 else f"${val/1e3:.0f}K",
            ha="center", fontsize=8)
ax.set_ylabel("Total Donation Amount")
ax.set_title("Total Donation Amount by State (2010–2026, Top 15)", fontsize=13, fontweight="bold")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K"))
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/state_donations_total.png", dpi=150, bbox_inches="tight")
plt.close()
print("\n✓ Saved: state_donations_total.png")

# ── 3. Small multiples — top 12 states, yearly trend ─────────────────────
top12_states = summary.head(12)["state"].tolist()
pivot = df[df["state"].isin(top12_states)].pivot_table(
    index="year", columns="state", values="total", aggfunc="sum", fill_value=0
)[top12_states]

ncols = 4
nrows = 3
fig, axes = plt.subplots(nrows, ncols, figsize=(16, 10))
axes = axes.flatten()
fig.suptitle("Donation Amount by State Over Time (Top 12)", fontsize=14, fontweight="bold")

for i, state in enumerate(top12_states):
    ax = axes[i]
    vals = pivot[state]
    color = "#2a9d8f" if state == "AZ" else "#e76f51"
    ax.bar(vals.index, vals.values, color=color, alpha=0.85, edgecolor="white", linewidth=0.4)
    ax.set_title(state, fontsize=11, fontweight="bold")
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    ax.tick_params(axis="y", labelsize=7)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K"))
    ax.grid(axis="y", alpha=0.3)

for j in range(len(top12_states), len(axes)):
    axes[j].set_visible(False)

plt.tight_layout()
plt.savefig(f"{OUT}/state_donations_trends.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ Saved: state_donations_trends.png")

# ── 4. Non-AZ only — same small multiples without AZ to show detail ───────
non_az = summary[summary["state"] != "AZ"].head(11)["state"].tolist()
pivot_naz = df[df["state"].isin(non_az)].pivot_table(
    index="year", columns="state", values="total", aggfunc="sum", fill_value=0
)[non_az]

fig, axes = plt.subplots(3, 4, figsize=(16, 10))
axes = axes.flatten()
fig.suptitle("Donation Amount by State Over Time — Excluding AZ (Top 11)", fontsize=13, fontweight="bold")

for i, state in enumerate(non_az):
    ax = axes[i]
    vals = pivot_naz[state]
    ax.bar(vals.index, vals.values, color="#e76f51", alpha=0.85, edgecolor="white", linewidth=0.4)
    ax.set_title(state, fontsize=11, fontweight="bold")
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    ax.tick_params(axis="y", labelsize=7)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K"))
    ax.grid(axis="y", alpha=0.3)

for j in range(len(non_az), len(axes)):
    axes[j].set_visible(False)

plt.tight_layout()
plt.savefig(f"{OUT}/state_donations_trends_nonaz.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ Saved: state_donations_trends_nonaz.png")
