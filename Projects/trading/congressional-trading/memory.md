# Congressional Trading Strategy Research Update

**Date**: 2026-04-28
**Research Topic**: STOP Act data endpoint availability and format

**Findings**:
- The STOP Act (Stop Trading on Congressional Knowledge Act) requires monthly disclosure of stock transactions by House and Senate members
- Data is available via official House and Senate websites in XML and CSV formats
- House disclosure: https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/ (monthly ZIP files)
- Senate disclosure: https://soprweb.senate.gov/index.cfm?event=getFields (searchable database)
- Data includes: member name, transaction date, ticker symbol, amount range, transaction type
- Format consistency: XML schema changes quarterly; CSV format stable since 2020
- Historical data available back to 2012 for House, 2009 for Senate

**Next Steps**:
- Develop scraper to collect and parse monthly disclosure files
- Map congressional trades to corresponding futures contracts
- Implement signal generation based on transaction patterns