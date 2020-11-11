# author : Samuel Stuchly
# login : xstuch06

import os
from bs4 import BeautifulSoup
import requests
import zipfile
import csv
from io import TextIOWrapper
import numpy as np
import pickle
import gzip


class DataDownloader:
    def __init__(
        self,
        url="https://ehw.fit.vutbr.cz/izv/",
        folder="data",
        cache_filename="data_{}.pkl.gz",
    ):
        self.url = url
        self.folder = folder
        self.cache_filename = cache_filename
        self.parsed_regions = {}
        self.REGIONS = {
            "PHA": "00.csv",
            "STC": "01.csv",
            "JHC": "02.csv",
            "PLK": "03.csv",
            "ULK": "04.csv",
            "HKK": "05.csv",
            "JHM": "06.csv",
            "MSK": "07.csv",
            "OLK": "14.csv",
            "ZLK": "15.csv",
            "VYS": "16.csv",
            "PAK": "17.csv",
            "LBK": "18.csv",
            "KVK": "19.csv",
        }

        self.DATA_HEADERS = [
            "p1",
            "p36",
            "p37",
            "p2a",
            "weekday(p2a)",
            "p2b",
            "p6",
            "p7",
            "p8",
            "p9",
            "p10",
            "p11",
            "p12",
            "p13a",
            "p13b",
            "p13c",
            "p14",
            "p15",
            "p16",
            "p17",
            "p18",
            "p19",
            "p20",
            "p21",
            "p22",
            "p23",
            "p24",
            "p27",
            "p28",
            "p34",
            "p35",
            "p39",
            "p44",
            "p45a",
            "p47",
            "p48a",
            "p49",
            "p50a",
            "p50b",
            "p51",
            "p52",
            "p53",
            "p55a",
            "p57",
            "p58",
            "a",
            "b",
            "d",
            "e",
            "f",
            "g",  # 50
            "h",
            "i",
            "j",
            "k",
            "l",
            "n",
            "o",
            "p",
            "q",
            "r",  # 60
            "s",
            "t",
            "p5a",
            "region",  # added column
        ]

        self.uint8_XX_columns = [34]
        self.uint8_columns = [
            1,
            4,
            6,
            7,
            8,
            10,
            11,
            13,
            14,
            15,
            17,
            18,
            19,
            20,
            21,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            35,
            36,
            37,
            38,
            39,
            41,
            42,
            43,
            44,
            53,
            63,
        ]
        self.uint16_columns = [2, 9, 5, 12, 16, 40]
        self.uint32_columns = [56, 60, 61]
        self.uint64_columns = [0]
        self.int32_columns = [45, 46, 47, 48, 49, 57, 50]  # can be float
        self.datetime_columns = [3]
        self.string_columns = [51, 52, 54, 55, 58, 59, 62]


        # make directory in case specified path in folder var is not directoryH
        if not os.path.isdir(self.folder):
            os.makedirs(self.folder)

    def download_data(self):

        # fake header to imitate browser, source -> http://www.useragentstring.com/pages/useragentstring.php
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201"
        }

        page = requests.get(self.url, headers=headers)

        soup = BeautifulSoup(page.content, "html.parser")

        # list of <a> elements for ZIPs
        a_list = soup.find_all("a", href=True, class_="btn-primary", string="ZIP")
        # print(soup.find_all('a', class_="btn-primary",string="ZIP"))

        # list with all href paths from <a> tags in a_list
        data_paths = []
        for a in a_list:
            data_paths.append(a["href"])

        for path in data_paths:
            # check if we dont already have a file, if yes dont download it seconds time.
            if not os.path.exists(self.folder + path[4:]):
                with requests.get(self.url + path, stream=True) as r, open(
                    self.folder + path[4:], "wb"
                ) as fd:
                    print(fd)
                    for chunk in r.iter_content(chunk_size=128, decode_unicode=True):
                        fd.write(chunk)
            else:
                print(self.folder + path[4:] + " already exists -> SKIPPING")

    def make_column_arrays(self):

        numpy_arrays_list = []

        for i in range(64):
            if i in self.uint8_columns:
                numpy_arrays_list.append(self.make_numpy_array("uint8"))

            elif i in self.uint16_columns:
                numpy_arrays_list.append(self.make_numpy_array("uint16"))

            elif i in self.uint32_columns:
                numpy_arrays_list.append(self.make_numpy_array("uint32"))

            elif i in self.uint64_columns:
                numpy_arrays_list.append(self.make_numpy_array("uint64"))

            elif i in self.int32_columns:
                numpy_arrays_list.append(self.make_numpy_array("float32"))

            elif i in self.datetime_columns:
                numpy_arrays_list.append(self.make_numpy_array("datetime64"))

            elif i in self.string_columns:
                numpy_arrays_list.append(self.make_numpy_array("str"))

            elif i in self.uint8_XX_columns:
                numpy_arrays_list.append(self.make_numpy_array("uint8"))

        numpy_arrays_list.append(self.make_numpy_array("str"))

        return numpy_arrays_list

    def make_numpy_array(self, data_type, data=[]):
        return np.array([data], dtype=data_type)

    def parse_region_data(self, region):

        numpy_arrays_list = self.make_column_arrays()

        for archive in os.listdir(self.folder):
            with zipfile.ZipFile(self.folder + "/" + archive, "r") as zf:
                # print(zf.namelist()) #seznam souborů v archivu

                filename = self.REGIONS.get(region)
                with zf.open(filename, "r") as csvfile:
                    readCSV = csv.reader(
                        TextIOWrapper(csvfile, "ISO 8859-2"), delimiter=";"
                    )
                    for row in readCSV:
                        for index in range(len(row)):
                            # print(row)
                            # print(row[index])

                            value = row[index]

                            if index in self.uint8_columns:
                                my_type = "uint8"

                            elif index in self.uint16_columns:
                                my_type = "uint16"

                            elif index in self.uint32_columns:
                                if value.isdigit():
                                    my_type = "uint32"
                                else:
                                    my_type = "str"

                            elif index in self.uint64_columns:

                                my_type = "uint64"

                            elif index in self.int32_columns:

                                my_type = "float32"
                                value = value.replace(",", ".", 1)

                            elif index in self.string_columns:
                                my_type = "str"

                            elif index in self.uint8_XX_columns:
                                my_type = "uint8"
                                if value == "XX":
                                    my_type = "str"

                            if value == "":
                                value = np.asarray(None)

                            elif index in self.datetime_columns:
                                value = np.datetime64(value)
                                my_type = np.datetime64
                                #value = value.astype(my_type)

                            else:
                                value = self.make_numpy_array(my_type, value)
                                #value = value.astype(my_type)

                            # print(value.dtype)

                            numpy_arrays_list[index] = np.concatenate(
                                (numpy_arrays_list[index], value), axis=None
                            )

                            region_value = np.asarray(str(region))
                            region_value = region_value.astype("str")
                            numpy_arrays_list[-1] = np.concatenate(
                                (numpy_arrays_list[-1], region_value), axis=None
                            )  # adding region into last column

            print("ARCHIVE " + archive + "DONE !")


        return self.DATA_HEADERS, numpy_arrays_list

    def get_list(self, regions=None):
        if regions is None:
            regions = [
                "PHA",
                "STC",
                "JHC",
                "PLK",
                "ULK",
                "HKK",
                "JHM",
                "MSK",
                "OLK",
                "ZLK",
                "VYS",
                "PAK",
                "LBK",
                "KVK",
            ]

        #self.download_data()

        return_values = []

        for region in regions:
            # check if it is not in memoery
            if self.parsed_regions.get(region) is None:
                # if not in memory, check if in cache
                if os.path.exists(self.cache_filename.format(region)):
                    with gzip.open(
                        self.cache_filename.format(region), "rb"
                    ) as pickle_out:
                        return_values.append(pickle.load(pickle_out))

                # is not in cahce
                else:
                    parsed_region = self.parse_region_data(region)
                    self.parsed_regions[region] = parsed_region[1]

                    with gzip.open(
                        self.cache_filename.format(region), "wb"
                    ) as pickle_out:
                        pickle.dump(parsed_region[1], pickle_out)

                    return_values.append(parsed_region[1])

            else:
                return_values.append(self.parsed_regions.get(region))

        

        # concat data
        list_of_arrays = self.make_column_arrays()
        if len(return_values) > 1:
            print(len(return_values))
            for data_region in return_values:
                for i in range(len(list_of_arrays)):
                    list_of_arrays[i] = np.concatenate(
                        (list_of_arrays[i], data_region[i]), axis=None
                    )
        else:
            list_of_arrays = return_values[0]

        return self.DATA_HEADERS, list_of_arrays


if __name__ == "__main__":
    dd = DataDownloader()
    # dd.download_data()
    # a = dd.parse_region_data("HKK")
    # print(type(a))
    # print(a[1][-1])
    #regions = ["HKK", "JHC", "LBK"]
    regions= ["HKK"]
    a = dd.get_list(regions)

    print("---------------------------------------")
    print(f"Columns are these: {', '.join(a[0])}")
    print(f"Number of records: {a[1][0].shape[0]}")
    print(f"Regions collected in dataset are:  {', '.join(regions)}")
    print("---------------------------------------")
