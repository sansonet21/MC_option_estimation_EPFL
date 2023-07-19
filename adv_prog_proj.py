import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import datetime
from datetime import timedelta
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
poly_reg = PolynomialFeatures(degree=5)
import requests
from xml.etree import ElementTree
import nasdaqdatalink as quandl
import datetime
from scipy import interpolate
# import BMmodule
import bs4 as bs


def get_tickers():
    #get the name of the stocks
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})

    names = []

    for i in table.findAll('tr')[1:]:
        current_name = i.findAll('td')[0].text
        names.append(current_name)

    #remove the trash taken in the importation
    names = [s.replace('\n', '') for s in names]
    #Remove GEHC, OGN, BRK.B, CEG and BF.B from the names list
    names.remove('GEHC')
    names.remove('OGN')
    names.remove('BRK.B')
    names.remove('CEG')
    names.remove('BF.B')
    names.sort()
    return names

def get_curve_data():
    url = "https://markets.newyorkfed.org/read?productCode=50&eventCodes=505&limit=25&startPosition=0&sort=postDt:-1&format=xml"
    response = requests.get(url)
    root = ElementTree.fromstring(response.content)

    data = []
    for content in root.findall('./rates/rate'):
        new_date = content.find('./effectiveDate').text
        rate = content.find('./percentRate').text
        data.append({
            'date': new_date,
            'percent_rate': rate,
        })
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%dT%H:%M:%S")
    return df

def get_forwards(T,N):
    daily_rate_data = get_curve_data()
    yield_data = quandl.get("USTREASURY/YIELD",authtoken="hz2Yz84fPmembB3-GN2T",start_date =(datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d') ,end_date=datetime.datetime.now().strftime("%Y-%m-%d")).reset_index()
    #find the most recent date which is common to both data sets
    greatest_common_date = max(set(daily_rate_data.date.values).intersection(set(yield_data.Date.values)))
    maturities = [1/252, 1/12, 2/12, 3/12, 6/12, 1, 2, 3, 5, 7, 10, 20, 30]
    #Get the yields for the greatest common date
    yields = yield_data[yield_data.Date == greatest_common_date].iloc[0,1:14].to_numpy()
    yields = np.insert(yields,0,float(daily_rate_data[daily_rate_data.date == greatest_common_date].iloc[0,1]))
    spline = interpolate.CubicSpline(maturities, yields)
    forward_rates = np.array([])
    before = 0
    now =0
    for i in range(1,int(T*N+1)):
        if i==1:
            forward = spline(i*T/(T*N))*i
            before = spline(i*T/(T*N))*i
        else:
            forward = spline(i*T/(T*N))*i - before
            before = spline(i*T/(T*N))*i
        forward_rates = np.append(forward_rates,forward)
    return forward_rates/100

#import the data for apple from yahoo finance
def inputs(ticker , n=2):
    start=datetime.date.today()-timedelta(days=365*n)
    end=datetime.date.today()
    #take the inputs from the user
    s_stock = yf.download(ticker,start,end)
    #log returns
    ret_stocks =np.log(s_stock[['Open', 'High', 'Low', 'Close', 'Adj Close']] / s_stock[['Open', 'High', 'Low', 'Close', 'Adj Close']].shift(1))
    ret_stocks.dropna()
    #average
    mu_m = np.mean(ret_stocks.Close)*252
    #variance
    sigma_m = np.std(ret_stocks.Close)*np.sqrt(252)
    #initial value
    s0 = s_stock.Close[-1]
    return s0, sigma_m , mu_m

#european option
def price(T,N,n,sigma,mu,S0,K,type,mode='python'):
    # T=year, N=days, n=number of simulations,sigma=volatility, mu=average return,
    #  r=risk free, S0=initial value, K=striking price, type=type of derivative
    dt=T/(N*T)
    t=np.arange(int(N*T))*T/(N*T)
    # if mode=='C++':
    #     S=BMmodule.BM(n, N, S0, int(T*N), sigma, mu, r)
    if mode=='python':
        S=np.zeros((n,int(N*T+1)))
        S[:,0]=S0
        Z=np.random.standard_normal((n,int(N*T))).cumsum(axis=1)
        S[:,1:]=S0*np.exp(mu*t-sigma**2*t/2+sigma*np.sqrt(dt)*Z)
    if type=='call':
        return np.exp(-np.sum(get_forwards(T,N))/(T*N))*np.mean(np.maximum(S[:,-1]-K,0))
    elif type=='put':
        return np.exp(-np.sum(get_forwards(T,N))/(T*N))*np.mean(np.maximum(K-S[:,-1],0))
    elif type=='asian_call':
        return np.exp(-np.sum(get_forwards(T,N))/(T*N))*np.mean(np.maximum(S.mean()-K,0))
    elif type=='asian_put':
        return np.exp(-np.sum(get_forwards(T,N))*(T*N))*np.mean(np.maximum(K-S.mean(),0))         

    #american option
def american_price(T,N,n,sigma,mu,S0,K,type,mode='python'):
    # T=year, N=days, n=number of simulations,sigma=volatility, mu=average return,
    # r=risk free, S0=initial value, K=striking price, type=type of derivative
    dt=T/(N*T)
    t=np.arange(int(N*T))*T/(N*T)
    # if mode=='C++':
    #     S=BMmodule.BM(n, N, S0, int(T*N), sigma, mu, get_forwards(T,N))
    if mode=='python':
        S=np.zeros((n,int(N*T+1)))
        S[:,0]=S0
        Z=np.random.standard_normal((n,int(N*T))).cumsum(axis=1)
        S[:,1:]=S0*np.exp(mu*t-sigma**2*t/2+sigma*np.sqrt(dt)*Z)
    discount=np.exp(-get_forwards(T,N)*dt)
    value=np.zeros((n,int(N*T+1)))
    if type=='call':
        value[:,-1]=np.maximum(0,S[:,-1]-K) 
    if type=='put':
        value[:,-1]=np.maximum(0,K-S[:,-1])
    for j in range(int(N*T-1),-1,-1):
        if type=='call':
            X_poly = poly_reg.fit_transform(S[:,j].reshape(-1, 1))
            pol_reg = LinearRegression()
            pol_reg.fit(X_poly,value[:,j+1])
            exercise_value=pol_reg.predict(X_poly)*discount[j]
            intrinsic_value=np.maximum(S[:,j]-K,0)
            value[:,j]=np.maximum(exercise_value,intrinsic_value)
        elif type=='put':
            X_poly = poly_reg.fit_transform(S[:,j].reshape(-1, 1))
            pol_reg = LinearRegression()
            pol_reg.fit(X_poly,value[:,j+1])
            exercise_value=pol_reg.predict(X_poly)*discount[j]
            intrinsic_value=np.maximum(K-S[:,j],0)
            value[:,j]=np.maximum(exercise_value,intrinsic_value)    
    return np.mean(value[:,0])

