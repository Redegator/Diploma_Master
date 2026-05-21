Цей скрипт призначений для автоматизації рутинних процесів обробки результатів біоінформатичного пайплайну MIRA 2.0 для вірусів грипу. Програма готує отримані консенсусні послідовності та метадані для завантаження в базу даних GISAID, проводить аналіз за допомогою зовнішніх інструментів (Nextclade) та автоматично генерує стандартизовані звіти для регіональних ЦКПХ.


## 1. Підготовка середовища

Переконайтеся, що активовано необхідне середовище (наприклад, Conda) та встановлено всі залежності:
```bash
# Створення та активація нового середовища (за потреби)
conda create -n flu_env python=3.10
conda activate flu_env

# Встановлення всіх залежностей за один раз
conda install -c conda-forge -c bioconda pandas biopython openpyxl beautifulsoup4 requests nextclade

```

## 2. Встановлення fluCLI

Завантажте архів із бінарним файлом для Linux (або Windows чи Apple) із вашого акаунта [GISAID](https://gisaid.org/) та розпакуйте його. Відкрийте термінал у папці з файлом і виконайте:

```bash
# Надання прав на виконання та переміщення до системної директорії
chmod +x fluCLI
sudo mv fluCLI /usr/local/bin/

# Перевірка встановлення (під час першого запуску може знадобитися авторизація)
fluCLI help

```


## 3. Налаштування Nextclade (бази даних та шляхи)

Перед першим використанням пайплайну необхідно завантажити референсні датасети вірусів грипу та налаштувати конфігурацію у файлі `run_nextclade.sh`.

1. **Завантаження датасетів:** Виконайте в терміналі наступні команди (їх також можна знайти закоментованими всередині `run_nextclade.sh`), щоб локально завантажити всі необхідні бази:
```bash
nextclade dataset get --name 'nextstrain/flu/h1n1pdm/ha/MW626062' --output-dir 'nextclade_datasets/h1n1pdm_MW626062'
nextclade dataset get --name 'nextstrain/flu/h3n2/ha/EPI1857216' --output-dir 'nextclade_datasets/h3n2_EPI1857216'
nextclade dataset get --name 'nextstrain/flu/b/ha/KX058884' --output-dir 'nextclade_datasets/flu_b_KX058884'
nextclade dataset get --name 'nextstrain/flu/vic/ha/KX058884' --output-dir 'nextclade_datasets/flu_vic_KX058884'
nextclade dataset get --name 'nextstrain/flu/yam/ha/JN993010' --output-dir 'nextclade_datasets/flu_yam_JN993010'
nextclade dataset get --name 'nextstrain/flu/h3n2/ha/CY163680' --output-dir 'nextclade_datasets/h3n2_CY163680'
nextclade dataset get --name 'nextstrain/flu/h1n1pdm/ha/CY121680' --output-dir 'nextclade_datasets/h1n1pdm_CY121680'
nextclade dataset get --name 'nextstrain/flu/h1n1/ha' --output-dir 'nextclade_datasets/h1n1_ha'
nextclade dataset get --name 'nextstrain/flu/h2n2/ha' --output-dir 'nextclade_datasets/h2n2_ha'
```

## 4. Структура файлів та папок

Для коректної роботи пайплайну критично важливо дотримуватися правильної ієрархії директорій. Усі робочі файли конкретного лабораторного запуску (наприклад, `RSP85`) мають знаходитися в окремій папці поряд із виконуваними скриптами.

### 📁 Вигляд директорії ДО запуску скрипта:

```text
Робоча_директорія/
├── process_mira.py                    # Головний Python-скрипт пайплайну
├── run_nextclade.sh                   # Bash-скрипт для локального запуску Nextclade
├── reports                            # Директорія, призначена для зберігання скриптів та шаблонів
|       ├── bulletin_gtemplate.docx        # Базовий шаблон документа Microsoft Word
|       └── bulletin_generator.py/         # Python-скрипт, який агрегує статистику з Excel-бази
└── MIRA_outputs
        └── RSP85/                             # Папка конкретного запуску (назва може бути будь-якою, що починається з "RSP")
            ├── amended_consensus.fasta        # Високоякісні консенсусні послідовності (від MIRA 2.0)
            ├── failed_amended_consensus.fasta # Послідовності, що не пройшли QC (від MIRA 2.0)
            └── metadata.xlsx                  # Метадані зразків (обов'язкові колонки: id, variant, region, ct, collection_date, sex, age, age_units)
```

## 5. Запуск скрипта

Скрипт запускається через інтерфейс командного рядка. 

**Важливо:** Відкрийте термінал **безпосередньо в робочій директорії** (там, де знаходяться `process_mira.py`, `run_nextclade.sh` та папка з результатами MIRA, наприклад `RSP85`).

Виконайте команду, передавши два параметри:
1. Обо'язковий параметр ідентифікатора запуску (наприклад, `85` або діапазон `85-88`).
2. Необов'язковий параметр типу секвенатора (`MiSeq` або `NextSeq`).

**Приклад команди:**
```bash
python process_mira.py 85 MiSeqм
```

## 6. Завантаження результатів у GISAID (gisaid_upload.sh)

Після успішного завершення роботи `process_mira.py` у папці запуску з'явиться директорія `gisaid_upload/` із файлами `gisaid_uploader.csv` та `fasta_for_gisaid.fasta`.

1. **Ручна перевірка:** Перед відправкою обов'язково відкрийте та прогляньте ці файли, щоб переконатися у коректності метаданих.
2. **Налаштування авторизації:** Відкрийте файл `gisaid_upload.sh` у текстовому редакторі та обов'язково пропишіть ваші облікові дані у параметри:
   * `--username`
   * `--password`
   * `--clientid`
3. **Відправка:** Збережіть зміни, надайте скрипту права на виконання та запустіть:

```bash
./gisaid_upload.sh 85
```

## 7. Генерація інформаційного бюлетеня (bulletin_generator.py)

Цей додатковий скрипт автоматизує створення щотижневих звітів-бюлетенів у форматі Word (`.docx`). Він зчитує статистику із загальних баз даних Excel (кількість ПЛР-тестів, секвенованих зразків тощо) та автоматично заповнює відповідні поля у шаблоні документа, зберігаючи правильне форматування (Times New Roman, 14pt).

### 📦 Додаткові залежності

Для роботи цього скрипта потрібна бібліотека `python-docx`. Встановіть її у ваше робоче середовище:

```bash
conda install -c conda-forge python-docx
```


### Налаштування перед запуском

Перед кожним запуском обов'язково відкрийте `bulletin_generator.py` у текстовому редакторі та оновіть змінні на початку файлу (дату, тиждень та шляхи до актуальних баз даних):

```python
date = '18 травня'
week = '20'

main_db_path = "../main_database/flu.xlsx"
pcr_info_path = "../../../Disk D/Мои документы/Grip/Rezultat/Звіти ПЛР/2025-2026/Зразки на грип та ГРВІ 2025 – 2026.xlsx"
```
