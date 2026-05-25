

fluCLI upload \
    --username 'ID****' \
    --password '**********' \
    --clientid 'cid-***************' \
    --metadata "RSP${1}/gisaid_upload/gisaid_uploader.csv" \
    --fasta "RSP${1}/gisaid_upload/fasta_for_gisaid.fasta" \
    --dateformat 'DDMMYYYY' \
    --log "RSP${1}/gisaid_upload/log.txt"