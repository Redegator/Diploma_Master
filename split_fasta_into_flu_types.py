from Bio import SeqIO
import pandas as pd

# Файли
fasta_file = "HA_only.fasta"


out_BH0N = open("fasta_for_trees/B_H0N1.fasta", "w")
out_AH1N = open("fasta_for_trees/A_H1N1.fasta", "w")
out_AH3N = open("fasta_for_trees/A_H3N2.fasta", "w")


records = list(SeqIO.parse(fasta_file, "fasta"))
metadata = pd.read_csv('metadata.csv')



# Отримання ідентифікаторів із fasta (після другого '/')
for record in records:
    parts = record.id.split("/")

    type_descriptor = parts[-1][-5:-1]

    # Рядок на дикій магії, який працює і шукає Region за Sample id
    region = metadata.loc[metadata["Sample"].astype(str).str.strip() == str(parts[2]).strip(), "Region"].astype(str).str.strip().iloc[0]


    record.id = parts[2] + '/' + region
    record.description = "" # Це фіксить, щоб якась ще інша діч не додавалася в назву

    # Запис у файли
    if type_descriptor == 'BH0N':
        SeqIO.write(record, out_BH0N, "fasta")
    elif type_descriptor == 'AH1N':
        SeqIO.write(record, out_AH1N, "fasta")
    elif type_descriptor == 'AH3N':
        SeqIO.write(record, out_AH3N, "fasta")
    else:
        print(f"Error for {record.id}")


out_BH0N.close()
out_AH1N.close()
out_AH3N.close()