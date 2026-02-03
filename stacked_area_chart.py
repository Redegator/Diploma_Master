import pandas as pd
import matplotlib.pyplot as plt


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)


df = pd.read_csv('metadata.csv')

df['collection_date'] = pd.to_datetime(df['collection_date'])


# Штука, яка витягує мені номер тижня і рік
iso = df['collection_date'].dt.isocalendar()
df['week_year'] = (
    iso['week'].astype(str).str.zfill(2)
    + '/' +
    iso['year'].astype(str)
)




# print(df['week_year'].value_counts())

sorted_weeks = sorted(
    df['week_year'].unique(),
    key=lambda x: (int(x.split('/')[1]), int(x.split('/')[0]))
)




import pandas as pd
import matplotlib.pyplot as plt

# Рахуємо кількість випадків на тиждень
counts = df['week_year'].value_counts().reset_index()
counts.columns = ['week_year', 'count']

# Сортуємо хронологічно
counts = counts.sort_values(
    by=['week_year'],
    key=lambda col: col.map(lambda x: (int(x.split('/')[1]), int(x.split('/')[0])))
)

# Будуємо графік
# plt.figure(figsize=(12, 6))
# plt.plot(counts['week_year'], counts['count'], marker='o', linestyle='-')

# plt.title('Кількість випадків по тижнях')
# plt.xlabel('Тиждень/Рік')
# plt.ylabel('Кількість')
# plt.xticks(rotation=60, ha='right')
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.show()








