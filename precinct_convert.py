import pandas as pd  

precincts = pd.read_csv('/2024_Door_Attempts - bq-results-20250107-174015-1736271644789.csv')
 
county_codes = {
    'YUMA': 'YU',
    'MARICOPA': 'MC',
    'SANTA CRUZ': 'SC',
    'GILA': 'GI',
    'PIMA': 'PM',
    'PINAL': 'PN',
    'APACHE': 'AP',
    'GRAHAM': 'GM',
    'LA PAZ': 'LP',
    'MOHAVE': 'MO',
    'NAVAJO': 'NA',
    'COCHISE': 'CH',
    'YAVAPAI': 'YA',
    'COCONINO': 'CN',
    'GREENLEE': 'GN'
}

def extract_pctnum(countyname, precinctcode, county_codes):  
    try:
        precinct_int = int(float(precinctcode))  # Handles cases like 25.0 → 25
    except ValueError:
        return 'ERROR'
  
    num_part = str(precinct_int).zfill(4)
    county_prefix = county_codes.get(countyname)
    if county_prefix:
        return county_prefix + num_part  # Concatenate county code and zero-padded precinct code
    else:
        return 'ERROR'

precincts['pctnum'] = precincts.apply(lambda row: extract_pctnum(row['countyname'], row['precinctcode'], county_codes), axis=1)
precincts.to_csv('/content/modified_precincts.csv', index=False)
precincts.head()
