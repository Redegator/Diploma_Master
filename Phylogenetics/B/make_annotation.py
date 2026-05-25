import pandas as pd
from Bio import SeqIO

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)



# Зчитування metadata
df = pd.read_csv("../../../metadata.csv")

# Зчитування FASTA
records = list(SeqIO.parse("B_H0N1.fasta", "fasta"))


# Підготовка списку результатів
rows = []
for record in records:
    sample_id = record.id.split('/')[0]
    match = df[df["Sample"].astype(str).str.strip() == str(sample_id).strip()]

    if not match.empty:
        date_str = match.iloc[0]["collection_date"]
        month = pd.to_datetime(date_str, errors="coerce").month
    else:
        month = None

    rows.append({"header": record.id, "month": month})

annotation_df = pd.DataFrame(rows)

# --- Кольори для місяців ---


colors = {
    11: "#613613",  # Листопад — темно-фіолетовий, сухе листя й сутінки
    12: "#002C80",  # Грудень — насичено-синій, зимове небо
    1:  "#84f542",  # Січень — холодний індиго, глибока зима
    2:  "#1F5E3F",  # Лютий — синьо-сталевий, передвесняний холод
    3:  "#c59104",  # Березень — темно-зелений, пробудження
    4:  "#e36b29",  # Квітень — землисто-золотистий, перші теплі дні
    5:  "#A5158C",  # Травень — насичений теракотово-помаранчевий, енергія весни
}

print(annotation_df["month"].value_counts().sort_index())

# --- Створюємо TREE_COLORS файл ---
lines = []
for _, r in annotation_df.iterrows():
    m = r["month"]
    if pd.notna(m) and int(m) in colors:
        color = colors[int(m)]
        lines.append(f'{r["header"]},label,{color}')

with open("B_annotation.txt", "w", encoding="utf-8") as f:
    f.write("TREE_COLORS\nSEPARATOR COMMA\n\nDATA\n")
    f.write("\n".join(lines))