"""
Цей скрипт використовується для обробки результатів MIRA. Він працює з двома FASTA-файлами: 
'RSP{run_id}/passed.fasta' та 'RSP{run_id}/less.fasta', а також 'RSP{run_id}/metadata.xlsx',
для підготовки зібраних послідовностей до завантаження на FluSurver.

Основні функції:
1. Підготовка даних для GISAID: обробка метаданих, стандартизація назв областей та
   генерація готових до завантаження файлів (CSV та FASTA) для fluCLI.
2. Форматування FASTA-файлів: очищення заголовків та виділення HA-сегментів
   для подального запуску NextClade і FluSurver
3. Аналіз  Nextclade: автоматичний запуск bash-скрипта, обробка результатів та
   визначення найкращого варіанту, клади й субклади вірусу.
4. Генерація фінального звіту: зведення показників якості, адаптація назв регіонів та
   збереження усіх даних у підсумковий Excel-файл
"""

# ЗАМІНІТЬ ЦЕ або передайте параметри при запуску з терміналу
run_id = 'example'
sequencer = 'MiSeq' # або 'NextSeq', це впливає на формат заголовків у FASTA

import os
import sys
import pandas as pd
from Bio import SeqIO
import requests
from bs4 import BeautifulSoup
import xlrd


pd.set_option('display.max_columns', None)  
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)


# Оновлення run_id та sequencer з аргументів командного рядка, якщо вони надані
sequencer = sys.argv[2] if len(sys.argv) > 2 else sequencer
run_id = sys.argv[1] if len(sys.argv) > 1 else run_id
run_name = 'RSP' + str(run_id)


amended_consensus = os.path.join(run_name, 'amended_consensus.fasta')
failed_amended_consensus = os.path.join(run_name, 'failed_amended_consensus.fasta')


# Функція для пошуку всіх ідентифікаторів фрагментів HA з вихідного файлу MIRA
def extract_ids(fasta_file):
    ids = []
    with open(fasta_file, 'r') as file:
        for line in file:
            if line.startswith('>') and "HA" in line:
                parts = line[1:].split('_')  # Remove '>' and split by '_'
                # parts = line[1:].split('|')  # Remove '>' and split by '_'
                if parts[0].isdigit() and len(parts[0]) == 4:
                    id = (parts[0])
                    ids.append(id)

    return ids


# Витягування ID зразків з вихідних fasta-файлів MIRA
amended_ids = extract_ids(amended_consensus)
failed_ids = extract_ids(failed_amended_consensus)

"""
БЛОК 1: ПІДГОТОВКА CSV ДЛЯ GISAID
================================================================================================================================================
"""

# Excel-файл з метаданими
excel_file = os.path.join(run_name, 'metadata.xlsx')
df_metadata = pd.read_excel(excel_file, usecols=["id", "variant", "region", "ct", "collection_date", "sex", "age", "age_units"], engine="openpyxl", dtype=str)
df_metadata = df_metadata.set_index('id')

# Використовується для запобігання значенням None в df_gisaid, якщо локації в метаданих були об'єднані
df_metadata['region'] = df_metadata['region'].ffill()


# Створення повного датасету для завантаження в GISAID
df_gisaid = pd.DataFrame(index=amended_ids, columns=['Isolate_Id', 'Segment_Ids', 'Isolate_Name', 'Subtype', 'Lineage', 'Passage_History', 
    'Location', 'province', 'sub_province', 'Location_Additional_info', 'Host', 'Host_Additional_info', 'Specimen_Source',
    'Sampling_Strategy', 'Sequencing_Strategy', 'Sequencing_Technology', 'Assembly_Method', 'Coverage', 'Seq_Id (HA)', 'Seq_Id (NA)',
    'Seq_Id (PB1)', 'Seq_Id (PB2)', 'Seq_Id (PA)', 'Seq_Id (MP)', 'Seq_Id (NS)', 'Seq_Id (NP)', 'Seq_Id (HE)', 'Seq_Id (P3)', 
    'Submitting_Sample_Id', 'Authors', 'Originating_Lab_Id', 'Originating_Sample_Id', 'Collection_Month', 'Collection_Year',
    'Collection_Date', 'Antigen_Character', 'Adamantanes_Resistance_geno', 'Oseltamivir_Resistance_geno', 'Zanamivir_Resistance_geno', 
    'Peramivir_Resistance_geno', 'Other_Resistance_geno', 'Adamantanes_Resistance_pheno', 'Oseltamivir_Resistance_pheno',
    'Zanamivir_Resistance_pheno', 'Peramivir_Resistance_pheno', 'Other_Resistance_pheno', 'Host_Age', 'Host_Age_Unit', 'Host_Gender',
    'Health_Status', 'Note', 'provider_sample_id'
])

# Параметри за замовчуванням
df_gisaid['Host'] = 'Human'
df_gisaid['Authors'] = 'Iryna,Demchyshyna;Ihor,Kuzin;Volodymyr,Kurpita;Vladyslav,Ostash;Liudmyla,Kota;Larysa,Kovalenko;Olha,Zaloilo'
df_gisaid['Originating_Lab_Id'] = 3816
df_gisaid['Health_Status'] = 'Out-patient'
df_gisaid['Specimen_Source'] = 'Nasopharyngeal'
df_gisaid['Sequencing_Technology'] = 'Illumina'
df_gisaid['Assembly_Method'] = 'MIRA 2.0'


# Стандартизація українських назв регіонів у глобальний географічний формат GISAID.
def update_location_func(region_text):

    dictionary_for_location_update = {
        "черкас": "Europe / Ukraine / Cherkasy region",
        "черніг": "Europe / Ukraine / Chernihiv region",
        "чернів": "Europe / Ukraine / Chernivtsi region",
        "дніпро": "Europe / Ukraine / Dnipropetrovsk region",
        "франк": "Europe / Ukraine / Ivano-Frankivsk region",
        "харків": "Europe / Ukraine / Kharkiv region",
        "херсон": "Europe / Ukraine / Kherson region",
        "хмельниц": "Europe / Ukraine / Khmelnytskyi region",
        "кіровогр": "Europe / Ukraine / Kirovohrad region",
        "львів": "Europe / Ukraine / Lviv region",
        "микола": "Europe / Ukraine / Mykolaiv region",
        "одес": "Europe / Ukraine / Odesa region",
        "полтав": "Europe / Ukraine / Poltava region",
        "рівне": "Europe / Ukraine / Rivne region",
        "сумс": "Europe / Ukraine / Sumy region",
        "терноп": "Europe / Ukraine / Ternopil region",
        "вінниц": "Europe / Ukraine / Vinnytsia region",
        "волин": "Europe / Ukraine / Volyn region",
        "закарпат": "Europe / Ukraine / Zakarpattia region",
        "запор": "Europe / Ukraine / Zaporizhzhia region",
        "житом": "Europe / Ukraine / Zhytomyr region",
    }

    if pd.isna(region_text):
        return None
    
    text = str(region_text).lower()
    
    # Окрема логіка для розділення міста Києва та Київської області
    if "київ" in text:
        if any(x in text for x in ["мцкпх", "міськ"]):
            return "Europe / Ukraine / Kyiv city"
        return "Europe / Ukraine / Kyiv region"
    
    # Мапінг через словник dictionary_for_location_update
    for key, location in dictionary_for_location_update.items():
        if key in text:
            return location
            
    return None


# Ітерація по кожному зразку, який успішно зібрався, і форматування його метадані
for sample_id in amended_ids:

    if sample_id in df_metadata.index:

        # Витягування конкретного рядка даних для цього sample_id
        # 'meta' тепер містить всю інформацію для 1 зразка (на основі метаданих Excel)
        meta = df_metadata.loc[sample_id]

        # Стандартизація субтипу
        Subtype_update = None
        if str(meta['variant']).upper() in ['В', 'B']:
            Subtype_update = 'B'
        elif str(meta['variant']).upper()  in ['A', 'А', 'H1', 'H3', 'Н1', 'Н3', 'H1/H3', 'H3/H1', 'Н1/Н3', 'Н3/Н1',]:
            Subtype_update = 'A'

        # Стандартизація статі
        Host_sex_update = None
        if meta['sex'] in ['ч', 'Ч']:
            Host_sex_update = 'M'
        elif meta['sex'] in ['ж', 'Ж']:
            Host_sex_update = 'F'

        # Стандартизація віку
        Host_age_update = meta['age']

        # Стандартизація одиниць віку
        Host_units_update = 'Y'
        if pd.notna(meta.get('age_units')):
            Host_units_update = 'M'

        # Стандартизація дати забору
        Collection_date_update = None
        year = meta["collection_date"][:4]
        month = meta["collection_date"][5:7]
        day = meta["collection_date"][8:10]
        Collection_date_update = f'{day}.{month}.{year}'

        # Стандартизація назви фрагмента
        Isolate_Name_update = None
        Isolate_Name_update = f'{Subtype_update}/Ukraine/{sample_id}/{year}'

        if Subtype_update == "A":
            Isolate_Name_update_PB1 = Isolate_Name_update + '/2'
            Isolate_Name_update_PB2 = Isolate_Name_update + '/1'
        elif Subtype_update == "B":
            Isolate_Name_update_PB1 = Isolate_Name_update + '/1'
            Isolate_Name_update_PB2 = Isolate_Name_update + '/2'
        else:
            Isolate_Name_update = None

        # Стандартизація регіону
        Location_update = None
        region_text = meta["region"]
        Location_update = update_location_func(region_text)


        # Збір всіх підготовлених даних для конкретного рядка
        row_updates = {
            'Isolate_Name': Isolate_Name_update,
            'Subtype': Subtype_update,
            'Location': Location_update,
            'Collection_Date': Collection_date_update,
            'Host_Age': Host_age_update,
            'Host_Age_Unit': Host_units_update,
            'Host_Gender': Host_sex_update,

            # Стандартизовані назви для кожного з 8 сегментів вірусу
            'Seq_Id (PB1)': Isolate_Name_update_PB1,
            'Seq_Id (PB2)': Isolate_Name_update_PB2,
            'Seq_Id (PA)':  f"{Isolate_Name_update}/3",
            'Seq_Id (HA)':  f"{Isolate_Name_update}/4",
            'Seq_Id (NP)':  f"{Isolate_Name_update}/5",
            'Seq_Id (NA)':  f"{Isolate_Name_update}/6",
            'Seq_Id (MP)':  f"{Isolate_Name_update}/7",
            'Seq_Id (NS)':  f"{Isolate_Name_update}/8"

        }
        
        # Застосування всіх змін до рядка
        df_gisaid.loc[sample_id, row_updates.keys()] = list(row_updates.values())

    # Якщо sample_id відсутній у df_metadata.index, він видаляється
    else:
        df_gisaid = df_gisaid.drop(labels=sample_id, axis=0)


gisaid_upload = f"RSP{run_id}/gisaid_upload"
os.makedirs(gisaid_upload, exist_ok=True)

df_gisaid.to_csv(f"{gisaid_upload}/gisaid_uploader.csv", index=False)

step_count = 1
num_of_steps = 6
print()
print(f'[{step_count}/{num_of_steps}] gisaid_uploader file is created!')


"""
БЛОК 2: ПІДГОТОВКА FASTA ДЛЯ GISAID
================================================================================================================================================
"""

# Функція для пошуку сегменту за 2 словами (ID і virus segment)
def find_sequences_by_keywords(keyword1, keyword2):

    seq = 0
    with open(amended_consensus, "r") as file:
        for record in SeqIO.parse(file, "fasta"):

            if keyword1 in record.id and keyword2 in record.id:
                seq = record.seq
                break

    return seq


with open(f"{gisaid_upload}/fasta_for_gisaid.fasta", "w") as fasta_file:
    # Перебір всіх зразків, які увійшли в CSV для GISAID
    for id in df_gisaid.index:
        
        # Витягування 8 сегментів Для кожного зразка
        for segment in ['Seq_Id (HA)','Seq_Id (NA)','Seq_Id (PB1)','Seq_Id (PB2)','Seq_Id (PA)','Seq_Id (MP)','Seq_Id (NS)','Seq_Id (NP)']:

            segment_name_to_find = segment.split('(')[1].split(')')[0]

            header = ">" + df_gisaid.at[id, segment]
            seq = find_sequences_by_keywords(id, segment_name_to_find)

            # Запис у файл
            fasta_file.write(f"{header}\n")
            fasta_file.write(f"{seq}\n")
    
    step_count += 1
    print(f'[{step_count}/{num_of_steps}] fasta_for_gisaid file is created!')


"""
БЛОК 3: ПІДГОТОВКА FASTA ДЛЯ FLUSURVER ТА NEXTCLADE
================================================================================================================================================
"""

search_word = "HA"
pass_less_dir = f"RSP{run_id}/pass_less_dir"
os.makedirs(pass_less_dir, exist_ok=True)

output_amended = os.path.join(pass_less_dir, 'passed.fasta')
output_failed = os.path.join(pass_less_dir, 'less.fasta')

# Одночасна обробка послідовностей і хорошої (amended), і поганої (failed) якості
for fasta_file, output_file in zip([amended_consensus, failed_amended_consensus], [output_amended, output_failed]):
    with open(output_file, "w") as f:
        
        for record in SeqIO.parse(fasta_file, "fasta"):
            if search_word in record.description:
                # Запис заголовка та послідовності у файл
                
                if sequencer == 'MiSeq':
                    # Замінює "4817_S21_L001|A_HA_H1" ==> "4817-S21"
                    clean_header = record.id.split('|')[0]
                elif sequencer == 'NextSeq':
                    clean_header = record.id.split('_')[0]
                
                print(f">{clean_header}", file=f)
                print(record.seq, file=f)
    step_count += 1
    print(f"[{step_count}/{num_of_steps}] Written to {str(output_file)}")

"""
БЛОК 4: ПІДГОТОВКА ЗВІТУ report.xlsx
This part is used to generate a report.xlsx file (that will be sent to the regions) 
================================================================================================================================================
"""

# Створення шаблону для вихідного звіту report.xlsx
report_df = pd.DataFrame({"id": df_metadata.index,
                          "region": None,
                          "region_ukr": None,
                          "variant": None,
                          "reference": None,
                          "clade": None,
                          "subclade": None,
                          "quality": None,
                          "ct": df_metadata['ct'].values})

report_df["quality"] = ["good" if id in amended_ids else None for id in report_df.id]

report_df['region'] = report_df['id'].map(df_metadata['region'])
report_df['region'] = report_df['region'].apply(update_location_func)

location_to_ukr_mapping = {
    'Europe / Ukraine / Vinnytsia region': 'Вінницький ОЦКПХ',
    'Europe / Ukraine / Volyn region': 'Волинський ОЦКПХ',
    'Europe / Ukraine / Dnipropetrovsk region': 'Дніпропетровський ОЦКПХ',
    'Europe / Ukraine / Zhytomyr region': 'Житомирський ОЦКПХ',
    'Europe / Ukraine / Zakarpattia region': 'Закарпатський ОЦКПХ',
    'Europe / Ukraine / Zaporizhzhia region': 'Запорізький ОЦКПХ',
    'Europe / Ukraine / Ivano-Frankivsk region': 'Ів.-Франківський ОЦКПХ',
    'Europe / Ukraine / Kyiv region': 'Київський ОЦКПХ',
    'Europe / Ukraine / Kyiv city': 'Київський МЦКПХ',
    'Europe / Ukraine / Kirovohrad region': 'Кіровоградський ОЦКПХ',
    'Europe / Ukraine / Lviv region': 'Львівський ОЦКПХ',
    'Europe / Ukraine / Mykolaiv region': 'Миколаївський ОЦКПХ',
    'Europe / Ukraine / Odesa region': 'Одеський ОЦКПХ',
    'Europe / Ukraine / Poltava region': 'Полтавський ОЦКПХ',
    'Europe / Ukraine / Rivne region': 'Рівненський ОЦКПХ',
    'Europe / Ukraine / Sumy region': 'Сумський ОЦКПХ',
    'Europe / Ukraine / Ternopil region': 'Тернопільський ОЦКПХ',
    'Europe / Ukraine / Kharkiv region': 'Харківський ОЦКПХ',
    'Europe / Ukraine / Kherson region': 'Херсонський ОЦКПХ',
    'Europe / Ukraine / Khmelnytskyi region': 'Хмельницький ОЦКПХ',
    'Europe / Ukraine / Cherkasy region': 'Черкаський ОЦКПХ',
    'Europe / Ukraine / Chernivtsi region': 'Чернівецький ОЦКПХ',
    'Europe / Ukraine / Chernihiv region': 'Чернігівський ОЦКПХ'
}

report_df['region_ukr'] = report_df['region'].map(location_to_ukr_mapping)



# Запуск зовнішнього скрипта для виконання NextClade у bash
import subprocess
subprocess.run(["bash", "run_nextclade.sh", str(run_id)])

result = subprocess.run(
    ["bash", "run_nextclade.sh", str(run_id)], 
    capture_output=True, 
    text=True
)


NEXTCLADE_OUTPUT = f"RSP{run_id}/pass_less_dir/nextclade_output"

desired_columns = [
    'id', 
    'qc.overallScore', 
    'clade', 
    'subclade', 
    'proposedSubclade', 
    'legacy-clade'
]


# Парсинг результатів
nextclade_data = []
for nextclade_csv in os.listdir(NEXTCLADE_OUTPUT):
    
    if nextclade_csv.endswith('.csv'):

        # Зчитування CSV (Nextclade за замовчуванням використовує крапку з комою)
        path_to_nextclade_csv = os.path.join(NEXTCLADE_OUTPUT, nextclade_csv)
        nextclade_df = pd.read_csv(path_to_nextclade_csv, sep=';')

        # Виокремлення ID
        nextclade_df['id'] = nextclade_df['seqName'].apply(lambda x: str(x).split('_')[0])

        # Отримання з desired_columns лише тих, що є в df.columns
        existing_cols = [col for col in desired_columns if col in nextclade_df.columns]
        nextclade_df = nextclade_df[existing_cols]

        # Додавання дадафрейму з назвою файла (щоб щоразу не відкривати файл) 
        nextclade_data.append((nextclade_csv, nextclade_df))


# Словник для зіставлення назв файлів датасетів Nextclade із назвами штамів
variant_map = {
    "flu_b_KX058884.csv": "B",
    "flu_vic_KX058884.csv": "B/Victoria",
    "flu_yam_JN993010.csv": "B/Yamagata",
    "h1n1_ha.csv": "H1N1",
    "h1n1pdm_CY121680.csv": "H1N1",
    "h1n1pdm_MW626062.csv": "H1N1",
    "h2n2_ha.csv": "H2N2",
    "h3n2_CY163680.csv": "H3N2",
    "h3n2_EPI1857216.csv": "H3N2"
}


# Пошук найкращого збігу (на основі score) для кожного зразка
for _, row in report_df.iterrows():
    sample_id = str(row['id'])
    current_quality = row['quality']

    best_score = 999999
    variant_update = None
    clade_update = None
    subclade_update = None

    # Перевірка поточного зразка по всіх датасетах
    for nextclade_csv, nextclade_df in nextclade_data:
        # Витягування специфічного рядка даних для конкретного sample_id
        match = nextclade_df[nextclade_df['id'] == sample_id]

        if not match.empty:
            score_to_compare = match['qc.overallScore'].values[0]

            # Якщо score не NaN і він менший за попередній знайдений бал, оновлюємо
            if pd.notna(score_to_compare) and best_score > score_to_compare:
                best_score = score_to_compare

                # Оновлення даних для штаму, які відповідають цьому запису
                variant_update = variant_map.get(nextclade_csv)
                clade_update = match['legacy-clade'].values[0] if 'legacy-clade' in match.columns else None
                subclade_update = match['clade'].values[0] if 'clade' in match.columns else None
    
    # Визначення фінального статусу якості
    quality_update = current_quality
    if pd.isna(current_quality):
        if variant_update is not None:
            quality_update = 'bad'
        else:
            quality_update = 'FAILED'


    # Оновлення рядка у report_df
    mask = report_df['id'].astype(str) == str(sample_id)
    report_df.loc[mask, ['variant', 'clade', 'subclade', 'quality']] = [variant_update, clade_update, subclade_update, quality_update]

step_count += 1
print(f"[{step_count}/{num_of_steps}] NextClade finished!")


# Надсилання запиту до FluSurver
url = "https://flusurver.bii.a-star.edu.sg/cgi-bin/flumapBlast3.pl"

ALL_FASTA=f"RSP{run_id}/pass_less_dir/combined_all.fasta"

payload_data = {
    'forceref': 'auto',     # Автоматичне визначення найкращого референсу (among current vaccine strains, full genomes)
    'lqicq': '1',
    'Submit': 'Submit'
}

# Відкриття файла і відправка HTTP POST-запиту
with open(ALL_FASTA, 'rb') as f:
    files_data = {'seqfile': f}
    
    response = requests.post(url, data=payload_data, files=files_data)

# Перевірка відповіді сервера
if response.status_code == 200:
    step_count += 1
    print(f"[{step_count}/{num_of_steps}] FluSurver прийняв дані✅")

# Парсинг результатів 
soup = BeautifulSoup(response.text, 'html.parser')
table = soup.find('table')

flusurver_results = {}
AA_identity_dict = {}
length_coverage_dict = {}


if table:
    # Перебір всіх рядків (tr), пропускаючи перший (заголовок)
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        # Перевірка, чи є в рядку достатньо колонок
        if len(cols) >= 5:
            # Відбір першої колонки (Query), очистка від пробілів
            raw_id = cols[0].text.strip()
            # Відрізання всього після першого нижнього підкреслення (напр. '5689_S4...' -> '5689')
            clean_id = raw_id.split('_')[0]
                    
            # Відбір третьої колонки (Best reference hit)
            reference_hit = cols[2].text.strip()

            # Відкидання варіанта, за якого FluSurver взяв зразок, але не знайшов йому референс
            if 'hit' in reference_hit or 'not' in reference_hit:
                reference_hit = ''
                    
            # Відкидання "HA " (якщо є пробіл, береться все, що ПІСЛЯ нього)
            if ' ' in reference_hit:
                reference_hit = reference_hit.split(' ', 1)[1]
            
            # Відкидання дужки "(H1N1)" (розбивка по дужці і збережння ПЕРШОЇ частину)  
            reference_hit = reference_hit.split('(')[0]
            flusurver_results[clean_id] = reference_hit


            AA_identity_dict[clean_id] = cols[3].text.strip()
            length_coverage_dict[clean_id] = cols[4].text.strip()


report_df['reference'] = report_df['id'].astype(str).map(flusurver_results)
report_df['AA_identity'] = report_df['id'].astype(str).map(AA_identity_dict)
report_df['length_coverage'] = report_df['id'].astype(str).map(length_coverage_dict)

# Визначення правильного порядку виведення рядків
custom_order = ['good', 'bad', 'FAILED']

# Перетворення колонки на категорійну з потрібним порядком
report_df['quality'] = pd.Categorical(report_df['quality'], categories=custom_order, ordered=True)
report_df = report_df.sort_values(by='quality')


# Перелік колонок, які зберігаються у звіт
report_df[['id', 'region_ukr', 'variant', 'reference', 'clade', 'subclade', 'quality', 'ct', 'AA_identity', 'length_coverage']].to_excel(
    f"RSP{run_id}/report.xlsx", 
    index=False, 
    engine='openpyxl'
)


print(report_df)