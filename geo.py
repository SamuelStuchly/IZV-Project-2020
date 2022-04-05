#!/usr/bin/python3.8
# coding=utf-8
import pandas as pd
import geopandas
import matplotlib.pyplot as plt
import contextily as ctx
import sklearn.cluster
import numpy as np

# muzeze pridat vlastni knihovny


def make_geo(df: pd.DataFrame) -> geopandas.GeoDataFrame:
    """ Konvertovani dataframe do geopandas.GeoDataFrame se spravnym kodovani

        Keyword arguments:
        df -- DataFrame na spracovanie
    """

    # select only useful columns
    df = df[["p5a", "d", "e", "region"]]
    # remove unset values
    df = df.dropna(subset=["d", "e"])
    # create geodataframe with correct crs S-JTSK
    gdf = geopandas.GeoDataFrame(
        df, geometry=geopandas.points_from_xy(df.d, df.e), crs="EPSG:5514"
    )

    return gdf


def plot_geo(
        gdf: geopandas.GeoDataFrame,
        fig_location: str = None,
        show_figure: bool = False):
    """ Vykresleni grafu s dvemi podgrafy podle lokality nehody

        Keyword arguments:
        gdf -- GeoDataFrame s datami na spracovanie
        fig_location -- cesta kam sa ulozi vysledna figure
        show_figure -- bool rozhodujuci ci sa ukaze graph
    """

    # only Plzensky kraj
    gdf = gdf.loc[gdf["region"] == "PLK"]

    # prevent blurry map - Web Mercator projection
    gdf = gdf.to_crs("epsg:3857")

    # figure
    f, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 8))
    # plot subplots
    gdf.loc[gdf["p5a"] == 1].plot(ax=ax1, markersize=1, color="tab:red")
    gdf.loc[gdf["p5a"] == 2].plot(ax=ax2, markersize=1, color="tab:green")

    # put TonerLite map as a background
    ctx.add_basemap(
        ax1,
        crs=gdf.crs.to_string(),
        source=ctx.providers.Stamen.TonerLite,
        alpha=0.9)
    ctx.add_basemap(
        ax2,
        crs=gdf.crs.to_string(),
        source=ctx.providers.Stamen.TonerLite,
        alpha=0.9)
    # turn off axes
    ax1.axis("off")
    ax2.axis("off")
    # set titles
    ax1.set_title("Nehody v obci - Plzensky Kraj")
    ax2.set_title("Nehody mimo obec - Plzensky Kraj")

    # get limits of subplots
    xmin1, xmax1 = ax1.get_xlim()
    ymin1, ymax1 = ax1.get_ylim()

    xmin2, xmax2 = ax2.get_xlim()
    ymin2, ymax2 = ax2.get_ylim()

    xmin = min(xmin1, xmin2)
    xmax = max(xmax1, xmax2)
    ymin = min(ymin1, ymin2)
    ymax = max(ymax1, ymax2)

    # set both subplots to same limits
    ax1.set_xlim(xmin, xmax)
    ax2.set_xlim(xmin, xmax)

    ax1.set_ylim(ymin, ymax)
    ax2.set_ylim(ymin, ymax)

    # set tight layout
    f.tight_layout()
    # make sure titles arent cut off
    plt.subplots_adjust(top=0.97)

    if fig_location is not None:
        plt.savefig(fig_location)

    if show_figure:
        plt.show()


def plot_cluster(
        gdf: geopandas.GeoDataFrame,
        fig_location: str = None,
        show_figure: bool = False):
    """ Vykresleni grafu s lokalitou vsech nehod v kraji shlukovanych do clusteru

        Keyword arguments:
        gdf -- GeoDataFrame s datami na spracovanie
        fig_location -- cesta kam sa ulozi vysledna figure
        show_figure -- bool rozhodujuci ci sa ukaze graph
    """

    # choose region
    gdf = gdf.loc[gdf["region"] == "PLK"]

    # prevent blurry map - Web Mercator projection
    gdf = gdf.to_crs("epsg:3857")

    coords = np.dstack([gdf.geometry.x, gdf.geometry.y]).reshape(-1, 2)

    # 22 seems to be visually optimal number of clusters

    model = sklearn.cluster.MiniBatchKMeans(n_clusters=22).fit(coords)

    gdf2 = gdf.copy()
    gdf2["cluster"] = model.labels_

    # aggregate to get count of accidents for each cluster
    gdf2 = gdf2.dissolve(by="cluster", aggfunc={"region": "count"}).rename(
        columns=dict(region="cnt")
    )

    gdf_coords = geopandas.GeoDataFrame(
        geometry=geopandas.points_from_xy(
            model.cluster_centers_[:, 0], model.cluster_centers_[:, 1]
        )
    )

    # merge and set geometry_y as the geometry fot the geodataframe
    gdf3 = gdf2.merge(
        gdf_coords,
        left_on="cluster",
        right_index=True).set_geometry("geometry_y")

    # plot figure
    plt.figure(figsize=(8, 8))
    ax = plt.gca()

    # grey point for every accident
    gdf.plot(ax=ax, markersize=0.5, color="tab:grey")
    # clusters ploting with color and size change beased on count "cnt"
    gdf3.plot(
        ax=ax,
        markersize=gdf3["cnt"] /
        1.5,
        column="cnt",
        legend=True,
        alpha=0.6)
    # background map
    ctx.add_basemap(
        ax, crs="epsg:3857", source=ctx.providers.Stamen.TonerLite, alpha=0.9
    )

    # turn off axes
    ax.axis("off")

    # set title
    ax.set_title("Nehody v PLK kraj")

    plt.tight_layout()

    if fig_location is not None:
        plt.savefig(fig_location)

    if show_figure:
        plt.show()


if __name__ == "__main__":
    # zde muzete delat libovolne modifikace
    gdf = make_geo(pd.read_pickle("accidents.pkl.gz"))
    plot_geo(gdf, "geo1.png", True)
    plot_cluster(gdf, "geo2.png", True)
