#!/bin/python3

"""
This script
1. checks three folders on WLD for new csvs of interest
2. makes a local copy 
    2a. Logs what files were transfered when
3. looks for updated data and edits run_models.csv if there's new data
4. aggregateds the dataset (with minor tweaks) and saves a csv with a timestamp
"""
import os, re       # for file detection
import shutil       # for file copying
import pandas as pd # for dir state comparison
import numpy as np  # for np.nan detection
import datetime     # for logging file transfer time

# Setup ------------------------------------------------------------------------
# Get data
rootbot_path = '/run/user/1000/gvfs/smb-share:server=mw22-wldata.agron.missouri.edu,share=wldata/WashburnLab/RootBot/'
#rootbot_path = '/run/user/1000/gvfs/smb-share:server=mw22-wldata.agron.missouri.edu,share=wldata/WashburnLab'
# Store
data_cache_path = '/home/washburnj/Documents/Kick/RootbotMonitor/data_cache'
# Process and Logistics
transfer_log_path = '/home/washburnj/Documents/Kick/RootbotMonitor/data_cache/Records/transfer_log.csv'
run_models_path = '/home/washburnj/Documents/Kick/RootbotMonitor/data_cache/Controls/run_models.csv'


## Get current directory state =================================================
### Of remote ##################################################################
active_csv_list = [entry for entry in os.listdir(rootbot_path+""+"Already Scored/") if re.match("\d+-\d+-plate_\d+.csv$", entry)]
ww_csv_list = [entry for entry in os.listdir(rootbot_path+"/"+"WW") if re.match("\d+-\d+-plate_\d+.csv$", entry)]
ws_csv_list = [entry for entry in os.listdir(rootbot_path+"/"+"WS") if re.match("\d+-\d+-plate_\d+.csv$", entry)]

active_csv_df = pd.DataFrame(active_csv_list, columns= ['file'])
ww_csv_df =     pd.DataFrame(ww_csv_list, columns= ['file'])
ws_csv_df =     pd.DataFrame(ws_csv_list, columns= ['file'])
active_csv_df['dir'] = 'active'
ww_csv_df['dir'] = 'ww'
ws_csv_df['dir'] = 'ws'

file_state = pd.concat([active_csv_df, ww_csv_df, ws_csv_df], axis = 0)

# These are all the files in the remote drive.
# file_state


### Of cache ###################################################################
cached_active_csv_list = [entry for entry in os.listdir(data_cache_path+"/"+"Already Scored/") if re.match("\d+-\d+-plate_\d+.csv$", entry)]
cached_ww_csv_list = [entry for entry in os.listdir(data_cache_path+"/"+"WW") if re.match("\d+-\d+-plate_\d+.csv$", entry)]
cached_ws_csv_list = [entry for entry in os.listdir(data_cache_path+"/"+"WS") if re.match("\d+-\d+-plate_\d+.csv$", entry)]

cached_active_csv_df = pd.DataFrame(cached_active_csv_list, columns= ['file'])
cached_ww_csv_df =     pd.DataFrame(cached_ww_csv_list, columns= ['file'])
cached_ws_csv_df =     pd.DataFrame(cached_ws_csv_list, columns= ['file'])
cached_active_csv_df['dir'] = 'active'
cached_ww_csv_df['dir'] = 'ww'
cached_ws_csv_df['dir'] = 'ws'

cached_file_state = pd.concat([cached_active_csv_df, cached_ww_csv_df, cached_ws_csv_df], axis = 0)
cached_file_state['status'] = 'cached'


## Contrast ====================================================================
# Compare the two dfs and flag all those without the cached status for download
contrast_file_state = cached_file_state.merge(file_state, how = 'outer')
contrast_file_state['download'] = [True if e != 'cached' else False for e in contrast_file_state['status'] ]
contrast_file_state = contrast_file_state.loc[contrast_file_state.download, ]



# Migrate files ----------------------------------------------------------------
## Transfer those that have not yet been moved. ================================
transfer_log = pd.DataFrame()
for i in contrast_file_state.index:
    assert contrast_file_state.loc[i, 'dir'] in ['active', 'ws', 'ww'
                                                ], "`dir` is not an allowed value. Should be 'active', 'ws', 'ww'"
    # Move file
    if contrast_file_state.loc[i, 'dir'] == 'active':
        shutil.copy(rootbot_path+"/"+"Already Scored/"+contrast_file_state.loc[i, 'file'],
                    data_cache_path+"/"+"Already Scored/")

    elif contrast_file_state.loc[i, 'dir'] == 'ws':
        shutil.copy(rootbot_path+"/"+"WS/"+contrast_file_state.loc[i, 'file'],
                    data_cache_path+"/"+"WS/")

    elif contrast_file_state.loc[i, 'dir'] == 'ww':
        shutil.copy(rootbot_path+"/"+"WW/"+contrast_file_state.loc[i, 'file'],
                    data_cache_path+"/"+"WW/")

    else:
        print("Issue with directory state") # this should never come up. Checking is done with the above assert statement.

    # add to change log
    temp = pd.DataFrame(contrast_file_state.loc[contrast_file_state.index ==i, ['file', 'dir']])
    temp['CopiedAt'] = str(datetime.datetime.now())
    if transfer_log.shape[0] == 0:
        transfer_log = temp
    else:
        transfer_log = pd.concat([transfer_log, temp], axis = 0)

## check if we need to write out anything ======================================
# default to not _run_ anything.
run_models = pd.DataFrame.from_dict({'run_models':['FALSE']})    # this is a str not a bool because R uses all caps.
if transfer_log.shape[0] > 0:
    #if there were additions we should rerun models.
    run_models = pd.DataFrame.from_dict({'run_models':['TRUE']}) # this is a str not a bool because R uses all caps.

    # If the file doesn't exist we'll include the header. Otherwise We'll just extend the file.
    transfer_log = transfer_log.rename(columns = {'file':'File', 'dir':'CopiedFrom'})
    include_header = not os.path.exists(transfer_log_path)
    transfer_log.to_csv(transfer_log_path, mode='a', header=include_header )
run_models.to_csv(run_models_path)


# Create a single csv for all the data -----------------------------------------
# # Inactive directories (WW, WS) -----------------------------------------------

# Get data in inactive folders
def _get_data_inactive_folders(data_cache_path = data_cache_path,
                               folder = "WS"):
    def _get_csv(data_cache_path,
                 folder,
                 csv_file):
        temp_path = data_cache_path+"/"+folder+"/"+csv_file
        temp = pd.read_csv(temp_path)
        # add path & group
        temp.loc[:, "path"] = temp_path
        temp.loc[:, "group"] = folder.lower()
        return(temp)

    csv_list = [entry for entry in os.listdir(data_cache_path+"/"+folder) if re.match("\d+-\d+-plate_\d+.csv$", entry)]
    df_list = [_get_csv(data_cache_path = data_cache_path,
                        folder = folder,
                        csv_file = entry) for entry in csv_list]

    # rbind and return
    folder_df = pd.concat(df_list, axis=0)
    return(folder_df)

ww = _get_data_inactive_folders(data_cache_path = data_cache_path, folder = "WW")
ws = _get_data_inactive_folders(data_cache_path = data_cache_path, folder = "WS")

inactive_res = pd.concat([ww, ws], axis = 0)

# there are spaces before some of the column names.


# reduce data size
# length is the only measure we care about.
old_names = list(inactive_res)
new_names = [name.strip() for name in old_names]

convert_names = {}
for i in range(len(old_names)):
    convert_names.update({old_names[i]:new_names[i]})

inactive_res = inactive_res.rename(columns = convert_names)
inactive_res = inactive_res.loc[:, ["length",  "group", "root_name",  "image",  "root",  "path"] ]


# Group check based on plate name.
# TODO do Mia's plate convetions hold for historical data?
temp = pd.DataFrame(inactive_res.loc[:, "image"]).drop_duplicates()
temp["plate"] = [entry.split("_")[1] for entry in list(temp.image)]

temp.loc[temp.plate == "noQR", "plate"] = np.nan
# float to include nan
temp["plate"] = [float(entry) for entry in list(temp.plate)]

# temp.plate.drop_duplicates()

# Mia's script "OrganizePhotos.py" states:
#plates 25, 26, 27, and 33 are always WS for every experiment
#plates 22, 23, and 24 are always WW for every experiment
temp["group_check"] = ""
temp.loc[temp.plate.isin([float(i) for i in [25, 26, 27, 33]]), 'group_check'] = "ws"
temp.loc[temp.plate.isin([float(i) for i in [22, 23, 24]]), 'group_check'] = "ww"

inactive_res = inactive_res.merge(temp, how = 'outer')

# temp = pd.DataFrame(inactive_res.loc[:, "root_name"]).drop_duplicates()

# inactive_res



# # Active Directories (`Already\ Scored/`) -------------------------------------

def _get_data_active_folder(data_cache_path = data_cache_path,
                               folder = "WS"):
    # modified to apply Mia's plate grouping convention
    def _get_csv2(data_cache_path,
                 folder,
                 csv_file):
        temp_path = data_cache_path+"/"+folder+"/"+csv_file
        temp = pd.read_csv(temp_path)
        # add path & treatment group
        temp.loc[:, "path"] = temp_path

        plate_num = csv_file.split(sep = "_")[-1].strip(".csv")
        plate_num = int(plate_num)
        if plate_num in [25, 26, 27, 33]:
            temp.loc[:, "group"] = "ws"
        elif plate_num in [22, 23, 24]:
            temp.loc[:, "group"] = "ww"

        return(temp)

    csv_list = [entry for entry in os.listdir(data_cache_path+"/"+folder) if re.match("\d+-\d+-plate_\d+.csv$", entry)]
    df_list = [_get_csv2(data_cache_path = data_cache_path,
                        folder = folder,
                        csv_file = entry) for entry in csv_list]

    # rbind and return
    folder_df = pd.concat(df_list, axis=0)
    return(folder_df)



active_res = _get_data_active_folder(data_cache_path = data_cache_path, folder = "Already Scored")

# Names contain whitespace that need be removed
old_names = list(active_res)
new_names = [name.strip() for name in old_names]

convert_names = {}
for i in range(len(old_names)):
    convert_names.update({old_names[i]:new_names[i]})

active_res = active_res.rename(columns = convert_names)
active_res = active_res.loc[:, ["length",  "group", "root_name",  "image",  "root",  "path"] ]

# active_res




# Merge, make minor changes and write out with timestamp
all_res = active_res.merge(inactive_res, how = "outer")
# Parse root_name into genotype/replicate
temp = pd.DataFrame(all_res.loc[:, "root_name"].drop_duplicates())
temp[['genotype','replicate']] = temp.root_name.str.split("seed",expand=True)
temp['replicate'] = temp.replicate.str.strip().str.strip("#")
all_res = all_res.merge(temp)


filename = str(datetime.datetime.now())
filename = 'rootbot_'+'_'.join(filename.split(' '))+'.csv'

all_res.to_csv(data_cache_path+'/Records/'+filename)

