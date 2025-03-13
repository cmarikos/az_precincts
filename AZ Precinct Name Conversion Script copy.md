This is the script I started with. This will work if unique precinct codes.

```python
import pandas as pd  

precincts = pd.read_csv('/RAZA_c4_2024_Door_Attempts - bq-results-20250107-174015-1736271644789.csv')
 

# County to prefix dictionary
county_codes = {
	'YUMA':'YU'
	,'MARICOPA':'MC'
	,'SANTA CRUZ':'SC'
	,'GILA':'GI'
	,'PIMA':'PM'
	,'PINAL':'PN'
	,'APACHE':'AP'
	,'GRAHAM':'GM'
	,'LA PAZ':'LP'
	,'MOHAVE':'MO'
	,'NAVAJO':'NA'
	,'COCHISE':'CH'
	,'YAVAPAI':'YA'
	,'COCONINO':'CN'
	,'GREENLEE':'GN'
}

  

# Function to extract pctnum based on county and precinct code
def extract_pctnum(countyname, precinctcode, county_codes):  

	try:
		precinct_int = int(float(precinctcode)) # Handles cases like 25.0 → 25
	except ValueError:
		return 'ERROR'
  

# Ensure precinctcode is a string and zero-pad to 4 digits
num_part = str(precinct_int).zfill(4)
 

# Get the county code from the dictionary
county_codes = county_codes.get(countyname)
	if county_codes:
	return county_codes + num_part # Concatenate county code and zero-padded precinct code
	else:
		return 'ERROR'
 

#Apply to dataframe, swap out row['__'] with column names
precincts['pctnum'] = precincts.apply(lambda row: extract_pctnum(row['countyname'], row['precinctcode'], county_codes), axis=1)

  
#Export the new dataframe to csv
precincts.to_csv('/content/modified_c4precincts.csv', index=False)

#Display head to check result
precincts.head()
```

If you have a precinct name in which you need to extract numbers you can add in the following to chop the numbers off

```python
import re

def extract_pctnum(county_name, precinctcode, county_codes):
    # Some precincts in Maricopa in my file are just called "UNCODED"
    if "UNCODED" in precinctcode:
        return "ERROR"

    # Extract the last three digits
    match = re.search(r'(\d{1,3})$', precinctcode)  # Looks for up to 3 digits at the end

    if not match:
        print(f"Invalid precinct code format: {precinctcode} (County: {county_name})")  # Debugging
        return 'ERROR'

    num_part = match.group(1).zfill(4)  # Ensure it's always 4 digits

    # Get the county prefix from the dictionary
    county_code = county_codes.get(county_name)

    if county_code:
        return county_code + num_part  # Concatenate county prefix + zero-padded precinct code
    else:
        print(f"County not found: {county_name}")  # Debugging
        return 'ERROR'

precincts['pctnum'] = precincts.apply(
    lambda row: extract_pctnum(row['county_name'], row['svi_registration_national_precinct_code'], county_codes),
    axis=1
)

print(precincts[['county_name', 'svi_registration_national_precinct_code', 'pctnum']].head())
```