"""
Upgrade Propensity Model - Predicts likelihood of donor upgrades.
Upgrade paths: one-time->sustainer, sustainer->increase, any->major gift
Author: Catherine Kiriakos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple
from pathlib import Path
import pickle

try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.metrics import roc_auc_score, precision_score, recall_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class UpgradePropensityModel:
    """Multi-target model for predicting upgrade likelihood."""
    
    FEATURES = ['tenure_months', 'total_gifts', 'avg_gift', 'max_gift', 
                'gift_frequency', 'days_since_gift', 'email_open_rate',
                'events_attended', 'engagement_score', 'capacity_score']
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.models = {}
        self.scalers = {}
        self._fitted = False
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        now = pd.Timestamp.now()
        f = pd.DataFrame(index=df.index)
        f['constituent_id'] = df['constituent_id']
        
        # Tenure
        if 'first_donation_date' in df.columns:
            dates = pd.to_datetime(df['first_donation_date'], errors='coerce')
            f['tenure_months'] = ((now - dates).dt.days / 30.44).fillna(12).clip(0, 120)
        else:
            f['tenure_months'] = 12
        
        f['total_gifts'] = df['total_gift_count'].fillna(1) if 'total_gift_count' in df.columns else 1
        f['avg_gift'] = df['average_gift_amount'].fillna(50) if 'average_gift_amount' in df.columns else 50
        f['max_gift'] = df['largest_single_gift'].fillna(50) if 'largest_single_gift' in df.columns else 50
        f['gift_frequency'] = (f['total_gifts'] / (f['tenure_months'] / 12).clip(1)).clip(0, 24)
        
        if 'last_donation_date' in df.columns:
            dates = pd.to_datetime(df['last_donation_date'], errors='coerce')
            f['days_since_gift'] = (now - dates).dt.days.fillna(60).clip(0, 365)
        else:
            f['days_since_gift'] = 30
        
        f['email_open_rate'] = df['email_open_rate_30d'].fillna(0.3) if 'email_open_rate_30d' in df.columns else 0.3
        f['events_attended'] = df['events_attended_12m'].fillna(0) if 'events_attended_12m' in df.columns else 0
        f['engagement_score'] = ((1 - f['days_since_gift']/365)*40 + f['email_open_rate']*30 + 
                                 f['gift_frequency'].clip(0,4)/4*30).clip(0, 100)
        f['capacity_score'] = (np.log1p(f['max_gift'])*10 + np.log1p(f['total_gifts']*f['avg_gift'])*5).clip(0, 100)
        
        return f
    
    def train(self, df: pd.DataFrame, labels: Dict[str, pd.Series]) -> Dict[str, Dict]:
        if not ML_AVAILABLE:
            raise ImportError("scikit-learn required")
        
        features = self._engineer_features(df)
        X = features[self.FEATURES].values
        metrics = {}
        
        for target, y in labels.items():
            # Handle both Series and array-like inputs
            y_values = y.values if hasattr(y, 'values') else y
            X_tr, X_val, y_tr, y_val = train_test_split(X, y_values, test_size=0.2, 
                                                         random_state=self.seed)
            scaler = StandardScaler()
            X_tr_s = scaler.fit_transform(X_tr)
            X_val_s = scaler.transform(X_val)
            
            model = GradientBoostingClassifier(n_estimators=100, max_depth=5, 
                                                learning_rate=0.1, random_state=self.seed)
            model.fit(X_tr_s, y_tr)
            
            self.models[target] = model
            self.scalers[target] = scaler
            
            y_prob = model.predict_proba(X_val_s)[:, 1]
            metrics[target] = {
                'auc': roc_auc_score(y_val, y_prob),
                'precision': precision_score(y_val, (y_prob >= 0.5).astype(int), zero_division=0),
                'recall': recall_score(y_val, (y_prob >= 0.5).astype(int), zero_division=0),
            }
        
        self._fitted = True
        return metrics
    
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._fitted:
            raise ValueError("Model not trained")
        
        features = self._engineer_features(df)
        X = features[self.FEATURES].values
        
        results = pd.DataFrame({'constituent_id': features['constituent_id']})
        
        for target, model in self.models.items():
            X_s = self.scalers[target].transform(X)
            results[f'{target}_score'] = model.predict_proba(X_s)[:, 1]
        
        score_cols = [c for c in results.columns if c.endswith('_score')]
        results['upgrade_propensity'] = results[score_cols].max(axis=1)
        results['best_path'] = results[score_cols].idxmax(axis=1).str.replace('_score', '')
        
        return results
    
    def get_recommendations(self, preds: pd.DataFrame, churn: pd.DataFrame = None) -> pd.DataFrame:
        recs = preds[['constituent_id', 'upgrade_propensity', 'best_path']].copy()
        
        if churn is not None:
            recs = recs.merge(churn[['constituent_id', 'churn_score']], on='constituent_id', how='left')
        recs['churn_score'] = recs.get('churn_score', 0.3).fillna(0.3)
        
        def action(r):
            hi_up, hi_ch = r['upgrade_propensity'] >= 0.5, r['churn_score'] >= 0.5
            if hi_up and not hi_ch: return 'prime_target'
            if hi_up and hi_ch: return 'careful_ask'
            if not hi_up and not hi_ch: return 'nurture'
            return 'save_first'
        
        recs['action'] = recs.apply(action, axis=1)
        recs['priority'] = (recs['upgrade_propensity']*100 - recs['churn_score']*50).clip(0, 100)
        
        return recs.sort_values('priority', ascending=False)
    
    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({'models': self.models, 'scalers': self.scalers}, f)
    
    @classmethod
    def load(cls, path: str):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        m = cls()
        m.models, m.scalers = data['models'], data['scalers']
        m._fitted = True
        return m


def generate_sample_data(n: int = 5000):
    np.random.seed(42)
    df = pd.DataFrame({
        'constituent_id': [f'UC-{i:08d}' for i in range(n)],
        'first_donation_date': pd.date_range(end=datetime.now()-timedelta(365), periods=n) - 
                               pd.to_timedelta(np.random.exponential(500, n), unit='D'),
        'last_donation_date': pd.date_range(end=datetime.now(), periods=n) - 
                              pd.to_timedelta(np.random.exponential(60, n), unit='D'),
        'total_gift_count': np.random.poisson(8, n) + 1,
        'average_gift_amount': np.random.exponential(45, n) + 10,
        'largest_single_gift': np.random.exponential(100, n) + 25,
        'email_open_rate_30d': np.clip(np.random.beta(3, 5, n), 0, 1),
        'events_attended_12m': np.random.poisson(0.5, n),
        'is_sustainer': np.random.choice([True, False], n, p=[0.35, 0.65]),
    })
    
    eng = df['email_open_rate_30d'] + df['events_attended_12m'] * 0.1
    cap = np.log1p(df['largest_single_gift']) / 5
    
    labels = {
        'to_sustainer': pd.Series(((np.random.random(n) < 0.05 + eng*0.2 + cap*0.1) & ~df['is_sustainer']).astype(int)),
        'sustainer_increase': pd.Series(((np.random.random(n) < 0.1 + eng*0.15) & df['is_sustainer']).astype(int)),
        'to_major': pd.Series((np.random.random(n) < 0.01 + cap*0.05).astype(int)),
    }
    return df, labels


if __name__ == "__main__":
    if not ML_AVAILABLE:
        print("Install scikit-learn: pip install scikit-learn")
        exit(1)
    
    print("Generating data...")
    df, labels = generate_sample_data(5000)
    
    print("Training models...")
    model = UpgradePropensityModel()
    metrics = model.train(df, labels)
    
    for t, m in metrics.items():
        print(f"  {t}: AUC={m['auc']:.3f}")
    
    print("\nSample predictions:")
    preds = model.predict(df.head(10))
    print(preds[['constituent_id', 'upgrade_propensity', 'best_path']])
    
    model.save('data/models/upgrade_model.pkl')
    print("\nModel saved.")