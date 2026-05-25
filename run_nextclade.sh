
# Завантаження потрібних датасетів NextClade

# nextclade dataset get --name 'nextstrain/flu/h1n1pdm/ha/MW626062' --output-dir 'nextclade_datasets/h1n1pdm_MW626062'
# nextclade dataset get --name 'nextstrain/flu/h3n2/ha/EPI1857216' --output-dir 'nextclade_datasets/h3n2_EPI1857216'
# nextclade dataset get --name 'nextstrain/flu/b/ha/KX058884' --output-dir 'nextclade_datasets/flu_b_KX058884'
# nextclade dataset get --name 'nextstrain/flu/vic/ha/KX058884' --output-dir 'nextclade_datasets/flu_vic_KX058884'
# nextclade dataset get --name 'nextstrain/flu/yam/ha/JN993010' --output-dir 'nextclade_datasets/flu_yam_JN993010'
# nextclade dataset get --name 'nextstrain/flu/h3n2/ha/CY163680' --output-dir 'nextclade_datasets/h3n2_CY163680'
# nextclade dataset get --name 'nextstrain/flu/h1n1pdm/ha/CY121680' --output-dir 'nextclade_datasets/h1n1pdm_CY121680'
# nextclade dataset get --name 'nextstrain/flu/h1n1/ha' --output-dir 'nextclade_datasets/h1n1_ha'
# nextclade dataset get --name 'nextstrain/flu/h2n2/ha' --output-dir 'nextclade_datasets/h2n2_ha'

# ВАЖЛИВО!!! НАЛАШТУВАТИ ПОТРІБНЕ СЕРЕДОВИЩЕ
source /home/v.ostash/miniconda3/etc/profile.d/conda.sh
conda activate my_env


# Шлях до завантажених датасетів
DATASETS_DIR="/home/v.ostash/databases/nextclade_datasets"

# Зчитування ID запуску з першого аргументу скрипта
RUN_ID=$1
RUN_DIR="RSP${RUN_ID}/pass_less_dir"

# Визначення шляхів до вхідних fasta-файлів
PASSED_DIR="RSP${RUN_ID}/pass_less_dir/passed.fasta"
LESS_DIR="RSP${RUN_ID}/pass_less_dir/less.fasta"
ALL_FASTA="RSP${RUN_ID}/pass_less_dir/combined_all.fasta"

# Об'єднання двох файлів
cat "$PASSED_DIR" "$LESS_DIR" > "$ALL_FASTA"

# Очищення та створення нової директорії для результатів nextclade
NEXTCLADE_OUTPUT="RSP${RUN_ID}/pass_less_dir/nextclade_output"
rm -rf "$NEXTCLADE_OUTPUT"
mkdir -p "$NEXTCLADE_OUTPUT"

# Перебір кожного датасету в директорії для аналізу
for DATASET in "$DATASETS_DIR"/*; do
    
    # Отримання назви датасету для формування імені вихідного файлу
    DS_NAME=$(basename "$DATASET")

    # Запуск nextcladeі
    nextclade run \
        --input-dataset "$DATASET" \
        --output-csv "$NEXTCLADE_OUTPUT/${DS_NAME}.csv" \
        "$ALL_FASTA" \
        --silent

done

