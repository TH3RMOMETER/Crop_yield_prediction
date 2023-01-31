from tensorflow import keras
import numpy as np
import pandas as pd
from tensorflow.keras import backend as K


def root_mean_squared_error(y_true, y_pred):
    return K.sqrt(K.mean(K.square(y_pred - y_true)))


def norm_df(df, cols):
    for col in cols:
        df[col] = df[col] / df[col].max()
    return df


def get_data(data_set, location, date_range, normalize=False):
    start_date = date_range[0]
    end_date = date_range[-1]
    if normalize:
        data_set = norm_df(data_set, ['tavg','prcp','tavg_shift','prcp_shift'])
    data_set['date'] = pd.to_datetime(data_set['date'])
    data_set = data_set.query(
        'date >= @start_date & date <= @end_date & name == @location')
    data_set = data_set[['NDVI_mean', 'NDMI_mean',
                         'NBSI_mean', 'tavg_shift', 'prcp_shift', 'date']]
    print(data_set)
    return data_set


def get_model_predictions(filepath: str, location: str, date_range=None):
    model = keras.models.load_model(
        filepath, custom_objects={'root_mean_squared_error': root_mean_squared_error})
    data_set = pd.read_pickle('df_shift_14.pickle')
    data = get_data(data_set=data_set, location=location, date_range=date_range, normalize = True)
    data = data.drop(['date'], axis=1).to_numpy()
    return model.predict(data[np.newaxis, ...])

def get_weather(location: str, date_range=None):
    data_set = pd.read_pickle('df_shift_14.pickle')
    data = get_data(data_set=data_set, location=location, date_range=date_range, normalize = False)
    return data[['tavg_shift', 'prcp_shift', 'date']]