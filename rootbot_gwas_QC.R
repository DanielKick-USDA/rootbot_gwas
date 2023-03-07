#On This Episode of "Grace tries to do R", it's Data Quality Control!
read.csv("data.csv")
#read in csv with phenotypic data
df = read.csv("data.csv")

#break off df into useful chunks, kept inbred name, cassette number, condition, image, which is plate name and time, and root lengths
df = subset(df, select = c("inbred","cassette","condition","image","length"))

#aggregate function taking standard deviations of root lengths by image/plate, ten lengths for each image/plate, into data_sd df
data_sd <- aggregate(df$length, list(df$image), FUN=sd)

#changing the column names to plate and sd_length
colnames(data_sd) <- c("Plate", "SD_Length")

#plotting standard deviation with scatter plot and density graph
library(ggplot2)
ggplot(data = data_sd, mapping = aes(x = SD_Length)) +
  geom_density(fill = "dark green", color = "dark green")

#scatter plot with separation between standard deviation greater and lesser than 2
ggplot(data = data_sd, mapping = aes(x = Plate, y = SD_Length))+
  geom_point(aes(color = SD_Length > 2))

#sorting out plates with SD_Length > 2
df_High_SD = data_sd[data_sd$SD_Length > 2,]

#sorting High SD plates into data frames based on year for plotting
df_2018Plates_High_SD = subset(df, image %in% c('20181019-103959-plate_002','20181101-200557-plate_008','20181117-140559-plate_002', '20181130-160559-plate_002', '20181130-163657-plate_007', '20181221-050556-plate_008'))

ggplot(data = df_2018Plates_High_SD, mapping = aes(x = image, y = length)) +
  geom_point() +
  theme(axis.text.x = element_text(angle = -60)) +
  coord_cartesian(ylim = c(-1, 18))

df_2019_20_21_Plates_High_SD = subset(df, image %in% c('20190427-095354-plate_002', '20190428-012600-plate_006', '20190428-140558-plate_002', '20190906-173700-plate_031', '20200216-084834-plate_022', '20211016-034102-plate_023'))

ggplot(data = df_2019_20_21_Plates_High_SD, mapping = aes(x = image, y = length)) +
  geom_point() +
  theme(axis.text.x = element_text(angle = -60))+
  coord_cartesian(ylim = c(-1, 18))

df_2022pt1_Plates_High_SD = subset(df, image %in% c('20220226-000301-plate_020', '20220312-010301-plate_020', '20220319-022909-plate_036', '20220326-011000-plate_046', '20220416-025104-plate_046', '20220416-025405-plate_040'))

ggplot(data = df_2022pt1_Plates_High_SD, mapping = aes(x = image, y = length)) +
  geom_point() +
  theme(axis.text.x = element_text(angle = -60))
  #coord_cartesian(ylim = c(-1, 30))

df_2022pt2_Plates_High_SD = subset(df, image %in% c('20220430-022200-plate_044', '20220430-023703-plate_040', '20220616-223108-plate_050', '20220616-225203-plate_042', '20220624-234003-plate_042'))
#hjust = -1
ggplot(data = df_2022pt2_Plates_High_SD, mapping = aes(x = image, y = length)) +
  geom_point() +
  theme(axis.text.x = element_text(angle = -60))

#creating table with existing High_SD data frame and information about seeds to be removed
#first row - 2018, second row - 2019-2021, third row - 2022 pt1, fourth row 2022 pt2

seeds_for_removal = c('1-10', '1-10', '8', '7, 3, 10', '1, 3', '9',
                                   'B73-10', 'B73, 1, 3', 'B73-10', 'B73', 'B73, 4, 8', '1',
                                   'B73', 'N/A', 'N/A', '4', '7', 'N/A',
                                   'N/A', 'N/A', '3, 8', '2, 7', 'N/A') 
notes_on_removal = c('incorrect measurement', 'incorrect measurement', 'misrep. of growth', 'misrep. of growth', 'misrep. of growth', 'misrep. of growth',
                                  'incorrect measurement', 'misrep. of growth', 'incorrect measurement', 'misrep. of growth', 'misrep. of growth', 'misrep. of growth',
                                  'other seeds correct', 'missing seed 4', 'missing seed 8', 'misrep. of growth', 'misrep. of growth', 'all seeds look correct',
                                  'missing 3 seeds', 'missing seed 10', 'misrep. of growth', 'misrep. of growth', 'all seeds look correct' )
re_scored = c('Y','Y', 'N', 'N', 'N', 'N',
              'Y', 'N', 'Y', 'N', 'N', 'N',
              'N', 'Y', 'Y', 'N', 'N', 'N',
              'Y', 'Y', 'N', 'N', 'N' )
df_Removed_Seeds <- cbind(df_High_SD, seeds_for_removal, notes_on_removal, re_scored)


# How to find the measurements that need to be replaced ------------------------

# Go through each plate in df_Removed_Seeds and follow below rules

Replace_Plates <- df_Removed_Seeds$Plate

# for(Plate in Replace_Plates){
#   print(Plate)
#   
# }

# How to replace measurements --------------------------------------------------

# when you need to replace a plate
  # go to the "Re-Scoring for QC" folder
    # Find csv with matching plate name (at start)
  # Get rid of the plate's data
  # read in the replacement data
  # subset the replacement to matching columns
  # add it into data

# when you need to replace an observation but not a whole plate
  # Does the rescored data exist?
    # if yes --
      # find the observations to replace
      # get the replacement data as above AND subset to the obs. to be used
      # drop old data add new data
    # if no --
      # drop with no replacements (use NA)

# when no seeds need to be replaced
  # don't do anything


df_backup <- df


df <- df_backup

for(Plate in Replace_Plates){
  plate_mask <- df_Removed_Seeds$Plate == Plate
  Plate_notes <- df_Removed_Seeds[plate_mask, c('notes_on_removal')]

  # No action needed -----------------------------------------------------------
  if (Plate_notes == "all seeds look correct") {
    # Do Nothing. 
    
  # Replace the full plate -----------------------------------------------------
  } else if (Plate_notes == "incorrect measurement") {
    
    if (df_Removed_Seeds[plate_mask, c('re_scored')] != "Y"){
      print("Warning! Expected `re_scored` == T")
      print(Plate)
      
    } else {
      # load replacment csv and replace
      search_res <- list.files('./Re-Scoring for QC/')
      
      if (TRUE %in% str_detect(string = search_res, 
                     pattern = paste(Plate, "\\D+\\.csv", sep = '') )){ 
        
        print('Plate found!')
        res <- search_res[
          str_detect(string = search_res, 
                     pattern = paste(Plate, "\\D+\\.csv", sep = '') )]
        
        replacement_data <- read.csv(paste('./Re-Scoring for QC/', res, sep = ''))
        replacement_data <- replacement_data[, c('length')]
        
        df[((df$image == Plate) & !is.na(df$image)), 'length'] <- NA
        
        if (length(df[((df$image == Plate) & !is.na(df$image)), 'length']) == length(replacement_data)){
          df[((df$image == Plate) & !is.na(df$image)), 'length'] <- replacement_data
          
        } else {
          
          #TODO This is being activated and we don't expect it to be. 
          # 1. Find what plates are activating this
          # 2. if they should be activating this -- then replace HOW we replace lengths
          # 3. if they shouldn't be activating this -- then find a way to make sure they don't (and replace the data anyway)
          print("Warning! Replacment length is not the same as the number of observations in the data.")
        }
        print(paste(Plate, 'was replaced!'))
        
        
      } else {
        print("Warning! Plate missing!")
        print(Plate)
      }      
    }
  } 
  #    
  # Possibly replacing a subset of seeds ---------------------------------------
  # !(Plate_notes %in% c("all seeds look correct", "incorrect measurement"))
}

Plate = "20181019-103959-plate_002" # should exist
Plate = "20181101-200557-plate_008"


Plate = "20190428-140558-plate_002" # should not exist

df_Removed_Seeds[plate_mask, ]




# install.packages("stringr")
library(stringr)



# for(res in search_res){
#   if (str_detect(string = res, 
#              pattern = "20181019-103959-plate_002\\D+\\.csv")){
#     print(res)
#   }
# }




# Syntax Notes -----------------------------------------------------------------

# df_Removed_Seeds[1:3, c('notes_on_removal')]
# df_Removed_Seeds$Plate 
# a <- 1
# a =  1 # assignment
# a == 1 # equivalence
# a == 2
# df_Removed_Seeds$Plate == Plate


# 
# # option 1
# a = df_Removed_Seeds$notes_on_removal == c("incorrect measurement")
# b = df_Removed_Seeds$notes_on_removal == c("all seeds look correct")
# a | b
# a + b > 0
# 
# # option 2
# df_Removed_Seeds$notes_on_removal %in% c("incorrect measurement",
                                       # "all seeds look correct")

# mask <- df_Removed_Seeds$notes_on_removal %in% c("all seeds look correct", "incorrect measurement")
# # mask == FALSE
# df_Removed_Seeds[!mask, ]
























































