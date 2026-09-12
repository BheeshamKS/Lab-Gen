# Lab Task: Data Analysis and Summary Statistics
# Student: Bheesham Kumar Sajnani (25F-DS-020)

import numpy as np
import pandas as pd

# 1. Create realistic sample student performance dataset
np.random.seed(42)
data = {
    'StudentID': [f'25F-DS-{i:03d}' for i in range(1, 11)],
    'Quiz_Score': np.random.randint(55, 98, size=10),
    'Assignment_Score': np.random.randint(60, 100, size=10),
    'Study_Hours': np.round(np.random.uniform(2.5, 10.0, size=10), 1)
}

df = pd.DataFrame(data)
df['Total_Score'] = (df['Quiz_Score'] * 0.4) + (df['Assignment_Score'] * 0.6)

print('=== Student Performance Dataset Preview ===')
print(df.head(6))

print('\n=== Descriptive Statistics ===')
print(df[['Quiz_Score', 'Assignment_Score', 'Total_Score']].describe().round(2))

top_student = df.loc[df['Total_Score'].idxmax()]
print(f'\nHighest Performer: {top_student["StudentID"]} with Score: {top_student["Total_Score"]:.1f}')
