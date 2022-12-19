#!/usr/bin/env python
import matplotlib.pyplot as plt
import csv
import numpy as np
import matplotlib
import os
from os.path import exists
from os import walk


def get_data_files(folder, file_ending=""):
    data_folders = [(file, [tmp for tmp in get_files(os.path.join(folder,file)) if tmp[0] == 'results.csv'][0][1]) for file in os.listdir(folder) if file.split('_')[-1].isdigit()]
    #data_folders = [(file, folder) for file, folder in data_folders if int(file[-1]) >=3 and file[0] == 'a']
    return data_folders
    

def get_files(folder, folder_start=""):
    return [(file,os.path.join(folder,file)) for file in os.listdir(folder) if file.startswith(folder_start)]

def get_data(type_file):
    data = {}
    appearances = {}
    for name, file in type_file:
        name = name[:-2]
        values = data.get(name, {})
        with open(file, "r") as f:
            csvData = csv.DictReader(f)
            for line in csvData:
                if float(line["prr"]) < 0.0001:
                    continue
                src = line["sport"]
                if line["protocol"] == "tcp" and not (int(src)<=100 or (int(src) > 200 and int(src) <= 300)):
                    continue
                if line["protocol"] == "udp" and not (int(src)<=100 or (int(src) > 300 and int(src) <= 400)):
                    continue
                values[src] = values.get(src, {})
                values[src]["protocol"] = line["protocol"]
                if(line["protocol"] == "udp"):
                    values[src]["data"] = values[src].get("data", [])
                    values[src]["data"].append(float(line["delay"]))
                else:
                    values[src]["data"] = values[src].get("data", [])
                    values[src]["data"].append(float(line["fct"]))
        data[name] = values
    for name, values in data.items():
        for port, items in values.items():
            items["data"] = sum(items["data"])/len(items["data"])
    return data

def refine_data(data, filter_big=False):
    rd = {}
    for name, d in data.items():
        rd[name] = {}
        rd[name]["udp"] = []
        rd[name]["tcp"] = []
        for port, dd in d.items():
            rd[name][dd['protocol']].append(dd['data'])
        rd[name][dd['protocol']] = [val for val in rd[name][dd['protocol']] if not filter_big or val < 35]
    return rd

def get_boxes(boxes, data, proto, var):
    for name, data in data.items():
        if var == "code":
            name = "_".join(name.split("_")[:-1])
        else:
            name = name.split("_")[-1]
            
        delays = data[proto]
        q1, median, q3 = np.percentile(np.asarray(delays), [25, 50, 75])
        boxes.append({
            'label' : name,
            'whislo': min(delays),    # Bottom whisker position
            'q1'    : q1,    # First quartile (25th percentile)
            'med'   : median,    # Median         (50th percentile)
            'q3'    : q3,    # Third quartile (75th percentile)
            'whishi': max(delays),    # Top whisker position
            'fliers': []        # Outliers
        })

for plot_variant in ["code"]:#, "failures"]:
    data = refine_data(get_data(get_data_files(plot_variant)), False)
    for proto in ["tcp", "udp"]:
        boxes = []
        get_boxes(boxes, data, proto, plot_variant)
        fig, ax = plt.subplots(1,1, figsize = (9.25,3.5))
        ax.bxp(boxes, showfliers=False)
        if proto == "tcp":
            ax.set_title('TCP Flow FCT in seconds (Compulsory SLAs)')
        else:
            ax.set_title('UDP Delay in seconds (Compulsory SLAs)')
            
        #plt.show()
        plt.savefig(plot_variant + "_" + proto + ".pdf", bbox_inches="tight")
        # plt.close()
