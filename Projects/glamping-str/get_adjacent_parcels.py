#!/usr/bin/env python3
"""
Script to get information about adjacent parcels for a given APN in Santa Cruz County.
Helps identify neighboring lots for potential purchase.

Usage:
    python get_adjacent_parcels.py <APN>
    python get_adjacent_parcels.py 042-011-050

Requirements:
    pip install requests beautifulsoup4 geopandas shapely
"""

import sys
import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import quote_plus, urljoin
import re

class SantaCruzCountyParcelInfo:
    def __init__(self):
        self.base_url = "https://www.santacruzcounty.us"
        self.assessor_search_url = "https://www.santacruzcounty.us/assessor/property-search/"
        self.gis_url = "https://gis.santacruzcounty.us/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_parcel_info(self, apn):
        """
        Get parcel information from Santa Cruz County Assessor's website
        """
        print(f"Searching for parcel: {apn}")
        
        # Clean APN format
        apn_clean = apn.strip().replace('-', '')
        if len(apn_clean) == 9:
            apn_formatted = f"{apn_clean[0:3]}-{apn_clean[3:6]}-{apn_clean[6:9]}"
        else:
            apn_formatted = apn
        
        try:
            # Try the assessor's property search
            params = {
                'searchtype': 'apn',
                'searchvalue': apn_formatted
            }
            
            response = self.session.get(self.assessor_search_url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for parcel information in the response
            # This will need to be adjusted based on actual website structure
            parcel_data = self._parse_assessor_response(soup, apn_formatted)
            
            if parcel_data:
                return parcel_data
            else:
                print(f"Could not find parcel {apn_formatted} through assessor search")
                return None
                
        except Exception as e:
            print(f"Error searching for parcel {apn}: {str(e)}")
            return None
    
    def _parse_assessor_response(self, soup, apn):
        """
        Parse the assessor's website response to extract parcel data
        Note: This is a placeholder - actual implementation depends on website structure
        """
        # Placeholder implementation - in reality, we'd need to inspect the actual website
        # and adjust selectors accordingly
        
        parcel_info = {
            'apn': apn,
            'owner_name': 'Not found',
            'mailing_address': 'Not found',
            'property_address': 'Not found',
            'use_code': 'Not found',
            'tax_rate_area': 'Not found',
            'assessed_value': 'Not found',
            'year_built': 'Not found',
            'lot_size': 'Not found',
            'building_sqft': 'Not found'
        }
        
        # Try to find common data patterns
        text_content = soup.get_text()
        
        # Look for owner information
        owner_patterns = [
            r'Owner Name[:\s]*([^\n\r]+)',
            r'Assessed Owner[:\s]*([^\n\r]+)',
            r'Property Owner[:\s]*([^\n\r]+)'
        ]
        
        for pattern in owner_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                parcel_info['owner_name'] = match.group(1).strip()
                break
        
        # Look for mailing address
        address_patterns = [
            r'Mailing Address[:\s]*([^\n\r]+(?:\n\s*[^\n\r]+)*)',
            r'Owner Mailing Address[:\s]*([^\n\r]+(?:\n\s*[^\n\r]+)*)'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE | re.DOTALL)
            if match:
                parcel_info['mailing_address'] = match.group(1).strip()
                break
        
        return parcel_info
    
    def get_adjacent_parcels_via_gis(self, apn):
        """
        Use GIS tools to find adjacent parcels
        Note: This would require access to Santa Cruz County's GIS API or web services
        """
        print(f"Finding adjacent parcels for {apn} via GIS...")
        
        # This is a placeholder for GIS functionality
        # In practice, you would:
        # 1. Get the parcel geometry for the input APN from GIS services
        # 2. Use a spatial query to find parcels that touch or intersect with a buffer
        # 3. Return the APNs of adjacent parcels
        
        # For now, return a mock response showing how this would work
        print("GIS functionality would be implemented here using:")
        print("- Santa Cruz County GIS REST API")
        print("- ArcGIS REST services")
        print("- Or direct database query if access is available")
        
        # Return mock adjacent APNs for demonstration
        # In reality, these would be calculated based on actual parcel boundaries
        mock_adjacent = [
            f"{apn[0:3]}-{apn[4:6]}-{int(apn[7:9]) + 1:02d}",  # Increment last two digits
            f"{apn[0:3]}-{int(apn[4:6]) + 1:02d}-{apn[7:9]}",  # Increment middle two digits
            f"{int(apn[0:3]) + 1:03d}-{apn[4:6]}-{apn[7:9]}",  # Increment first three digits
        ]
        
        return mock_adjacent
    
    def get_adjacent_parcel_info(self, apn):
        """
        Main function to get information about adjacent parcels
        """
        print(f"Getting information for parcel {apn} and its adjacent parcels\n")
        
        # Get info for the main parcel
        main_parcel = self.get_parcel_info(apn)
        if not main_parcel:
            print(f"Could not retrieve information for main parcel {apn}")
            return None
        
        print(f"Main Parcel Info:")
        print(json.dumps(main_parcel, indent=2))
        print("\n" + "="*50 + "\n")
        
        # Get adjacent parcels
        adjacent_apns = self.get_adjacent_parcels_via_gis(apn)
        
        adjacent_info = []
        for adj_apn in adjacent_apns:
            print(f"Getting info for adjacent parcel: {adj_apn}")
            info = self.get_parcel_info(adj_apn)
            if info:
                adjacent_info.append(info)
            time.sleep(1)  # Be respectful to the server
        
        result = {
            'main_parcel': main_parcel,
            'adjacent_parcels': adjacent_info,
            'total_adjacent_found': len(adjacent_info)
        }
        
        return result

def main():
    if len(sys.argv) != 2:
        print("Usage: python get_adjacent_parcels.py <APN>")
        print("Example: python get_adjacent_parcels.py 042-011-050")
        sys.exit(1)
    
    apn = sys.argv[1]
    
    finder = SantaCruzCountyParcelInfo()
    result = finder.get_adjacent_parcel_info(apn)
    
    if result:
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Main Parcel: {result['main_parcel']['apn']}")
        print(f"Owner: {result['main_parcel']['owner_name']}")
        print(f"Adjacent Parcels Found: {result['total_adjacent_found']}")
        
        print("\nAdjacent Parcels:")
        for i, parcel in enumerate(result['adjacent_parcels'], 1):
            print(f"{i}. APN: {parcel['apn']}")
            print(f"   Owner: {parcel['owner_name']}")
            print(f"   Address: {parcel['mailing_address']}")
            print()
        
        # Save results to file
        output_file = f"adjacent_parcels_{apn.replace('-', '_')}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to: {output_file}")
        
    else:
        print("Failed to retrieve parcel information")
        sys.exit(1)

if __name__ == "__main__":
    main()