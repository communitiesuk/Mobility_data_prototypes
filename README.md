# Mobility data innovation project
The Ministry for Housing, Communities and Local Government (MHLCG, previously DLUHC) has run a data innovation project developing data prototypes using mobility data from O2 Motion.
The data product from O2 Motion we use is anonymised and aggregated origin-destination journey counts at MSOA level.

# The code structure
The main branch is protected, and all of the code which sits in main has been reviewed by the project team.
We're working on a series of prototypes and experimental analyses using this data. The development work is in separate branches, and merged into main when reviewed.

Most of our prototypes are stored in ```analysis/```, with some in ```notebooks/```. 
We have common code and function in ```src/```

## Commonly used public data sources
Our code points to MHCLG's storage, but quite a lot of the data is publicly available.
Here's a non-exhaustive list of data sources:
### Shapefiles
[2011 MSOAs](https://geoportal.statistics.gov.uk/search?q=BDY_MSOA%20DEC_2011&sort=Title%7Ctitle%7Casc)

[2011 Intermediate Zones](https://spatialdata.gov.scot/geonetwork/srv/api/records/389787c0-697d-4824-9ca9-9ce8cb79d6f5)

[2011 Northern Ireland SOAs](https://www.nisra.gov.uk/publications/super-output-area-boundaries-gis-format)

[2022 Built Up Areas](https://geoportal.statistics.gov.uk/datasets/ons::built-up-areas-december-2022-boundaries-gb-bgg/about)

[ONS public transport isochrones](https://geoportal.statistics.gov.uk/search?q=PRD_ISO&sort=Date%20Created%7Ccreated%7Cdesc)

[Population weighted centroids for MSOAs](https://geoportal.statistics.gov.uk/datasets/c0e3f920e20e41b3a994dd7fc7333c91_0/explore)

### Auxillary data
[MSOA population](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/middlesuperoutputareamidyearpopulationestimates)

[IZ population](https://statistics.gov.scot/data/population-estimates-2011-datazone-linked-dataset)

[SOA population](https://www.nisra.gov.uk/statistics/population/population-estimates-small-geographical-areas)

[BUA population](https://www.ons.gov.uk/peoplepopulationandcommunity/housing/datasets/townsandcitiescharacteristicsofbuiltupareasenglandandwalescensus2021)

### Mapping
[We use the Ordnance Survey API for basemaps](https://www.ordnancesurvey.co.uk/products/os-maps-api)
# Prototypes
## Local travel areas
```analysis/Local_travel_areas/```

For communities (MSOAs) or towns (BUAs), we find the area containing X% (default 90%) of destinations for trips originating from our origin.
This gives the area in which people spend the majority of their day-to-day life.
## Economic integration
```analysis/Local_travel_areas/```

For towns and cities, we find the most important larger settlements, based on travel patterns.
This give wider context about the economic circumstances for towns, and their interdependecnes.
## Functional economic areas (FEAs)
```analysis/FEAs/```

We use network graph analysis to group MSOAs into relatively self-contained economic communities.
## Local intelligence : town footfall
```analysis/adhoc/ldc_towns_analysis/```

For towns we construct summary metrics to contribute to town data packs.
MHCLG has published these data packs: https://www.gov.uk/government/publications/long-term-plan-for-towns-data-packs-for-55-towns
## Catchment areas
```analysis/Local_travel_areas/```

For a given destination, either a BUA or MSOA, we find the region where the majority of travel originated from.
This gives us a measure of the catchment area of effect for local changes.
## Destination seasonality
```/notebooks/seasonality```

We look at the variation of trips to destinations through the year and identify local areas with highly seasonal travel patterns.
## Comparison with public transport isochrones
```/analysis/isochrone_exceedance/```

The ONS have published spatial data on the areas which can be reached within 15, 30, 45, and 60 minutes via walking and public transport.
We compare these to observed travel patterns.
## Trip expectedness prototyping
```/analysis/unexpectedness/```

We have developed a prototype for training a neural network algorithm on national travel patterns to then compare local areas and find the journeys which are most over- or under-observed.
## Origin-destination matrix decomposition
```/analysis/eigenvectors/```

To investigate functional economic areas, we experimented with casting the origin-destination data as a square matrix and mapping the dominant eigenvectors.
## Commuter flow prototyping
```/analysis/Commuterflows/```

Tests of comparing commuter flow methods with the O2 data.
## City centre identification
```/analysis/adhoc/find_city_centres```

A quick prototype of using population movement data to define where the centre of cities is located.
# The code environment
The project is primarily written in python. We have a shared environment - environment.yml

The terminal command to build a new environment with conda is:
``` conda env create -f environment.yml ```
For reference, the command to use an existing environment (called mobility) is:
``` conda activate mobility ``` 

If you add new python packages during a prototype, include them in the PR for that branch.
To re-write out the environment, use:
``` conda env export > environment.yml ```
When an environment YAML has been updated, to update an existing environment, use:
```conda env update --name mobility --file environment.yml --prune```


# Data
For MHCLG users, the data is hosted internally on the Consolidated Data Store. If the SQL queries give errors when running, this is *probably* caused by permissions for the data table on the CDS - check with the project team on this.
