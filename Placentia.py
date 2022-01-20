import streamlit as st
import pandas as pd
import numpy as np
from zipfile import ZipFile
# import wget
import glob

@st.cache(suppress_st_warning=True)
def prepareData():
    # if not (glob.glob("98-401-X2016061_English_CSV_data.csv")):
        # download the openData
        # url = "https://www12.statcan.gc.ca/census-recensement/2016/dp-pd/prof/details/download-telecharger/comp/GetFile.cfm?Lang=E&FILETYPE=CSV&GEONO=061"
        # wget.download(url, '98-401-X2016061_eng_CSV.zip')
        # unzip the zip file
        # with ZipFile('98-401-X2016061_eng_CSV.zip', 'r') as zipObj:
        #     zipObj.extractall() 

    rawData = pd.read_csv("98-401-X2016061_English_CSV_data.csv")
    rawData = rawData[~rawData["GEO_NAME"].str.contains("Division")]



    # selecting required fileds(which are in rows)
    memberIDs = [
        1,    # Population, 2016
        22,   # 55 to 59 years
        23,   # 60 to 64 years	
        24,   # 65 years and over
        58,   # Average household size
        73,   # Average size of census families
        674,  # Average total income in 2015 among recipients
        680,  # Average government transfers in 2015 among recipients ($)    
        690,  # Government transfers (%)
        ]
    data = rawData[rawData["Member ID: Profile of Census Subdivisions (2247)"].isin(memberIDs)]
    data = data.pivot(index="GEO_NAME", columns="DIM: Profile of Census Subdivisions (2247)", values="Dim: Sex (3): Member ID: [1]: Total - Sex").reset_index()
    data = data.rename_axis(None, axis=1).reset_index(drop=True)

    for col in data.columns[1:]:
        data[col] = pd.to_numeric(data[f"{col}"], errors='coerce')

    data["over_55"] = data["55 to 59 years"] + data["60 to 64 years"] + data["65 years and over"]
    data = data.drop(["55 to 59 years","60 to 64 years","65 years and over"], axis=1)
    # We eliminated 87 communities that their population was less than 300 and ended up to 193
    data = data.dropna().reset_index().drop("index", axis=1)
    data["percentage_over55"] = data["over_55"]/data["Population, 2016"]
    return data

data =prepareData()

placentia_PercOver55 = float(data[data.GEO_NAME == "Placentia"]["percentage_over55"])
placentia_population = float(data[data.GEO_NAME == "Placentia"]["Population, 2016"])
placentia_avgIncome = float(data[data.GEO_NAME == "Placentia"]["Average total income in 2015 among recipients ($)"])
placentia_household = float(data[data.GEO_NAME == "Placentia"]["Average household size"])

std_age = 0.05
std_population = 0.1
std_income = 0.1
std_household = 0.05

temp = data.copy()

temp = temp[((placentia_PercOver55-std_age) <= temp["percentage_over55"]) & 
    (temp["percentage_over55"] <= (placentia_PercOver55+std_age))]

temp = temp[((placentia_population-placentia_population*std_population) <= temp["Population, 2016"]) & 
    (temp["Population, 2016"] <= (placentia_population+placentia_population*std_population))]

temp = temp[((placentia_avgIncome-placentia_avgIncome*std_income) <= temp["Average total income in 2015 among recipients ($)"]) & 
    (temp["Average total income in 2015 among recipients ($)"] <= (placentia_avgIncome+placentia_avgIncome*std_income))]

temp = temp[((placentia_household-placentia_household*std_household) <= temp["Average household size"]) & 
    (temp["Average household size"] <= (placentia_household+placentia_household*std_household))]

temp = temp[["GEO_NAME", "Population, 2016", "percentage_over55", "Average total income in 2015 among recipients ($)", "Average household size"]]
temp = temp.rename(columns={"GEO_NAME":"Community", "Population, 2016":"Population", "Average total income in 2015 among recipients ($)": "Avg income 2015"})
_ = temp.reset_index(drop=True)



std_age = 5
std_population = 10
std_income = 10
std_household = 5
step = 5
min = 0
max = 100
st.sidebar.title("Please select the desired deviation from Placentia")
age_STD = st.sidebar.slider("% age_STD", min_value=min, max_value=max, step=step, value=std_age)
population_STD = st.sidebar.slider("% population_STD", min_value=min, max_value=max, step=step, value=std_population)
income_STD = st.sidebar.slider("% income_STD", min_value=min, max_value=max ,step=step, value=std_income)
household_STD = st.sidebar.slider("% household_STD", min_value=min, max_value=max, step=step, value=std_household)
sort_dict = {"Community":"Community", 
             "Population":"Population",
             "Percentage_over55":"percentage_over55", 
             "Avg income 2015":"Avg income 2015",
             "Average household size":"Average household size"}

sort = st.sidebar.selectbox("sort on:", ["Community","Population","percentage_over55","Avg income 2015","Average household size"], 0)

def community(age_STD,population_STD,income_STD,household_STD, sort ):

    temp = data.copy()

    temp = temp[((placentia_PercOver55-age_STD/100) <= temp["percentage_over55"]) & 
        (temp["percentage_over55"] <= (placentia_PercOver55+age_STD/100))]

    temp = temp[((placentia_population-placentia_population*population_STD/100) <= temp["Population, 2016"]) & 
        (temp["Population, 2016"] <= (placentia_population+placentia_population*population_STD/100))]

    temp = temp[((placentia_avgIncome-placentia_avgIncome*income_STD/100) <= temp["Average total income in 2015 among recipients ($)"]) & 
        (temp["Average total income in 2015 among recipients ($)"] <= (placentia_avgIncome+placentia_avgIncome*income_STD/100))]

    temp = temp[((placentia_household-placentia_household*household_STD/100) <= temp["Average household size"]) & 
        (temp["Average household size"] <= (placentia_household+placentia_household*household_STD/100))]

    temp = temp[["GEO_NAME", "Population, 2016", "percentage_over55", "Average total income in 2015 among recipients ($)", "Average household size"]]
    temp = temp.rename(columns={"GEO_NAME":"Community", "Population, 2016":"Population", "Average total income in 2015 among recipients ($)": "Avg income 2015"})
    temp = temp.reset_index(drop=True).sort_values(sort, ascending=True)
    st.table(temp)

st.header('"Placentia-like" Communities')
community(age_STD,population_STD,income_STD,household_STD, sort)



