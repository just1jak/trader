#!/bin/bash
#
# Script to find adjacent parcel owners in Santa Cruz County
# Usage: ./find_adjacent_owners.sh <APN>
# Example: ./find_adjacent_owners.sh 042-011-050

APN="$1"

if [ -z "$APN" ]; then
    echo "Usage: $0 <APN>"
    echo "Example: $0 042-011-050"
    exit 1
fi

echo "Finding adjacent parcels for APN: $APN"
echo "========================================"

# Step 1: Get your parcel information
echo "1. Getting information for your parcel ($APN)..."
echo "   Visit: https://www.santacruzcounty.us/assessor/property-search/"
echo "   Search by APN: $APN"
echo "   Note down: Owner name, mailing address, and property address"
echo ""

# Step 2: Use GIS to find adjacent parcels
echo "2. Finding adjacent parcels using GIS..."
echo "   Visit: https://gis.santacruzcounty.us/"
echo "   Steps:"
echo "   a. Use the parcel search tool to find your parcel ($APN)"
echo "   b. Once your parcel is highlighted, use the 'Identify' tool"
echo "   c. Click on parcels immediately surrounding yours (N, S, E, W, and diagonals)"
echo "   d. For each adjacent parcel, note the APN"
echo ""
echo "   Typical adjacent APN patterns (these are examples - verify with GIS):"
echo "   - North:  $(echo $APN | awk -F- '{printf \"%03d-%02d-%02d\", $1, $2+1, $3}')"
echo "   - South:  $(echo $APN | awk -F- '{printf \"%03d-%02d-%02d\", $1, $2-1, $3}')"
echo "   - East:   $(echo $APN | awk -F- '{printf \"%03d-%02d-%02d\", $1+1, $2, $3}')"
echo "   - West:   $(echo $APN | awk -F- '{printf \"%03d-%02d-%02d\", $1-1, $2, $3}')"
echo "   - NE:     $(echo $APN | awk -F- '{printf \"%03d-%02d-%02d\", $1+1, $2+1, $3}')"
echo "   - NW:     $(echo $APN | awk -F- '{printf \"%03d-%02d-%02d\", $1-1, $2+1, $3}')"
echo "   - SE:     $(echo $APN | awk -F- '{printf \"%03d-%02d-%02d\", $1+1, $2-1, $3}')"
echo "   - SW:     $(echo $APN | awk -F- '{printf \"%03d-%02d-%02d\", $1-1, $2-1, $3}')"
echo ""

# Step 3: Get owner information for each adjacent parcel
echo "3. Getting owner information for adjacent parcels..."
echo "   For each adjacent APN found in step 2:"
echo "   a. Visit: https://www.santacruzcounty.us/assessor/property-search/"
echo "   b. Search by the adjacent APN"
echo "   c. Record the owner name and mailing address"
echo ""

# Step 4: Check tax status
echo "4. Checking tax status (optional but recommended)..."
echo "   Visit: https://www.santacruzcounty.us/taxcollector/"
echo "   Look for 'Tax Defaulted Property' or 'Delinquent Tax List'"
echo "   Check if any adjacent parcels appear on tax-defaulted lists"
echo ""

# Step 5: Create tracking spreadsheet
echo "5. Creating tracking spreadsheet..."
cat > adjacent_parcels_tracker.csv << EOF
APN,Owner Name,Mailing Address,Property Address,Use Code,Tax Status,Notes
$APN,"TO BE FILLED","TO BE FILLED","TO BE FILLED","TO BE FILLED","TO BE FILLED","Your current parcel"
EOF

echo "   Created adjacent_parcels_tracker.csv"
echo "   Fill in the information as you gather it from the assessor's website"
echo ""

echo "Next Steps:"
echo "==========="
echo "1. Use the GIS portal to identify exact adjacent APNs"
echo "2. Look up each APN on the assessor's website for owner info"
echo "3. Fill in the CSV spreadsheet with your findings"
echo "4. Check tax-defaulted lists for any adjacent parcels"
echo "5. Consider reaching out to owners via mail (most respectful approach)"
echo ""
echo "Resources:"
echo "=========="
echo "- Assessor's Office: https://www.santacruzcounty.us/assessor/"
echo "- GIS Portal: https://gis.santacruzcounty.us/"
echo "- Tax Collector: https://www.santacruzcounty.us/taxcollector/"
echo "- Recorder's Office: https://www.santacruzcounty.us/recorder/"
echo ""
echo "Tip: Consider creating a letter template explaining:"
echo "- You're a local resident planning responsible glamping development"
echo "- You're interested in discussing potential sale/lease options"
echo "- You're not a large developer seeking to flip quickly"
echo "- You value stewardship and compatibility with the area"