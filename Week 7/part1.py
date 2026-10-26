import pandas as pd

#Question 1
df = pd.read_csv('Data\\BDX.csv')
print(df.head(5),"\n")

#Question 2
print("Rows and columns:", df.shape)
print("Number of Rows:", df.shape[0])
print("Number of Columns:", df.shape[1],"\n")

#Question 3
print("Column Names:", df.columns.tolist(),"\n")

#Question 4
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

df_2020 = df[df["Date"].dt.year >= 2020]

print("Dataframe for 2020 onwards:\n")
print(df_2020.head(5),"\n")
print("Rows and columns:", df_2020.shape)
print("Number of Rows:", df_2020.shape[0])
print("Number of Columns:", df_2020.shape[1])
