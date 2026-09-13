# CICIDS2017 source

## Official source (gated)

The canonical host, https://www.unb.ca/cic/datasets/ids-2017.html (and its
download endpoint at https://cicresearch.ca/CICDataset/CIC-IDS-2017/), now
requires submitting a registration form (name/email/organization/job title)
before granting a download link. As of 2026-09-13 there is no ungated direct
download from the University of New Brunswick / Canadian Institute for
Cybersecurity's own infrastructure — the old direct-IP mirror
(`205.174.165.80`) now redirects back to the dataset index page instead of
serving files.

## Mirror actually used

Downloaded the 8 standard `MachineLearningCSV` files from the public,
unauthenticated Hugging Face dataset mirror:

https://huggingface.co/datasets/c01dsnap/CIC-IDS2017

- Monday-WorkingHours.pcap_ISCX.csv
- Tuesday-WorkingHours.pcap_ISCX.csv
- Wednesday-workingHours.pcap_ISCX.csv
- Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
- Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
- Friday-WorkingHours-Morning.pcap_ISCX.csv
- Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
- Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv

Verified: combined row count across all 8 files is 2,830,743, matching the
canonical CICIDS2017 total (2,830,743 rows / 78 features / 1 label column)
cited in the original CIC paper and widely reported in the literature.

Downloaded: 2026-09-13.
