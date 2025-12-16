"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum. In
some way, we would like to depict results with something similar to the maps
that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def load_data():
    """Load data from the CSV files referendum/regions/departments."""
    # Referendum is semicolon-separated
    referendum = pd.read_csv('data/referendum.csv', sep=';')
    regions = pd.read_csv('data/regions.csv')
    departments = pd.read_csv('data/departments.csv')

    return referendum, regions, departments


def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.
    The columns in the final DataFrame should be
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """
    # Rename columns to match the assignment requirements
    df_reg = regions.rename(columns={'code': 'code_reg', 'name': 'name_reg'})
    df_dep = departments.rename(columns={
        'region_code': 'code_reg',
        'code': 'code_dep',
        'name': 'name_dep'
    })

    # Merge departments with regions to get region names
    merged = pd.merge(
        df_dep[['code_reg', 'code_dep', 'name_dep']],
        df_reg[['code_reg', 'name_reg']],
        on='code_reg',
        how='left'
    )

    return merged[['code_reg', 'name_reg', 'code_dep', 'name_dep']]


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum and regions_and_departments in one DataFrame.
    Drop lines relative to DOM-TOM-COM
      and French living abroad (code with 'Z').
    """
    # 1. Standardize department codes in referendum
    # to match departments.csv (padding)
    dept_code = referendum['Department code'].astype(str)
    referendum['code_dep'] = dept_code.str.zfill(2)

    # 2. Filter out 'Z' codes (DOM-TOM, etc.)
    referendum = referendum[~referendum['code_dep'].str.contains('Z')]

    # 3. Merge with regions and departments info
    merged = pd.merge(
        referendum,
        regions_and_departments,
        on='code_dep',
        how='inner'  # Use inner to automatically drop rows with no area match
    )

    return merged


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """
    # Group by code and name to aggregate sums
    results = referendum_and_areas.groupby(
        ['code_reg', 'name_reg']
    ).agg({
        'Registered': 'sum',
        'Abstentions': 'sum',
        'Null': 'sum',
        'Choice A': 'sum',
        'Choice B': 'sum'
    }).reset_index()

    # Set code_reg as index as requested by docstring
    results = results.set_index('code_reg')

    return results


def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum.

    Return a gpd.GeoDataFrame with a column 'ratio' containing the results.
    """
    # 1. Load geographic data
    regions_geo = gpd.read_file('data/regions.geojson')

    # 2. Calculate the ratio (Choice A / Expressed Ballots)
    # Expressed = Choice A + Choice B
    a = referendum_result_by_regions['Choice A']
    b = referendum_result_by_regions['Choice B']
    referendum_result_by_regions['ratio'] = a / (a + b)

    # 3. Merge geographic data with results
    # Ensure types match for merging (code should be string)
    regions_geo['code'] = regions_geo['code'].astype(str)

    # Merge on the code
    gdf = regions_geo.merge(
        referendum_result_by_regions,
        left_on='code',
        right_index=True
    )

    # 4. Plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    gdf.plot(column='ratio', ax=ax, legend=True, cmap='RdYlGn')
    ax.set_axis_off()
    ax.set_title("Referendum Results: Ratio of Choice A")

    return gdf


if __name__ == "__main__":
    referendum, df_reg, df_dep = load_data()
    regions_and_departments = merge_regions_and_departments(df_reg, df_dep)
    referendum_and_areas = merge_referendum_and_areas(
        referendum, regions_and_departments
    )
    referendum_results = compute_referendum_result_by_regions(
        referendum_and_areas
    )
    print(referendum_results)

    gdf = plot_referendum_map(referendum_results)
    plt.show()
