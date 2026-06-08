import os
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import src.database as db

class TransactionCategorizer:
    def __init__(self):
        self.pipeline = None
        self.is_trained = False
        
        # Rule-based fallback dictionary
        self.rules = {
            "coffee": "Food & Dining",
            "starbucks": "Food & Dining",
            "mcdonald": "Food & Dining",
            "burger": "Food & Dining",
            "pizza": "Food & Dining",
            "diner": "Food & Dining",
            "cafe": "Food & Dining",
            "food": "Food & Dining",
            "restaurant": "Food & Dining",
            
            "grocery": "Groceries",
            "supermarket": "Groceries",
            "kroger": "Groceries",
            "whole foods": "Groceries",
            "walmart": "Groceries",
            "safeway": "Groceries",
            "trader joe": "Groceries",
            
            "uber": "Transportation",
            "lyft": "Transportation",
            "taxi": "Transportation",
            "transit": "Transportation",
            "gas": "Transportation",
            "fuel": "Transportation",
            "shell": "Transportation",
            "exxon": "Transportation",
            
            "netflix": "Bills & Utilities",
            "spotify": "Bills & Utilities",
            "comcast": "Bills & Utilities",
            "internet": "Bills & Utilities",
            "utility": "Bills & Utilities",
            "electric": "Bills & Utilities",
            "power": "Bills & Utilities",
            "mobile": "Bills & Utilities",
            "att": "Bills & Utilities",
            "verizon": "Bills & Utilities",
            
            "rent": "Housing",
            "housing": "Housing",
            "apartment": "Housing",
            "mortgage": "Housing",
            "hardware": "Housing",
            "home depot": "Housing",
            
            "zara": "Shopping",
            "amazon": "Shopping",
            "target": "Shopping",
            "clothing": "Shopping",
            "mall": "Shopping",
            "store": "Shopping",
            
            "movie": "Entertainment",
            "theater": "Entertainment",
            "amc": "Entertainment",
            "concert": "Entertainment",
            "tickets": "Entertainment",
            "park": "Entertainment",
            "disney": "Entertainment",
            "game": "Entertainment",
            
            "salary": "Income",
            "payroll": "Income",
            "freelance": "Income",
            "dividend": "Income",
            "payment": "Income",
            
            "etf": "Investments",
            "vanguard": "Investments",
            "coinbase": "Investments",
            "btc": "Investments",
            "stock": "Investments",
            "crypto": "Investments"
        }

    def _rule_based_classify(self, description: str) -> str:
        """Classify transaction description using pre-defined rules."""
        desc_lower = description.lower().strip()
        for keyword, category in self.rules.items():
            if keyword in desc_lower:
                return category
        return "Shopping"  # Default category fallback

    def train(self):
        """Fetches training data from the database and trains the TF-IDF + Logistic Regression model."""
        df = db.get_ml_training_data()
        
        # Check if we have enough distinct classes and samples to train an ML model
        if len(df) < 10 or df["category"].nunique() < 3:
            # Not enough data, use rule-based fallback
            self.is_trained = False
            return
        
        try:
            # Define Pipeline: Convert text to TF-IDF n-grams, then apply Logistic Regression
            self.pipeline = Pipeline([
                ("tfidf", TfidfVectorizer(
                    ngram_range=(1, 2), 
                    lowercase=True, 
                    token_pattern=r"(?u)\b\w+\b", # capture single characters if needed
                    min_df=1
                )),
                ("clf", LogisticRegression(C=1.5, max_iter=1000))
            ])
            
            X = df["description"].str.lower()
            y = df["category"]
            
            self.pipeline.fit(X, y)
            self.is_trained = True
        except Exception as e:
            print(f"Error training categorizer: {e}")
            self.is_trained = False

    def predict(self, description: str) -> tuple[str, float]:
        """Predicts the category of a transaction and returns (category, confidence)."""
        desc_cleaned = description.strip().lower()
        
        # If ML model is not trained or error occurs, fallback to rules
        if not self.is_trained or self.pipeline is None:
            category = self._rule_based_classify(desc_cleaned)
            # Rule matches have 1.0 confidence, otherwise 0.5 default fallback
            confidence = 1.0 if category != "Shopping" or "shopping" in desc_cleaned else 0.5
            return category, confidence
        
        try:
            # Pred probabilities
            probs = self.pipeline.predict_proba([desc_cleaned])[0]
            max_idx = np.argmax(probs)
            category = self.pipeline.classes_[max_idx]
            confidence = float(probs[max_idx])
            
            # If confidence is very low (e.g. < 35%), try rule based override
            if confidence < 0.35:
                rule_cat = self._rule_based_classify(desc_cleaned)
                if rule_cat != "Shopping":
                    return rule_cat, 0.60
                    
            return category, confidence
        except Exception:
            # Safety fallback
            category = self._rule_based_classify(desc_cleaned)
            return category, 0.5

    def add_override(self, description: str, correct_category: str):
        """Inserts an override category and retrains the model immediately."""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO ml_training_data (description, category) VALUES (?, ?)",
            (description.strip().lower(), correct_category)
        )
        conn.commit()
        conn.close()
        
        # Retrain the model with the new data
        self.train()

# Singleton categorizer instance
_categorizer = None

def get_categorizer():
    global _categorizer
    if _categorizer is None:
        _categorizer = TransactionCategorizer()
        _categorizer.train()
    return _categorizer
