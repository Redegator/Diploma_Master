import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)


# Зчитуємо дані
df = pd.read_csv("metadata.csv")


print(df.columns)


# Для 4253 нема collection_date, треба подивитися і взяти дату по по даті захворювання, якщо є


print(len(df['Sample'].unique()))
