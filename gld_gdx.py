# -*- coding: utf-8 -*-
"""GLD_GDX.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KrkeFEZjom0H7g4DTYWRgS6DdUa_D3LR
"""

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
from matplotlib import pyplot
import pandas as pd
import pandas_datareader as pdr
import tensorflow
import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.layers import LSTM, GRU, Conv1D, MaxPooling1D, Flatten
from keras.preprocessing import sequence
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error as mse
from keras.callbacks import EarlyStopping
from sklearn.metrics import r2_score
from keras.optimizers import SGD
from keras.optimizers import Adam
import time
from sklearn import neighbors
from sklearn.ensemble import RandomForestRegressor
from sklearn.utils import shuffle
from sklearn.model_selection import RandomizedSearchCV, GridSearchCV, train_test_split, KFold, cross_val_score
from sklearn.svm import SVR, SVC
from sklearn import metrics
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
import itertools
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import RandomForestClassifier
import xgboost 
from xgboost import XGBClassifier
from xgboost import XGBRegressor

spy = pdr.get_data_yahoo('spy', start = '2007-01-01', end = '2017-10-1')
gld = pdr.get_data_yahoo('gld', start = '2007-01-01', end = '2017-10-1')
gdx = pdr.get_data_yahoo('gdx', start = '2007-01-01', end = '2017-10-1')

plt.figure(figsize=(15,7))
plt.plot(spy.Close)
plt.plot(gdx.Close)
plt.plot(gld.Close)
plt.xlabel('Date')
plt.ylabel('Value ($)')
plt.rcParams.update({'font.size': 18})

gdx['ratio_spy'] = gdx['Close'].values/(gld['Close'].values*(spy['Close'].values)**0.9)
gdx['ratio'] = gdx['Close'].values/(gld['Close'].values)**1
fig = plt.figure()
plt.rcParams.update({'font.size': 18})
plt.figure(figsize=(15,8))
plt.subplot(2, 2, 1)
plt.plot(spy.Close)
plt.title('spy')

plt.subplot(2, 2, 2)
plt.plot(gdx.Close)
plt.title('gdx')
plt.subplots_adjust(hspace = 0.4)

plt.subplot(2, 2, 3)
plt.plot(gld.Close)
plt.title('gld')

plt.subplot(2, 2, 4)
plt.plot(gdx.ratio)
plt.title('ratio')
plt.plot(gdx.ratio)
#pyplot.yscale('log')

p_gld, p_gdx, p_spy = [], [], []
for i in range(len(gdx)-1):
  p_gld.append(gld.Close[i+1]/gld.Close[i]-1)
  p_gdx.append(gdx.Close[i+1]/gdx.Close[i]-1)
  p_spy.append(spy.Close[i+1]/spy.Close[i]-1)

"""### There is correlation"""

plt.scatter(np.asarray(p_gld)*1.8, np.array(p_gdx)-np.array(p_spy));
from scipy.stats import pearsonr
corr, _ = pearsonr(np.asarray(p_gld)*1.5, np.array(p_gdx)-np.array(p_spy)*0.68)
print('Pearsons correlation: %.3f' % corr)

"""### Long term does not work"""

accum = 1
mult = 1.1
acc_list = []
for i in range(len(p_gdx)):
  accum += accum*(p_gdx[i]-p_gld[i]*mult)
  acc_list.append(accum)
plt.plot(acc_list)

def affinity(p_gld, p_gdx, multiplier, days):
  tendency = [0]*days
  for i in range(days, len(p_gld)):
    tendency.append(sum(p_gld[i-days:i])*multiplier-sum(p_gdx[i-days:i]))
  return tendency

aff_1 = affinity(p_gld, p_gdx, 1.7, 1)   
aff_2 = affinity(p_gld, p_gdx, 1.7, 2)
aff_4 = affinity(p_gld, p_gdx, 1.7, 4)
aff_8 = affinity(p_gld, p_gdx, 1.7, 8)
aff_16 = affinity(p_gld, p_gdx, 1.7, 16)
df = pd.DataFrame(list(zip(aff_1, aff_2, aff_4, aff_8, aff_16)), columns=['one', 'two', 'four', 'eight', 'sixteen'])
df

def affinity(p_gld, p_gdx, multiplier, days):
  tendency = [0]*(days-1)
  for i in range(days-1, len(p_gld)):
    tendency.append(sum(p_gld[i+1-days:i+1])*multiplier-sum(p_gdx[i+1-days:i+1]))
  return tendency

aff_1 = affinity(p_gld, p_gdx, 1.7, 1)   
aff_2 = affinity(p_gld, p_gdx, 1.7, 2)
aff_4 = affinity(p_gld, p_gdx, 1.7, 4)
aff_8 = affinity(p_gld, p_gdx, 1.7, 8)
aff_16 = affinity(p_gld, p_gdx, 1.7, 16)
aff_1_shifted = aff_1 + [0]
aff_1_shifted = aff_1_shifted[1:]
aff_2_shifted =  aff_2 + [0, 0]
aff_2_shifted = aff_2_shifted[2:]
aff_4_shifted =  aff_4 +[0,0,0,0]
aff_4_shifted = aff_4_shifted[4:]
df = pd.DataFrame(list(zip(p_gdx,p_gld, aff_1, aff_2, aff_4, aff_8, aff_16, aff_1_shifted, aff_2_shifted, aff_4_shifted)),
                  columns=['pct_gdx', 'pct_gld', 'one', 'two', 'four', 'eight', 'sixteen', 'aff_1_shifted', 'aff_2_shifted', 'aff_4_shifted'])
plt.hist(aff_2, bins=25)
plt.hist(aff_4, bins=25, alpha = 0.6)
plt.hist(aff_8, bins=25, alpha = 0.4)
plt.hist(aff_16, bins=25, alpha = 0.2);
df.head(10)

labels = []
for i in range(len(aff_1)):
  if aff_1[i] > 0.015:
    labels.append('red')
  elif aff_1[i] > 0 and aff_1[i]< 0.015:
    labels.append('yellow')
  elif aff_1[i] > -0.015 and aff_1[i]< 0:
    labels.append('yellow')
  else:
    labels.append('green')

labels = []
for i in range(len(df)):
  if df.aff_4_shifted[i] > 0.03:
    labels.append('red')
  elif df.aff_4_shifted[i] > 0 and df.aff_4_shifted[i]< 0.03:
    labels.append('white')
  elif df.aff_4_shifted[i] > -0.03 and df.aff_4_shifted[i]< 0:
    labels.append('white')
  else:
    labels.append('green')

from sklearn.decomposition import PCA
pca = PCA(n_components=2)
principalComponents = pca.fit_transform(np.column_stack((df['one'], df['two'], df['four'], df['eight'], df['sixteen'])))
pdf = pd.DataFrame(data = principalComponents
             , columns = ['one', 'two'])
a = pdf['one'].tolist()
b = pdf['two'].tolist()
plt.figure(figsize=(15,7))
plt.scatter(a,b, c = labels, alpha = 0.6)
#plt.axis([-0.2, 0.2, -0.1, 0.1]);

from sklearn.decomposition import PCA
pca = PCA(n_components=2)
principalComponents = pca.fit_transform(np.column_stack((aff_2, aff_4, aff_8, aff_16)))
pdf = pd.DataFrame(data = principalComponents
             , columns = ['one', 'two'])
a = pdf['one'].tolist()
b = pdf['two'].tolist()
plt.figure(figsize=(15,7))
plt.scatter(a,b, c = labels, alpha = 0.6)
#plt.axis([-0.2, 0.2, -0.1, 0.1]);

labels = ['yellow']
for i in range(len(aff_1)):
  if aff_1[i] > 0.015:
    labels.append('red')
  elif aff_1[i] > 0 and aff_1[i]< 0.015:
    labels.append('yellow')
  elif aff_1[i] > -0.015 and aff_1[i]< 0:
    labels.append('yellow')
  else:
    labels.append('green')
labels = labels[:-1]

from sklearn.manifold import TSNE
time_start = time.time()
tsne = TSNE(n_components=2, verbose=0, perplexity=100, n_iter=1500)
tsne_results = tsne.fit_transform(np.column_stack((aff_2, aff_4, aff_8, aff_16)))
print('t-SNE done! Time elapsed: {} seconds'.format(time.time()-time_start))
pdf = pd.DataFrame(data = tsne_results, columns = ['one', 'two'])
a = pdf['one'].tolist()
b = pdf['two'].tolist()
plt.figure(figsize=(15,7))
plt.scatter(a,b, c = labels, alpha = 0.7)

from sklearn.manifold import TSNE
time_start = time.time()
tsne = TSNE(n_components=2, verbose=0, perplexity=100, n_iter=1500)
tsne_results = tsne.fit_transform(np.column_stack((aff_2, aff_4, aff_8, aff_16)))
print('t-SNE done! Time elapsed: {} seconds'.format(time.time()-time_start))
pdf = pd.DataFrame(data = tsne_results, columns = ['one', 'two'])
a = pdf['one'].tolist()
b = pdf['two'].tolist()
plt.figure(figsize=(15,7))
plt.scatter(a,b, c = labels, alpha = 0.7)