#!/usr/bin/env python3.8
# coding=utf-8

from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import os
from matplotlib import rcParams

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def get_dataframe(filename: str, verbose: bool = False) -> pd.DataFrame:
    """ Prepare data and return dataframe .
        Function was taken from previous exercise.
    """ 

    if os.path.isfile(filename):

        # reading dafarame
        df = pd.read_pickle(filename)

        # crating new column with date -- is duplicate of p2a
        df["date"] = pd.to_datetime(df["p2a"])

        # converting columns with types object to category except "region" column
        for col in df:
            if df[col].dtype == 'object':
                if col != 'region':
                    df[col] = df[col].astype('category')

        return df

    else:
        print(
            f"Invalid path to file {os.path.dirname(os.path.realpath(__file__))}/{filename}"
        )
        exit(-1)


def make_table(s: pd.Series):
    """ Compose dataframe from given series and months and seasons, and create a table from dataframe.
        Print the table to stdout in latex format. 
        Also we find the worst month and return it to second function.
    """
    seasons = ["Zima", "Zima", "Zima", "Jar", "Jar", "Jar",
               "Leto", "Leto", "Leto", "Jesen", "Jesen", "Jesen"]

    pd_seasons = pd.Series(seasons)
    pd_months = pd.Series(MONTHS)
    frame = {'Avg': s, "Month": pd_months, 'Season': pd_seasons}
    result_df = pd.DataFrame(frame)
    result_df["Season"] = result_df["Season"].shift(1)
    result_df["Month"] = result_df["Month"].shift(1)

    max_acc_cnt = result_df["Avg"].max()

    index = result_df.index[result_df["Avg"] == max_acc_cnt]
    worst_month = result_df["Month"][index]

    result_df = result_df.iloc[1:]
    result_df = result_df.set_index(["Season", "Month"])
    # result_df = result_df.transpose()





    print(result_df.to_latex(multirow=True,
                             multicolumn=False, bold_rows=True, escape=True))
    # print(result_df)
    return worst_month, max_acc_cnt

def plot_graph(df: pd.DataFrame,
               fig_location: str = None,
               show_figure: bool = False):
    """ Plot a figure contistng of two graphs, one shows number of accidents per month and second averages that data on seasons """

    # filter data that are accident with wild game
    df2 = df.loc[df["p6"] == "5"]
    # take only needed columns
    df2 = df2[["p1", "date"]]

    df3 = df2.groupby([df['date'].dt.year.rename('year'),
                       df['date'].dt.month.rename('month')]).count()

    df3 = df3.reset_index()
    # count number of times month has data in dataframe and store in dict
    month_records = df3['month'].value_counts().sort_values(
        ascending=False).to_dict()

    # series with sums of accident counts for each months
    per_month_acc_cnt = df3.groupby('month')["p1"].sum().rename('accident_cnt')
    
    # create series from dictionary
    month_records_series = pd.Series(month_records)
    
    # devide seires with record numbers  and get a final series with avg
    avg_ser = per_month_acc_cnt.div(month_records_series)
    # take last element
    last_elem = avg_ser[-1:]
    # cut last element
    rest_elem = avg_ser[:-1]

    # connet into new dataframe with corerctly ordered values
    new_df = last_elem.append(rest_elem)

    # generate table for latex
    worst_month, worst_stat = make_table(new_df)

    moj = np.array_split(new_df, 4)
    moj = np.array(moj)
    f_df = pd.DataFrame(moj)
    tf_df = f_df.transpose()

    seasons = ["Zima", "Jar", "Leto", "Jesen"]
    # set column values to seasons
    tf_df.columns = seasons
    # define figure for both subplots
    f, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 7))
    # color list for season graph
    ax1_colors = ["blue", "green", "red", "orange"]
    avg = tf_df.mean()
    spring_avg = avg['Jar']
    winter_avg = avg['Zima']
    rest_avg = (avg['Jar'] + avg['Leto'] + avg['Jesen']) / 3

    avg.plot(ax=ax1, kind="bar", color=ax1_colors)
    # color list for months graph
    ax2_colors = ["blue", "blue", "blue", "green", "green", "green",
          "red", "red", "red", "orange", "orange", "orange"]
    avg_ser.plot(ax=ax2, kind="bar", color=ax2_colors)

    ax2.set_xticklabels(MONTHS)

    ax1.set_ylim([600, 1200])
    ax1.color = "red"

    ax1.set_title("Nehody so zverinou v Ceskej republike")
    ax1.set_ylabel("Priemerny pocet nehod")
    ax2.set_ylabel("Priemerny pocet nehod")

    f.tight_layout()

    if fig_location:
        plt.savefig(fig_location)

    if show_figure:
        plt.show()

    print(f"Primerny pocet nehod s divokou zverou v Zime: {winter_avg:.2f}.")
    print(
        f"Primerny pocet nehod s divokou zverou na zvysok roka: {rest_avg:.2f}.")
    print(f"Primerny pocet nehod s divokou zverou na Jar: {spring_avg:.2f}, a to hlavne v {worst_month.values[0]}i, kedy je najvyssia hodnota nehodovsoti {worst_stat:.2f}.")


if __name__ == "__main__":
    df = get_dataframe("accidents.pkl.gz")
    plot_graph(df, "fig.png", False)
