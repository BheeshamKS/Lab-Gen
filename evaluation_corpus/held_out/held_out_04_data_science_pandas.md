# Data Science Laboratory Manual
## Session: 10 - Exploratory Data Analysis and Statistical Summaries
**Course:** Data Science & Applied Statistics  
**Topic:** Transaction Data Distribution Analysis and IQR Outlier Detection

### Scenario & Dataset Description:
The dataset simulates electronic banking transactions containing transaction identifier, customer age, transaction amount ($), and customer rating.

### LAB TASKS:
#### Task 1: Descriptive Statistics Summary
Write a Python script using pandas to calculate the mean, median, standard deviation, and variance for transaction amounts from sample transaction records.

#### Task 2: Outlier Detection using Interquartile Range
Write a Python script to compute the 25th percentile (Q1), 75th percentile (Q3), and IQR for transaction amounts, identifying all records where amount > Q3 + 1.5 * IQR.

#### Task 3: Summary Visualization and Distribution Reporting
Write a Python script to summarize transaction distribution statistics and display formatted metrics.

### OBSERVATION TABLE:
| Metric | Formula | Expected Calculation |
| :--- | :--- | :--- |
| Mean | sum(x) / N | Arithmetic Average of Amounts |
| Median | Q2 (50th percentile) | Middle Value |
| IQR | Q3 - Q1 | Spread of Middle 50% |

### Questions for Analysis:
1. Under what statistical distribution conditions is the median preferred over the mean as a measure of central tendency?
2. How does the 1.5 * IQR multiplier threshold minimize false positives in financial anomaly detection?

### Viva Voce Questions:
1. What is the definition of the Interquartile Range (IQR)?
2. Why is NumPy or Pandas vectorized operation faster than a standard Python for-loop?
