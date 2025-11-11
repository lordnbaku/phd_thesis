import pandas as pd
import numpy as np
from linearmodels.panel import PanelOLS
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

print("Loading data from 'Bank Data2' (Sheet Index 3)...")
df = pd.read_excel('nigerian_banks.xlsx', sheet_name=3)  # "Bank Data2"

print("Cleaning data...")
df['bank_id'] = pd.Categorical(df['Bank Name']).codes + 1
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
df['post2015'] = (df['Year'] >= 2015).astype(int)

# Use CORRECT column names from "Bank Data2"
# CGDI, Practice Index (PIND), Compliance Index (COMID), TCAR, MC
vars_keep = ['bank_id', 'Year', 'NPLR', 'CGDI', 'PIND', 'COMID', 'MC', 'TCAR']
df = df[vars_keep + ['post2015']].dropna()
df = df.set_index(['bank_id', 'Year'])

print(f"Panel ready: {df.shape[0]} obs, {len(df.index.unique('bank_id'))} banks")

# FULL MODEL
print("\nRunning Full Model...")
mod1 = PanelOLS.from_formula(
    'NPLR ~ CGDI + PIND + COMID + MC + TCAR + EntityEffects + TimeEffects',
    data=df
).fit(cov_type='clustered', cluster_entity=True)
print(mod1.summary)

# INTERACTION MODEL
print("\nRunning Interaction Model...")
mod2 = PanelOLS.from_formula(
    'NPLR ~ CGDI + CGDI:post2015 + PIND + COMID + MC + TCAR + EntityEffects + TimeEffects',
    data=df
).fit(cov_type='clustered', cluster_entity=True)

print(f"\nCGDI (pre-2015): {mod2.params['CGDI']:.3f}")
print(f"CGDI × Post2015: {mod2.params['CGDI:post2015']:.3f}")
print(f"Total CGDI effect post-2015: {mod2.params['CGDI'] + mod2.params['CGDI:post2015']:.3f}")

# PLOT
print("\nGenerating plot...")
plt.figure(figsize=(11, 7))
sns.scatterplot(data=df.reset_index(), x='CGDI', y='NPLR', hue='post2015', alpha=0.7, s=60)
sns.regplot(data=df.reset_index()[df.reset_index()['Year'] < 2015], 
            x='CGDI', y='NPLR', scatter=False, color='blue')
sns.regplot(data=df.reset_index()[df.reset_index()['Year'] >= 2015], 
            x='CGDI', y='NPLR', scatter=False, color='red')
plt.title('NPL Ratio vs Transparency (CGDI)\nBlue = Pre-2015 | Red = Post-2015', fontsize=14)
plt.xlabel('Corporate Governance Disclosure Index (CGDI %)', fontsize=12)
plt.ylabel('Non-Performing Loan Ratio (NPLR %)', fontsize=12)
plt.legend(title='Period', labels=['Pre-2015', 'Post-2015'])
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('npl_vs_cgdi_final.png', dpi=300, bbox_inches='tight')
plt.show()
# EXPORT RESULTS TO CSV
print("\nExporting results to CSV...")
results = {
    'Variable': ['CGDI (pre-2015)', 'CGDI × Post2015', 'Total CGDI (post-2015)', 
                 'PIND', 'COMID', 'MC', 'TCAR'],
    'Coefficient': [
        mod2.params['CGDI'],
        mod2.params['CGDI:post2015'],
        mod2.params['CGDI'] + mod2.params['CGDI:post2015'],
        mod2.params['PIND'],
        mod2.params['COMID'],
        mod2.params['MC'],
        mod2.params['TCAR']
    ],
    'Std_Error': [
        mod2.std_errors['CGDI'],
        mod2.std_errors['CGDI:post2015'],
        np.nan,  # Total effect has no direct SE
        mod2.std_errors['PIND'],
        mod2.std_errors['COMID'],
        mod2.std_errors['MC'],
        mod2.std_errors['TCAR']
    ],
    'P_value': [
        mod2.pvalues['CGDI'],
        mod2.pvalues['CGDI:post2015'],
        np.nan,
        mod2.pvalues['PIND'],
        mod2.pvalues['COMID'],
        mod2.pvalues['MC'],
        mod2.pvalues['TCAR']
    ]
}

import pandas as pd
results_df = pd.DataFrame(results)
results_df.to_csv('npl_regression_results.csv', index=False)
print("Exported: npl_regression_results.csv")

print("\nDONE! Check: npl_vs_cgdi_final.png")
