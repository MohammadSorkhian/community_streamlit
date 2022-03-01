import streamlit as st
import pandas as pd
import numpy as np
from zipfile import ZipFile
from st_aggrid import AgGrid
from st_aggrid.shared import GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
# import wget
import glob

st.set_page_config(page_title="Communities", layout="wide") 

# removing menue bar and footer
hide_footer = '''
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility:hidden;}
    </style>
'''
st.markdown(hide_footer, unsafe_allow_html=True)

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
    15,   # 20 to 24 years
    16,   # 25 to 29 years
    17,   # 30 to 34 years
    18,   # 35 to 39 years
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

    communitiesDistancesData = pd.read_csv("communitiesDistances.csv", index_col=0)
    data = data.merge(communitiesDistancesData, left_on="GEO_NAME", right_index=True)

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


####################
##### side bar #####

if ("showHelp" not in st.session_state.keys()): 
    st.session_state.showHelp = "False"

def onShowHelpClickHandler():
    if st.session_state.showHelp == "True" : 
        st.session_state.showHelp = "False"
    else: 
        st.session_state.showHelp = "True"
 
if st.sidebar.button("Help"):
    onShowHelpClickHandler()

if st.session_state.showHelp == "True":
    st.sidebar.markdown('''
    This project aims to find communities that have the most similarity to Placentia.
    - We have four criteria: age (over 55), population, income, and household size. The following sliders give you the ability to set desired tolerance from Placentia.
    - By adjusting the Radius slide and selecting a community, we can see more details about other communities within the Radius range of the selected one. This helps to figure out how many potential employees we have within the Radius range of the chosen community.
    ''')


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

st.sidebar.text("")
st.sidebar.text("")
st.sidebar.text("")

radious = st.sidebar.slider("Radious_Km", min_value=1, max_value=50, step=1, key="radious", value=5)

sort = st.sidebar.selectbox("sort by:", ["Community","Population","percentage_over55","Avg income 2015","Average household size"], 0)



#####################
##### main page #####
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
    temp["percentage_over55"] = (temp["percentage_over55"]*100).round(1)
    

    gb = GridOptionsBuilder.from_dataframe(temp)
    gb.configure_selection(selection_mode="single", use_checkbox=True)
    # gb.configure_pagination()
    # gb.configure_side_bar()
    # gb.configure_default_column(
    #     groupable=False, 
    #     value=False, 
    #     enableRowGroup=False, 
    #     aggFunc="sum", 
    #     editable=False)
    gridOptions = gb.build()


    PlacentiaLIke_table = st.columns((20,1,10))
    with PlacentiaLIke_table[0]:
        selected = AgGrid(temp,
            gridOptions=gridOptions,
            enable_enterprise_modules=False,
            allow_unsafe_jscode=True,
            update_mode=GridUpdateMode.SELECTION_CHANGED)['selected_rows']#[0]["Community"]


    if (len(selected)>0):

        community_name = selected[0]["Community"]

        communitiesWithenRadious = data[(data[community_name] <= radious)][["GEO_NAME", "20 to 24 years", "25 to 29 years", "30 to 34 years", "35 to 39 years", community_name]]\
        .rename(columns={"GEO_NAME":"Community", community_name:"Direct Distance(km)"})\

        communitiesWithenRadious["Direct Distance(km)"] = round(communitiesWithenRadious["Direct Distance(km)"])
        communitiesWithenRadious["20 to 30 years"] = communitiesWithenRadious["20 to 24 years"]+communitiesWithenRadious["25 to 29 years"]
        communitiesWithenRadious["30 to 40 years"] = communitiesWithenRadious["30 to 34 years"]+communitiesWithenRadious["35 to 39 years"]
        communitiesWithenRadious.drop(["20 to 24 years","25 to 29 years","30 to 34 years","35 to 39 years"],axis=1, inplace=True)
        communitiesWithenRadious = communitiesWithenRadious[["Community", "20 to 30 years", "30 to 40 years", "Direct Distance(km)"]]
        communitiesWithenRadious.loc[1000] = communitiesWithenRadious.sum()
        communitiesWithenRadious.loc[1000,"Community"] = "Total"
        communitiesWithenRadious.loc[1000,"Direct Distance(km)"] = np.nan

        st.text("")
        st.write(f"Communities in the range of {st.session_state.radious} km from {community_name}")

        radious_table_detail = st.columns((20,1,10))
        with radious_table_detail[0]:
            AgGrid(communitiesWithenRadious)
        with radious_table_detail[2]:
            numberOver55 = int(selected[0]["Population"]*(selected[0]["percentage_over55"]/100))
            sum20_30 = int(communitiesWithenRadious.loc[1000,"20 to 30 years"])
            sum30_40 = int(communitiesWithenRadious.loc[1000,"30 to 40 years"])
            st.markdown(f'''<p>- In {community_name}, we have {numberOver55} elderlies fifty-five and over <br>
                - Within {radious} km from {community_name}, we have {sum20_30 +sum30_40} (20 to 40 year olds) potential caregivers. </p>''', unsafe_allow_html=True)


st.header('"Placentia-like" Communities')
community(age_STD,population_STD,income_STD,household_STD, sort)




