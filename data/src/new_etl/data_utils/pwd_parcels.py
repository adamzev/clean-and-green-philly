import geopandas as gpd

from ..classes.featurelayer import FeatureLayer
from ..constants.services import PWD_PARCELS_QUERY
from ..metadata.metadata_utils import provide_metadata


def transform_pwd_parcels_gdf(pwd_parcels_gdf: gpd.GeoDataFrame):
    """
    Transforms the PWD parcels GeoDataFrame in place by dropping rows with null 'brt_id' and
    renaming 'brt_id' to 'opa_id'.

    Args:
        gdf (gpd.GeoDataFrame): The input GeoDataFrame containing PWD parcels data.

    """
    # Drop rows with null brt_id, rename to opa_id, and validate geometries
    pwd_parcels_gdf.dropna(subset=["brt_id"], inplace=True)
    pwd_parcels_gdf.rename(columns={"brt_id": "opa_id"}, inplace=True)
    pwd_parcels_gdf["geometry"] = pwd_parcels_gdf["geometry"].make_valid()

    # Ensure geometries are polygons or multipolygons
    if not all(pwd_parcels_gdf.geometry.type.isin(["Polygon", "MultiPolygon"])):
        raise ValueError("Some geometries are not polygons or multipolygons.")


def merge_pwd_parcels_gdf(
    primary_featurelayer_gdf: gpd.GeoDataFrame, pwd_parcels_gdf: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    # Join geometries from PWD parcels
    # Temporarily drop geometry from the primary feature layer

    # Filter PWD parcels to just the opa_ids in primary
    opa_ids_in_primary = primary_featurelayer_gdf["opa_id"].unique()
    pwd_subset = pwd_parcels_gdf[pwd_parcels_gdf["opa_id"].isin(opa_ids_in_primary)]

    # Count how many of those are missing geometry
    no_geometry_count = pwd_subset["geometry"].isnull().sum()
    pwd_parcels_gdf_unique_opa_id = pwd_parcels_gdf.drop_duplicates(subset="opa_id")
    primary_featurelayer_gdf_unique_opa_id = primary_featurelayer_gdf.drop_duplicates(
        subset="opa_id"
    )

    pwd_parcels_gdf_indexed = pwd_parcels_gdf_unique_opa_id.set_index("opa_id")
    merged_gdf_indexed = primary_featurelayer_gdf_unique_opa_id.set_index("opa_id")

    merged_gdf_indexed.update(
        pwd_parcels_gdf_indexed[["geometry"]],
    )
    merged_gdf = merged_gdf_indexed.reset_index()

    print("Number of observations retaining point geometry:", no_geometry_count)
    return merged_gdf


@provide_metadata()
def pwd_parcels(primary_featurelayer: FeatureLayer) -> FeatureLayer:
    """
    Updates the primary feature layer by replacing its geometry column with validated
    geometries from PWD parcels data. Retains point geometry for rows with no polygon
    geometry available.

    Args:
        primary_featurelayer (FeatureLayer): The primary feature layer to update.

    Returns:
        FeatureLayer: The updated primary feature layer with geometries replaced
                      by those from PWD parcels or retained from the original layer if no match.

    Columns Updated:
        geometry: The geometry column is updated with validated geometries from PWD parcels.

    Primary Feature Layer Columns Referenced:
        opa_id, geometry

    Tagline:
        Improve geometry with PWD parcels data.

    Source:
        https://phl.carto.com/api/v2/sql
    """
    # Load PWD parcels
    pwd_parcels = FeatureLayer(
        name="PWD Parcels",
        carto_sql_queries=PWD_PARCELS_QUERY,
        use_wkb_geom_field="the_geom",
        cols=["brt_id"],
    )

    pwd_parcels_gdf = pwd_parcels.gdf

    transform_pwd_parcels_gdf(pwd_parcels_gdf)

    primary_featurelayer.gdf = merge_pwd_parcels_gdf(
        primary_featurelayer.gdf, pwd_parcels_gdf
    )

    return primary_featurelayer
