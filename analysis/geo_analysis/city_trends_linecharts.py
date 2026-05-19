import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ── Load data ────────────────────────────────────────────────────────────────
contrib = pd.read_csv(
    '../../All Contributions Ever 4.9.26.xls',
    encoding='utf-16', sep='\t', on_bad_lines='skip', low_memory=False
)
contrib['date'] = pd.to_datetime(contrib['Date Received'], errors='coerce')
contrib = contrib[contrib['date'].notna()].copy()
contrib['amount'] = pd.to_numeric(contrib['Amount'], errors='coerce').fillna(0)
contrib = contrib[contrib['amount'] > 0].copy()
contrib['vanid'] = contrib['VANID'].astype(str)
contrib['year'] = contrib['date'].dt.year

contacts = pd.read_csv(
    '../../Database List 4.9.26.xls',
    encoding='utf-16', sep='\t', on_bad_lines='skip', low_memory=False
)
contacts = contacts.rename(columns={
    'VANID': 'vanid',
    'State/Province': 'state',
    'City': 'city',
})[['vanid', 'city', 'state']]
contacts['vanid'] = contacts['vanid'].astype(str)

# ── Join & filter AZ, 2010–2026 ──────────────────────────────────────────────
df = contrib.merge(contacts, on='vanid', how='left')
df = df[(df['state'] == 'AZ') & (df['year'] >= 2010)].copy()
df = df[df['city'].notna() & (df['city'].str.strip() != '')].copy()

# ── Pick top 10 cities by total unique donors across all years ───────────────
city_donor_totals = df.groupby('city')['vanid'].nunique().sort_values(ascending=False)
top10_cities = city_donor_totals.head(10).index.tolist()
df_top = df[df['city'].isin(top10_cities)].copy()

# ── Build yearly series ───────────────────────────────────────────────────────
# Chart 1: unique donors per city per year
donors_by_city_year = (
    df_top.groupby(['city', 'year'])['vanid']
    .nunique()
    .reset_index()
    .rename(columns={'vanid': 'unique_donors'})
    .pivot(index='year', columns='city', values='unique_donors')
    .reindex(range(2010, 2027))   # fill missing years with NaN
)

# Chart 2: total donation amount per city per year
amount_by_city_year = (
    df_top.groupby(['city', 'year'])['amount']
    .sum()
    .reset_index()
    .pivot(index='year', columns='city', values='amount')
    .reindex(range(2010, 2027))
)

COLORS = plt.get_cmap('tab10').colors

def plot_city_lines(pivot_df, title, ylabel, formatter, save_path, yticks, ymin):
    _, ax = plt.subplots(figsize=(14, 6))

    # Only replace NaN (truly missing years), keep actual 0 values as-is
    # Cities that are always 0 are already excluded via top10 selection
    data = pivot_df.copy()

    for i, city in enumerate(top10_cities):
        if city not in data.columns:
            continue
        series = data[city]
        color = COLORS[i % 10]

        # Solid line 2010–2025
        solid = series[series.index <= 2025]
        ax.plot(solid.index, solid.values, color=color, linewidth=2,
                label=city, marker='o', markersize=4)

        # Dashed segment 2025–2026 to signal partial year
        if 2026 in series.index and pd.notna(series.get(2026)) and pd.notna(series.get(2025)):
            ax.plot([2025, 2026], [series[2025], series[2026]],
                    color=color, linewidth=2, linestyle='--')
            ax.plot(2026, series[2026], color=color, marker='o',
                    markersize=4, fillstyle='none')

    # Apply sqrt scale AFTER data is plotted so limits are already set
    ax.set_yscale('function', functions=(np.sqrt, np.square))
    ax.set_ylim(bottom=ymin)
    ax.set_yticks(yticks)
    ax.yaxis.set_major_formatter(formatter)

    ax.axvspan(2025.5, 2026.5, color='#f0f0f0', zorder=0, alpha=0.5)

    ax.set_title(title, fontweight='bold', fontsize=14)
    ax.set_ylabel(ylabel)
    ax.set_xlabel('Year')
    ax.set_xticks(range(2010, 2027))
    ax.set_xticklabels(range(2010, 2027), rotation=45, ha='right')
    ax.legend(loc='upper left', fontsize=6, ncol=2, framealpha=0.9, handlelength=1.2, handletextpad=0.3, borderpad=0.3, labelspacing=0.2)
    ax.grid(axis='y', alpha=0.3)
    ax.grid(axis='x', alpha=0.15)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f'Saved: {save_path}')
    plt.show()

# ── Chart 1: Unique donors ────────────────────────────────────────────────────
plot_city_lines(
    donors_by_city_year,
    title='Number of Unique Donors by City Over Time (Top 10 AZ Cities)',
    ylabel='Donors per Year',
    formatter=mticker.FuncFormatter(lambda v, _: f'{int(v):,}'),
    save_path='../figures/city_unique_donors_trend.png',
    yticks=[0, 10, 25, 50, 75, 100, 150, 200, 300, 400, 500],
    ymin=0,
)

# ── Chart 2: Total donation amount ────────────────────────────────────────────
plot_city_lines(
    amount_by_city_year,
    title='Total Donation Amount by City Over Time (Top 10 AZ Cities)',
    ylabel='Total Donations ($)',
    formatter=mticker.FuncFormatter(lambda v, _: f'${v/1000:.0f}K' if v >= 1000 else f'${v:.0f}'),
    save_path='../figures/city_donation_amount_trend.png',
    yticks=[0, 1000, 5000, 10000, 25000, 50000, 100000, 150000, 200000, 300000],
    ymin=0,
)
