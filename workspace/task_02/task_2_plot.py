# Lab Task: Data Visualization with Matplotlib
# Student: Bheesham Kumar Sajnani (25F-DS-020)

import numpy as np
import matplotlib.pyplot as plt

# Generate sample distribution data
np.random.seed(101)
hours = np.linspace(1, 10, 20)
scores = 50 + (hours * 4.5) + np.random.normal(0, 3, 20)

plt.figure(figsize=(7, 4))
plt.scatter(hours, scores, color='#2b5c8f', label='Student Data')
m, b = np.polyfit(hours, scores, 1)
plt.plot(hours, m*hours + b, color='#e05d44', linestyle='--', label=f'Trend (slope={m:.2f})')

plt.title('Study Hours vs Exam Score Analysis', fontsize=12, fontweight='bold')
plt.xlabel('Weekly Study Hours')
plt.ylabel('Exam Score (%)')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('plot_output.png', dpi=150)
print('[+] Scatter plot successfully rendered and saved to plot_output.png')
print(f'[+] Fitted Trend Equation: Score = {m:.2f} * Hours + {b:.2f}')
