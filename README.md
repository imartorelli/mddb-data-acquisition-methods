# mddb-data-acquisition-methods

description: a collection of information acquisition methods for the MycoDiversityDataBase (MDDB)

# List of methods that can be used for collecting information from sources.

## Description 
Sources can be open publications (i.e. such as journal articles) and structured information obtained from records stored in available archives (i.e. ncbi databases). This method was developed when we are not able to use the `DataBankList` attribute value of PubMed database for retrieving the data source link to a scientific publication. Because the value in this PubMed field is not available, we dig in the publication source to see if there is any relevant Data source linked. This approach allows us to complete the full mapping for the creation of the MDDB relation named `datasource`, the association in which connects the MDDB Literature category to the Study category. This relationship associates the `Article` entity of Literature to `Dataset` entity of the Study.

## related dataset resources 

- please refer to [DOI]() for the complete data schema of MDDB

## folder overview

1. PDF-parse-collect.py : a script where you provide the DOI of the article and collects the data sources related to the publication (source: ../LU_projects/methods/scripts/Data_acquisition/FetchSRAfromPDF/UpdatedVersion) upload




