#!/bin/bash

# Directory containing the PDFs - adjust this path as needed
PDF_DIR="$1"

if [ -z "$PDF_DIR" ]; then
    echo "Usage: ./rename_docs.sh /path/to/pdf/directory"
    exit 1
fi

cd "$PDF_DIR" || exit 1

# Format: book<number>_p<page>_<type>.pdf
# Book number provides chronological ordering

mv "2264247.pdf"   "book20119_p538_deed.pdf"
mv "2264248.pdf"   "book20119_p540_mortgage.pdf"
mv "2266524.pdf"   "book20129_p3_municipal_lien.pdf"
mv "323439.pdf"    "book323439_p521_municipal_lien.pdf"
mv "3156402.pdf"   "book323439_p522_mortgage.pdf"
mv "4040834.pdf"   "book27144_p153_deed.pdf"
mv "4040835.pdf"   "book27144_p155_mortgage.pdf"
mv "4067436.pdf"   "book27262_p574_municipal_lien.pdf"
mv "4364240.pdf"   "book28661_p167_notice.pdf"
mv "4468597.pdf"   "book29144_p278_deed.pdf"
mv "4468598.pdf"   "book29144_p279_mortgage.pdf"
mv "4543770.pdf"   "book29519_p257_mortgage.pdf"
mv "4820896.pdf"   "book30794_p316_mortgage.pdf"
mv "5937768.pdf"   "book38562_p177_municipal_lien.pdf"
mv "5937769.pdf"   "book38562_p178_mortgage.pdf"
mv "6221162.pdf"   "book40894_p65_municipal_lien.pdf"
mv "6221163.pdf"   "book40894_p66_mortgage.pdf"
mv "20883696.pdf"  "book45667_p272_mortgage.pdf"
mv "26159323.pdf"  "book59349_p393_mortgage.pdf"
mv "26180878.pdf"  "book59515_p317_mortgage.pdf"
mv "26180879.pdf"  "book59515_p338_homestead.pdf"
mv "32656755.pdf"  "book79923_p306_discharge.pdf"
mv "32659872.pdf"  "book79945_p30_mortgage.pdf"
mv "33442839.pdf"  "book85472_p541_discharge.pdf"
mv "33445209.pdf"  "book85472_p482_municipal_lien.pdf"
mv "33445210.pdf"  "book85742_p484_deed.pdf"
mv "33445212.pdf"  "book85742_p491_mortgage.pdf"
mv "33445213..pdf" "book85742_p518_homestead.pdf"

echo "Done! Renamed $(ls *.pdf | wc -l) files."

