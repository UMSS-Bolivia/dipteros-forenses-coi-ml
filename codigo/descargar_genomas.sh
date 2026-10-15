#!/usr/bin/env bash
# Descarga los genomas de referencia (no se incluyen en el repositorio por su tamaño).
# Uso: bash descargar_genomas.sh CARPETA_DESTINO
set -e
DEST="${1:-genomas}"
mkdir -p "$DEST" && cd "$DEST"

# 1) NCBI Datasets: genoma, GFF3, CDS y proteínas cuando existen
for acc in GCA_014635995.1 GCA_942486065.2 GCF_030504385.1 GCF_022045245.1; do
  datasets download genome accession "$acc" --include genome,gff3,cds,protein --filename "$acc.zip"
  unzip -q -o "$acc.zip" -d "$acc"
  (cd "$acc" && md5sum -c --quiet md5sum.txt && echo "$acc: MD5 OK")
done

# 2) Aldrichina grahami (GigaDB 10.5524/100673)
G=https://s3.ap-northeast-1.wasabisys.com/gigadb-datasets/live/pub/10.5524/100001_101000/100673
mkdir -p aldrichina_grahami && cd aldrichina_grahami
for f in assembly.fasta coding_gene_annotation.gff coding_gene_nucleotide_sequences.fas coding_gene_translated_sequences.fas 100673.md5; do
  curl -fO "$G/$f"
done
grep -E "assembly.fasta|coding_gene" 100673.md5 | md5sum -c -
cd ..

# 3) Calliphora vomitoria: anotación y proteínas de Ensembl (versión 2024_05)
E=https://ftp.ebi.ac.uk/pub/ensemblorganisms/GCA/942/486/065/2/ensembl/2024_05/geneset
mkdir -p ensembl_calliphora_vomitoria && cd ensembl_calliphora_vomitoria
for f in genes.gff3.gz cdna.fa.bgz pep.fa.bgz; do curl -fO "$E/$f"; done
echo "Descarga completa en $DEST"
