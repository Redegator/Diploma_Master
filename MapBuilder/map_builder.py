import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
# pd.set_option('display.width', None)


all_df = pd.read_excel('settings.xlsx', usecols='A:C')


# Витягуємо всі параметри з екселю
filename = all_df.iloc[1, 1]
color = all_df.iloc[2, 1]
vmin = all_df.iloc[3, 1]
vmax = all_df.iloc[4, 1]
tickCount = all_df.iloc[5, 1]
label_name = all_df.iloc[6, 1]
language = all_df.iloc[7, 1]
empty_values = all_df.iloc[8, 1]


# Витягуємо всі значення для областей з екселю
regions_df = all_df.loc[10:, ['id', 'number']].copy()

regions_df['number'] = pd.to_numeric(regions_df['number'])

if empty_values != 'yes':
    regions_df = regions_df[regions_df['number'].fillna(0) > 0].copy()

regions_df['id'] = regions_df['id'].astype(int)
regions_df = regions_df[['id', 'number']]


# Геодані регіонів України
with open('Ukraine-regions.json', encoding='utf-8') as f:
    topo = json.load(f)
ukraine_regions = alt.Data(values=topo, format=alt.DataFormat(type='topojson', feature='UKR_adm1'))


# Дані по зразках
if language == 'ua':
    oblast_ids = {
        "Вінницька": 3159,
        "Волинська": 3160,
        "Дніпропетровська": 3140,
        "Житомирська": 3162,
        "Запорізька": 3161,
        "Закарпатська": 3158,
        "Івано-Франківська": 3142,
        "Київська": 3146,   # область, не місто
        "Кіровоградська": 3148,
        "Львівська": 3150,
        "Миколаївська": 3151,
        "Одеська": 3152,
        "Полтавська": 3153,
        "Рівненська": 3154,
        "Сумська": 3156,
        "Тернопільська": 3157,
        "Харківська": 3143,
        "Херсонська": 3144,
        "Хмельницька": 3145,
        "Черкаська": 3136,
        "Чернівецька": 3138,
        "Чернігівська": 3137,
        "м. Київ": 3147,
        "ㅤㅤㅤАвтономна Республіка Крим": 3139,
        "Луганська": 3149,
        "Донецька": 3141
    }
    
elif language == 'eng':
    oblast_ids = {
        "Vinnytsia": 3159,
        "Volyn": 3160,
        "Dnipropetrovsk": 3140,
        "Zhytomyr": 3162,
        "Zaporizhzhia": 3161,
        "Zakarpattia": 3158,
        "Ivano-Frankivsk": 3142,
        "Kyiv": 3146,   # область, не місто
        "Kirovohrad": 3148,
        "Lviv": 3150,
        "Mykolaiv": 3151,
        "Odesa": 3152,
        "Poltava": 3153,
        "Rivne": 3154,
        "Sumy": 3156,
        "Ternopil": 3157,
        "Kharkiv": 3143,
        "Kherson": 3144,
        "Khmelnytskyi": 3145,
        "Cherkasy": 3136,
        "Chernivtsi": 3138,
        "Chernihiv": 3137,
        "Kyiv city": 3147,
        "ㅤㅤㅤAutonomous Republic of Crimea": 3139,
        "Luhansk": 3149,
        "Donetsk": 3141
    }

oblast_names_df = pd.DataFrame(list(oblast_ids.items()), columns=['region', 'id'])


# Центроїди для підписів на карті
centroids = pd.DataFrame({
    "id": [
        3136, 3137, 3138, 3140, 3141, 3142, 3143, 3144, 3145, 3146,
        3147, 3148, 3150, 3151, 3152, 3153, 3154, 3156, 3157, 3158,
        3159, 3160, 3161, 3162, 3149, 3139
    ],
    "lon": [
        31.331493, 31.975935, 25.888811, 34.8, 37.8, 24.628592, 36.590609, 33.4, 26.907733, 30.323011,
        30.105833, 32.256516, 23.847720, 31.960882, 30.258725, 33.738598, 26.548957, 33.862612, 25.596856, 23.189433,
        28.585057, 24.753590, 35.729808, 28.431416, 38.95, 34.49
    ],
    "lat": [
        49.358305, 51.554604, 48.415654, 48.50, 48.10, 48.89204, 49.737541, 46.70, 49.667992, 49.877921,
        50.487134, 48.617372, 49.977351, 47.495375, 47.203764, 49.888243, 50.932083, 51.330561, 49.497751, 48.553755,
        49.04712, 51.448278, 47.467979, 50.852741, 49.06, 45.4
    ]
})



# З'єднання даних з центроїдами (додавання координат по id області)
labeled_participants = regions_df.merge(centroids, on="id", how="left") \
                                 .merge(oblast_names_df, on="id", how="left")


def format_label(val):
    if val == 0:
        return '*'
    return str(int(val))

def format_color(val):
    if val == 0:
        return 'red'
    return 'black'

labeled_participants['display_text'] = labeled_participants['number'].fillna(0).apply(format_label)
labeled_participants['display_color'] = labeled_participants['number'].fillna(0).apply(format_color)

# Картографічна основа
sns.set_theme(style="whitegrid")
map_chart = alt.Chart(ukraine_regions).mark_geoshape(
    stroke='black',
    strokeWidth=0.5
).encode(
    color=alt.Color(
        'number:Q',
        # scale=alt.Scale(scheme='purpleblue', domain=[0, 10]),
        scale=alt.Scale(scheme=color, domain=[vmin, vmax]),
        legend=alt.Legend(
            orient='bottom',
            offset=-140,
            legendX=50,
            title=f'ㅤㅤ{label_name}',
            # title=f'Coxsackievirus',
            titleFontSize=13,
            labelFontSize=11,
            tickCount=tickCount   # Кількість міток на градієнтній легенді
        )
    ),
    tooltip=['properties.NAME_1:N', 'number:Q']
).transform_lookup(
    lookup='properties.ID_1',
    from_=alt.LookupData(labeled_participants, key='id', fields=['number'])
).transform_filter(
    alt.datum.number > 0
).project(
    type='mercator'
)


# Підписи з кількістю зразків
labels = alt.Chart(labeled_participants).mark_text(
    fontSize=10,
    fontWeight='bold',
    color='black'  # <--- Просто задаємо чорний колір для всіх
).encode(
    longitude='lon:Q',
    latitude='lat:Q',
    text='display_text:N'  # <--- Беремо підготовлений текст із зірочкою
)


# Підписи з назвами областей
labeled_participants["lat_name_label"] = np.where(
    labeled_participants["region"].isin(["Kyiv city", "м. Київ"]),
    labeled_participants["lat"] + 0.25,
    labeled_participants["lat"] - 0.2
)
name_labels = alt.Chart(labeled_participants).mark_text(
    fontSize=9.5,
    color='black'
).encode(
    longitude='lon:Q',
    latitude='lat_name_label:Q',
    text='region:N'
)


# Обводка незаповнених областей
outline = alt.Chart(ukraine_regions).mark_geoshape(
    filled=False,
    stroke='black'
)

# Комбінування шарів
os.makedirs("plots", exist_ok=True)
(map_chart + labels + name_labels + outline).properties(width=800, height=600).save(f"plots/{filename}_map_.html")


# Об'єднуємо шари в один об'єкт
final_chart = (map_chart + labels + name_labels + outline).properties(
    width=800, 
    height=600
)

# Зберігаємо у PNG
# scale_factor=3.0 забезпечує високу якість (High DPI)
final_chart.save(f"plots/{filename}_map.png", scale_factor=5.0)