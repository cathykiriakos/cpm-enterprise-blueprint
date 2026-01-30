"""
Churn Prediction Model for Public Media Sustainers
===================================================

Predicts probability of sustainer churn (cancellation or payment failure).

Model: Gradient Boosting Classifier
Target: Binary (churned within 90 days)
Features: Engagement, giving history, payment behavior

Author: Catherine Kiriakos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json
import pickle
import warnings
warnings.filterwarnings('ignore')

# Check for ML libraries
try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class ChurnPredictor:
    """Churn prediction model for sustaining members."""
    
    FEATURE_COLS = [
        'days_since_last_engagement',
        'days_since_last_donation',
        'email_open_rate_30d',
        'email_click_rate_30d',
        'tenure_months',
        'total_gifts',
        'avg_gift_amount',
        'consecutive_failed_payments',
        'sustainer_months',
        'engagement_score',
    ]
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importances_ = {}
        self._fitted = False
        
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features from raw constituent data."""
        features = pd.DataFrame(index=df.index)
        features['constituent_id'] = df['constituent_id']
        
        now = pd.Timestamp.now()
        
        # Days since dates
        for col in ['last_engagement_date', 'last_donation_date']:
            if col in df.columns:
                dates = pd.to_datetime(df[col], errors='coerce')
                features[f'days_since_{col.replace("_date", "")}'] = (now - dates).dt.days.fillna(999)
            else:
                features[f'days_since_{col.replace("_date", "")}'] = 999
        
        # Direct copies with defaults
        features['email_open_rate_30d'] = df.get('email_open_rate_30d', 0).fillna(0)
        features['email_click_rate_30d'] = df.get('email_click_rate_30d', 0).fillna(0)
        features['total_gifts'] = df.get('total_gift_count', 0).fillna(0)
        features['avg_gift_amount'] = df.get('average_gift_amount', 0).fillna(0)
        features['consecutive_failed_payments'] = df.get('consecutive_failed_payments', 0).fillna(0)
        
        # Tenure calculations
        if 'first_donation_date' in df.columns:
            first_dates = pd.to_datetime(df['first_donation_date'], errors='coerce')
            features['tenure_months'] = ((now - first_dates).dt.days / 30.44).fillna(0)
        else:
            features['tenure_months'] = 0
            
        if 'sustainer_start_date' in df.columns:
            sus_dates = pd.to_datetime(df['sustainer_start_date'], errors='coerce')
            features['sustainer_months'] = ((now - sus_dates).dt.days / 30.44).fillna(0)
        else:
            features['sustainer_months'] = 0
        
        # Composite engagement score
        features['engagement_score'] = (
            (1 - features['days_since_last_engagement'].clip(0, 365) / 365) * 50 +
            features['email_open_rate_30d'] * 50
        ).clip(0, 100)
        
        return features
    
    def train(self, df: pd.DataFrame, labels: pd.Series) -> Dict[str, float]:
        """Train the churn model."""
        if not ML_AVAILABLE:
            raise ImportError("scikit-learn required. Install: pip install scikit-learn")
        
        # Engineer features
        features = self._engineer_features(df)
        X = features[self.FEATURE_COLS].values
        y = labels.values
        
        # Split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state, stratify=y
        )
        
        # Scale
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=self.random_state
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Store feature importances
        self.feature_importances_ = dict(zip(self.FEATURE_COLS, self.model.feature_importances_))
        self._fitted = True
        
        # Evaluate
        y_pred_proba = self.model.predict_proba(X_val_scaled)[:, 1]
        y_pred = (y_pred_proba >= 0.5).astype(int)
        
        return {
            'auc': roc_auc_score(y_val, y_pred_proba),
            'precision': precision_score(y_val, y_pred),
            'recall': recall_score(y_val, y_pred),
            'f1': f1_score(y_val, y_pred),
        }
    
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate churn predictions."""
        if not self._fitted:
            raise ValueError("Model not trained")
        
        features = self._engineer_features(df)
        X = features[self.FEATURE_COLS].values
        X_scaled = self.scaler.transform(X)
        
        probas = self.model.predict_proba(X_scaled)[:, 1]
        
        # Assign tiers
        tiers = ['low'] * len(probas)
        for i, p in enumerate(probas):
            if p >= 0.85: tiers[i] = 'critical'
            elif p >= 0.6: tiers[i] = 'high'
            elif p >= 0.3: tiers[i] = 'medium'
        
        return pd.DataFrame({
            'constituent_id': features['constituent_id'],
            'churn_score': probas,
            'churn_tier': tiers,
            'prediction_date': datetime.now().date(),
        })
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importances."""
        return pd.DataFrame([
            {'feature': k, 'importance': v}
            for k, v in sorted(self.feature_importances_.items(), key=lambda x: -x[1])
        ])
    
    def save(self, path: str):
        """Save model to file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_importances': self.feature_importances_,
            }, f)
    
    @classmethod
    def load(cls, path: str) -> 'ChurnPredictor':
        """Load model from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        predictor = cls()
        predictor.model = data['model']
        predictor.scaler = data['scaler']
        predictor.feature_importances_ = data['feature_importances']
        predictor._fitted = True
        return predictor


def generate_sample_data(n: int = 5000) -> Tuple[pd.DataFrame, pd.Series]:
    """Generate synthetic data for training demonstration."""
    np.random.seed(42)
    
    df = pd.DataFrame({
        'constituent_id': [f'UC-{i:08d}' for i in range(n)],
        'last_engagement_date': pd.date_range(end=datetime.now(), periods=n) - 
            pd.to_timedelta(np.random.exponential(30, n), unit='D'),
        'last_donation_date': pd.date_range(end=datetime.now(), periods=n) - 
            pd.to_timedelta(np.random.exponential(45, n), unit='D'),
        'first_donation_date': pd.date_range(end=datetime.now()-timedelta(365), periods=n) - 
            pd.to_timedelta(np.random.exponential(365, n), unit='D'),
        'sustainer_start_date': pd.date_range(end=datetime.now()-timedelta(180), periods=n) - 
            pd.to_timedelta(np.random.exponential(180, n), unit='D'),
        'email_open_rate_30d': np.clip(np.random.beta(2, 5, n), 0, 1),
        'email_click_rate_30d': np.clip(np.random.beta(1, 10, n), 0, 1),
        'total_gift_count': np.random.poisson(10, n),
        'average_gift_amount': np.random.exponential(50, n),
        'consecutive_failed_payments': np.random.choice([0]*4 + [1, 2, 3], n),
    })
    
    # Generate labels based on features
    days_inactive = (datetime.now() - df['last_engagement_date']).dt.days
    churn_prob = np.clip(
        0.1 + 0.002 * days_inactive + 0.3 * (1 - df['email_open_rate_30d']) + 
        0.15 * df['consecutive_failed_payments'], 0, 1
    )
    labels = (np.random.random(n) < churn_prob).astype(int)
    
    return df, pd.Series(labels)


if __name__ == "__main__":
    print("="*60)
    print("CHURN PREDICTION MODEL DEMO")
    print("="*60)
    
    if not ML_AVAILABLE:
        print("Error: Install scikit-learn: pip install scikit-learn")
        exit(1)
    
    # Generate data
    print("\n1. Generating synthetic data...")
    df, labels = generate_sample_data(5000)
    print(f"   {len(df)} samples, {labels.mean()*100:.1f}% churn rate")
    
    # Train
    print("\n2. Training model...")
    model = ChurnPredictor()
    metrics = model.train(df, labels)
    print(f"   AUC: {metrics['auc']:.4f}")
    print(f"   Precision: {metrics['precision']:.4f}")
    print(f"   Recall: {metrics['recall']:.4f}")
    
    # Feature importance
    print("\n3. Feature Importance:")
    for _, row in model.get_feature_importance().head(5).iterrows():
        print(f"   {row['feature']}: {row['importance']:.4f}")
    
    # Predict
    print("\n4. Sample Predictions:")
    preds = model.predict(df.head(10))
    print(preds[['constituent_id', 'churn_score', 'churn_tier']])
    
    # Save
    print("\n5. Saving model...")
    model.save('data/models/churn_model.pkl')
    print("   Saved to data/models/churn_model.pkl")
    
    print("\n" + "="*60)