from Bio import SeqIO
import pandas as pd

# Файли
fasta_file = "Metadata_table_prep/all.fasta"

# Зчитування fasta та Excel
records = list(SeqIO.parse(fasta_file, "fasta"))

# Отримання ідентифікаторів із fasta (після другого '/')
fasta_ids = set()
for record in records:
    parts = record.id.split("/")
    if len(parts) > 2:
        fasta_ids.add(parts[2])  # третя частина (після другого '/')




print(fasta_ids)
