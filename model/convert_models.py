import joblib
from xgboost import XGBRegressor, XGBClassifier

model_names = ['intensity', 'hedonic', 'tension', 'complexity']
for name in model_names:
    model = joblib.load(f'models/{name}_model.pkl')
    if isinstance(model, (XGBRegressor, XGBClassifier)):
        model.save_model(f'models/{name}_model.json')
        print(f'已转换: {name}_model.pkl -> {name}_model.json')
    else:
        print(f'{name}_model 是 {type(model).__name__}，跳过转换')