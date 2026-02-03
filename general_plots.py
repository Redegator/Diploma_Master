import pandas as pd
import numpy as np
import altair as alt

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)


main_df = pd.read_csv('metadata_table_prep/metadata.csv')


bins = range(0, 100, 5)

for i, row in main_df.iterrows():

    try:
        age = int(row["Age"])

        for bin in bins:

            if age >= bin and age <= bin+5:
                main_df.at[i, "Age_group"] = f"{bin}-{bin+4}"
        

    except:
        main_df.at[i, "Age_group"] = "Unknown"


B_df = main_df[main_df['Variant Virus'] == 'B']
H1N1_df = main_df[main_df['Variant Virus'] == 'H1N1']
H3N2_df = main_df[main_df['Variant Virus'] == 'H3N2']



import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")


def map_build_func(df, df_name):

    if df_name == "influenza A (H1N1)":
        color = "purpleblue"
    elif df_name == "influenza A (H3N2)":
        color = "reds"
    elif df_name == "influenza B":
        color = "yellowgreen"
    elif df_name == "influenza":
        color = "yellowgreenblue"

    # Геодані регіонів України
    ukraine_regions = alt.topo_feature(
        'https://raw.githubusercontent.com/org-scn-design-studio-community/sdkcommunitymaps/master/geojson/Europe/Ukraine-regions.json', 
        'UKR_adm1'
    )

    # Дані по зразках
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
        "Kyiv city": 3147
    }


    participants_by_oblast = (
        df['Region']
        .value_counts()
        .rename_axis('oblast')
        .reset_index(name='Number of samples')
    )

    participants_by_oblast["oblast_id"] = participants_by_oblast["oblast"].map(oblast_ids)

    # Центроїди для підписів на карті
    centroids = pd.DataFrame({
        "oblast_id": [
            3136, 3137, 3138, 3140, 3141, 3142, 3143, 3144, 3145, 3146,
            3147, 3148, 3150, 3151, 3152, 3153, 3154, 3156, 3157, 3158,
            3159, 3160, 3161, 3162
        ],
        "lon": [
            31.331493, 31.975935, 25.888811, 34.8, 37.8, 24.628592, 36.590609, 33.4, 26.907733, 30.323011,
            30.105833, 32.256516, 23.847720, 31.960882, 30.258725, 33.738598, 26.548957, 33.862612, 25.596856, 23.189433,
            28.585057, 24.753590, 35.729808, 28.431416
        ],
        "lat": [
            49.358305, 51.554604, 48.415654, 48.50, 48.10, 48.89204, 49.737541, 46.70, 49.667992, 49.877921,
            50.487134, 48.617372, 49.977351, 47.495375, 47.203764, 49.888243, 50.932083, 51.330561, 49.497751, 48.553755,
            49.04712, 51.448278, 47.467979, 50.852741
        ]
    })

    # З'єднання даних з центроїдами
    labeled_participants = participants_by_oblast.merge(centroids, on="oblast_id", how="left")

    # Картографічна основа
    map_chart = alt.Chart(ukraine_regions).mark_geoshape(
        stroke='black',
        strokeWidth=0.5
    ).encode(
        color=alt.Color(
            'Number of samples:Q',
            # scale=alt.Scale(scheme='purpleblue', domain=[0, 10]),
            scale=alt.Scale(scheme=color),
            legend=alt.Legend(
                orient='bottom',
                offset=-140,
                legendX=50,
                title='ㅤㅤㅤNumber of samples',
                titleFontSize=13,
                labelFontSize=11,
                tickCount=6   # Кількість міток на градієнтній легенді
            )
        ),
        tooltip=['properties.NAME_1:N', 'num_participants:Q']
    ).transform_lookup(
        lookup='properties.ID_1',
        from_=alt.LookupData(labeled_participants, 'oblast_id', ['Number of samples'])
    ).project(
        type='mercator'
    )

    # Підписи з кількістю зразків
    labels = alt.Chart(labeled_participants).mark_text(
        fontSize=10,
        fontWeight='bold',
        color='black'
    ).encode(
        longitude='lon:Q',
        latitude='lat:Q',
        text='Number of samples:Q'
    )

    # Підписи з назвами областей
    labeled_participants["lat_name_label"] = np.where(
        labeled_participants["oblast"] == "Kyiv city",
        labeled_participants["lat"] + 0.25,
        labeled_participants["lat"] - 0.2
    )
    name_labels = alt.Chart(labeled_participants).mark_text(
        fontSize=9.5,
        color='black'
    ).encode(
        longitude='lon:Q',
        latitude='lat_name_label:Q',
        text='oblast:N'
    )

    # Обводка незаповнених областей
    outline = alt.Chart(ukraine_regions).mark_geoshape(
        filled=False,
        stroke='black'
    )

    # Комбінування шарів
    (map_chart + labels + name_labels + outline).properties(width=800, height=600).save(f"plots/maps/{df_name}_map_.html")


# Функція для підпису: кількість + %
def percentage_description_func(pct, allvals):
    absolute = int(round(pct/100.*sum(allvals)))
    return f"{absolute}\n({pct:.1f}%)"

for df, df_name in zip([B_df, H1N1_df, H3N2_df, main_df], ["influenza B", "influenza A (H1N1)", "influenza A (H3N2)", "influenza"]):


    data_for_chart = df['Sex'].value_counts()

    sex_order = ["Female", "Male", "Unknown"]
    data_for_chart = data_for_chart.reindex(sex_order).dropna() 


    plt.figure(figsize=(5, 5))
    plt.pie(
        data_for_chart.values,
        labels=data_for_chart.index,
        autopct=lambda pct: percentage_description_func(pct, data_for_chart.values),
        startangle=90,
        colors=["#d168b9", "#67bed9", "#bbbbbb"]
    )
    plt.title(f"Sex distribution for {df_name}")
    plt.savefig(f"plots/new_sex_distribution/sex_{df_name}.png", dpi=300, bbox_inches="tight")
    plt.show()



    age_data = df['Age_group'].value_counts()


    age_order = ["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34",
             "35-39", "40-44", "45-49", "50-54", "55-59", "60-64",
             "65-69", "70-74", "75-79", "80-84", "85-89", "90-94", "95-99"]

    

    if df_name == "influenza A (H3N2)" or df_name == "influenza":
        age_data = age_data.reindex(age_order, fill_value=0)
    else:
        age_data = age_data.reindex(age_order).dropna()  # впорядкували


    # Графік
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))

    ax = sns.barplot(
        x=age_data.index,
        y=age_data.values,
        color="#608CEC"
    )

    ax.set_xlabel("Age")
    ax.set_ylabel("Number of subjects")

    import matplotlib.ticker as mticker
    ax.yaxis.set_major_locator(mticker.MultipleLocator(5))

    # Прибираємо рамки
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Підписуємо значення над стовпчиками
    for i, v in enumerate(age_data.values):
        ax.text(i, v + 0.5, str(int(v)), ha='center', va='bottom', fontsize=9)

    plt.title(f"Age distribution for {df_name}")
    plt.tight_layout()
    plt.savefig(f"plots/age_distribution/age_{df_name}.png", dpi=300, bbox_inches="tight")
    plt.show()



    print(df_name)
    print()

    print(df['Sex'].value_counts())
    print()

    # print(df['Region'].value_counts())
    
    map_build_func(df, df_name)

    print('\n')