import pandas as pd
from services.postgremanager.utils import engine
from env import url


orders = pd.read_csv(url)

orders.columns = orders.columns.str.lower().str.replace(" ", "_")

def sql_load():
    orders.to_sql("orders", engine, if_exists="replace", index=False)
    print("Orders Loaded\n")