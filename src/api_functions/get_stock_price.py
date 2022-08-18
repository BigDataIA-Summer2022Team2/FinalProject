import pandas as pd
import numpy as np
import yaml, os
from sqlalchemy import create_engine
from datetime import datetime,timedelta
import pandas_datareader as pdr
# Scale the data
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
import pymysql
from keras.models import Sequential
from keras.layers import Dense, LSTM

#################################################################
# @Description: API Functions
# @Author: Meihu Qin
# @UpdateDate: 2022/8/17

#Connect to MySQL DB
abs_path = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))

yaml_path = abs_path + "/mysql.yaml"

with open(yaml_path, 'r') as file:
        config = yaml.safe_load(file)

db_host = config['credentials']['host']
db_user = config['credentials']['user']
db_password = config['credentials']['password']
db_database = config['credentials']['database']
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=db_host, db=db_database, user=db_user, pw=db_password))
dbConnection = engine.connect()

"""
    This function needs you to choose a company stock name and the start/end date of the data you want to look up. It returns the historical stock price data for that 
    time period.
    """
def SaveStockPrice(compamyabbreviation):
                
        #datetime.datetime is a data type within the datetime module
        end = datetime.now()
        start = datetime(end.year - 10, end.month, end.day)
        #DataReader method name is case sensitive
        
        df = pdr.DataReader(compamyabbreviation, 'yahoo', start, end)
        df = df.reset_index()
        df = df.round(2)
        # Create SQLAlchemy engine to connect to MySQL Database
        engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
                                        .format(host=db_host, db=db_database, user=db_user, pw=db_password))
        # Insert data in to MySQL using SQLAlchemy engine
        # engine.execute("INSERT INTO  `database_name`.`student` (`name` ,`class` ,`mark` ,`sex`) \VALUES ('King1',  'Five',  '45',  'male')")
        # Convert dataframe to sql table                                   
        df.to_sql(f'{compamyabbreviation.upper()}', engine, if_exists='replace', index=False)
        engine.dispose()

        res = compamyabbreviation.upper() + " Table created! Saving success!"
        
        return {"details":res}
"""
    This function needs you to choose a company stock name and the start/end date of the data you want to look up. It returns the historical stock price data for that 
    time period.
    """
def getStockPrice(compamyabbreviation, start_date, end_date):

        start_date = str(start_date)
        end_date = str(end_date)
        df = pd.read_sql(f"select * from {compamyabbreviation}_stock WHERE Date BETWEEN '{start_date}' AND '{end_date}'", dbConnection)
        data = df.to_dict()
        return data

"""
    This function takes a company stock name as an input, and it returns the data from the past 7 days.
    """
def getRecent7StockPrice(compamyabbreviation):
        end = datetime.now()
        if end.day -7 >= 1:
                start = datetime(end.year, end.month, end.day - 7)
        else:
                if end.month == 1:
                        start = datetime(end.year-1, 12, 24+end.day)
                if end.month in [3,5,7,8,10,12]:
                        start = datetime(end.year, end.month-1, 25+end.day)
                if end.month in [2,4,6,9,11]:
                        start = datetime(end.year, end.month-1, 24+end.day)
        df = pd.read_sql(f"select * from {compamyabbreviation}_stock WHERE Date BETWEEN '{start}' AND '{end}'", dbConnection)
        data = df.to_dict()
        return data

"""
    This function takes a company stock name as an input, and it returns the data from the past 30 days.
    """
def getRecent30StockPrice(compamyabbreviation):
        end = datetime.now()
        if end.month > 1:
                start = datetime(end.year, end.month-1, end.day)
        else:
                start = datetime(end.year-1, 12, end.day)
        df = pd.read_sql(f"select * from {compamyabbreviation}_stock WHERE Date BETWEEN '{start}' AND '{end}'", dbConnection)
        data = df.to_dict()
        return data


"""
    This function takes a company stock name as an input, and it returns the data from the past year.
    """
def getRecent1YStockPrice(compamyabbreviation):
        end = datetime.now()

        start = datetime(end.year-1, end.month, end.day)
        
        df = pd.read_sql(f"select * from {compamyabbreviation}_stock WHERE Date BETWEEN '{start}' AND '{end}'", dbConnection)
        data = df.to_dict()
        return data

"""
    This function takes a company stock name as an input and return its predicted stock price
    """
def PredictStockPrice(compamyabbreviation):
        
        model = load_model(f"{compamyabbreviation}_model.h5")

        df = pd.read_sql(f"select Close from {compamyabbreviation}_stock ", dbConnection)

        dataset = df.values
        scaler = MinMaxScaler(feature_range=(0,1))
        scaled_data = scaler.fit_transform(dataset)
        test_data = scaled_data[2446: , :]
        # Create the data sets x_test and y_test
        x_test = []
        
        for i in range(60, len(test_data)):
                x_test.append(test_data[i-60:i, 0])
        
        # Convert the data to a numpy array
        x_test = np.array(x_test)

        print(len(x_test))
        # Reshape the data
        x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1 ))

        #Get the models predicted price values 
        predictions = model.predict(x_test)
        predictions = scaler.inverse_transform(predictions)
        predictions = predictions.reshape(10).tolist()
        print(predictions)
        result = {}
        for i in range(1,11):
                result[i] = predictions[i-1]
        
        return result


# @author Cheng Wang
# @date   8/17/2022
def userFollowCompanyStatusCheck(username,co_abbr):
        """
                Check if the user whether could follow the given Company stock
                @params:
                        1. username -> user who sign in to FastAPI (we will check it from local MySQL database)
                        2. co_abbr -> company abbrivation name
                @return:
                        1. already followed
                        2. we will create one row of data into stock_follow_table
                                2.1 download target company abbrivation name stock history(max 10 years)
                        3. something wrong (we need check...)
        """
        con = pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_database, charset="utf8")
        c = con.cursor()
        sql = "select userId from user_table WHERE username = '"
        c.execute(sql + username + "';")
        userId = c.fetchall()[0][0]
        #print(result)
        
        checkUserFollowStatus = "select count(1) from stock_follow_table where userId = '" + str(userId) + "' and stockAbbrName = '" + str(co_abbr.upper()) + "';"
        c.execute(checkUserFollowStatus)
        result = c.fetchall()[0][0]
        res_dict = {}
        if(result == 1):
                res_dict[username] = "You already followed!"
                checkTableSQL = "show tables like '"+ co_abbr.upper() +"';"
                #c.execute(checkTableSQL)
                #test = c.fetchall()[0][0]
                #print("========================================\n",test)
                
                
        elif(result == 0):
                #res_dict[username] = "You need follow it! Check DB if exists!"
                nowTime = datetime.now()
                c.execute('INSERT INTO stock_follow_table(userId,createDate,updateDate,disabled,stockAbbrName) VALUES(%s,%s,%s,%s,%s)',(userId,nowTime,nowTime,0,co_abbr.upper()))
                con.commit()
                # c.execute(checkUserFollowStatus)
                # status = c.fetchall()[0][0]
                # To download target Company Max (10 years) history 
                
                checkTableSQL = "show tables like '"+ co_abbr.upper() +"';"
                c.execute(checkTableSQL)
                getResultFromSQL = c.fetchall()
                if getResultFromSQL == ():
                        SaveStockPrice(co_abbr)
                        res_dict[username] = co_abbr.upper() + " Table created! Saving success!"
                else:
                        table_name = getResultFromSQL[0][0]
                        
                        if(table_name.upper() != co_abbr.upper()):
                                SaveStockPrice(co_abbr)
                                res_dict[username] = co_abbr.upper() + " Table created! Saving success!"
                        else:
                                res_dict[username] = "Someone already followed this company!"
                      
        else:
                res_dict[username] = "Something went wrong!" 
        return res_dict

      
      
      
  
def saveStockPriceandTrainModel():

        #datetime.datetime is a data type within the datetime module
        yesterday = datetime.today()+timedelta(-1)
        yesterday_format = yesterday.strftime('%Y-%m-%d')

        #DataReader method name is case sensitive
        stockname = pd.read_sql(f"select distinct stockAbbrName from stock_follow_table", dbConnection)
        compamyabbreviation = stockname['stockAbbrName'].values.tolist()
        for name in compamyabbreviation:
                #Get yesterday stock data
                yesterdaydata = pdr.DataReader(name, 'yahoo', f"'{yesterday_format}'", f"'{yesterday_format}'")
                yesterdaydata = yesterdaydata.reset_index()
                yesterdaydata = yesterdaydata.round(2)
                
                engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
                                                .format(host=db_host, db=db_database, user=db_user, pw=db_password))
                #Save one row data into stock table                                     
                yesterdaydata.to_sql(f'{name}', engine, if_exists='append', index=False)
                engine.dispose()

                df = pd.read_sql(f"select * from {name}", dbConnection)
                # Create a new dataframe with only the 'Close column 
                data = df.filter(['Close'])

                # Convert the dataframe to a numpy array
                dataset = data.values

                # Get the number of rows to train the model on
                training_data_len = len(dataset)

                # Scale the data
                scaler = MinMaxScaler(feature_range=(0,1))
                scaled_data = scaler.fit_transform(dataset)

                # Create the training data set 
                # Create the scaled training data set
                train_data = scaled_data[0:int(training_data_len), :]

                # Split the data into x_train and y_train data sets
                x_train = []
                y_train = []

                for i in range(60, len(train_data)):
                        x_train.append(train_data[i-60:i, 0])
                        y_train.append(train_data[i, 0])
                        if i<= 61:
                                print(x_train)
                                print(y_train)
                                print()
                        
                # Convert the x_train and y_train to numpy arrays 
                x_train, y_train = np.array(x_train), np.array(y_train)

                # Reshape the data
                x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))


                # Build the LSTM model
                model = Sequential()
                model.add(LSTM(128, return_sequences=True, input_shape= (x_train.shape[1], 1)))
                model.add(LSTM(64, return_sequences=False))
                model.add(Dense(25))
                model.add(Dense(1))

                # Compile the model
                model.compile(optimizer='adam', loss='mean_squared_error')

                # Train the model
                model.fit(x_train, y_train, batch_size=1, epochs=1)
                model_path = abs_path + f"/models/{name}.h5"
                model.save(model_path)
        
        result = {}
        for i in range(compamyabbreviation):
                result[str[i+1]] = compamyabbreviation[i]
        result["updated date"] = datetime.date.today()
        
        return result
                   