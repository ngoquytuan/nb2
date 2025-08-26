import json
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import re

class NaiveBayesFilter:
    def __init__(self, model_path: str = 'models/nb_model.pkl'):
        self.model_path = model_path
        self.pipeline = None
        self.load_or_train_model()
    
    def preprocess_text(self, text: str) -> str:
        """Tiền xử lý văn bản tiếng Việt"""
        # Chuyển về chữ thường
        text = text.lower()
        # Loại bỏ ký tự đặc biệt, giữ lại chữ cái và số
        text = re.sub(r'[^\w\s]', ' ', text)
        # Loại bỏ khoảng trắng thừa
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def load_training_data(self) -> tuple:
        """Load dữ liệu training từ file JSON"""
        with open('data/training_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        texts = []
        labels = []
        
        # Legitimate messages (label = 0)
        for text in data['legitimate']:
            texts.append(self.preprocess_text(text))
            labels.append(0)
        
        # Spam messages (label = 2)
        for text in data['spam']:
            texts.append(self.preprocess_text(text))
            labels.append(2)
        
        # Suspicious messages (label = 1)
        for text in data['suspicious']:
            texts.append(self.preprocess_text(text))
            labels.append(1)
        
        return texts, labels
    
    def train_model(self):
        """Huấn luyện model Naive Bayes"""
        print("Training Naive Bayes model...")
        
        texts, labels = self.load_training_data()
        
        # Tạo pipeline: TF-IDF + Naive Bayes
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words=None  # Không dùng stop words cho tiếng Việt
            )),
            ('nb', MultinomialNB(alpha=1.0))
        ])
        
        # Train model
        self.pipeline.fit(texts, labels)
        
        # Lưu model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.pipeline, f)
        
        print(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load model đã train"""
        try:
            with open(self.model_path, 'rb') as f:
                self.pipeline = pickle.load(f)
            print(f"Model loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            print(f"Model file not found: {self.model_path}")
            return False
    
    def load_or_train_model(self):
        """Load model hoặc train nếu chưa có"""
        if not self.load_model():
            self.train_model()
    
    def predict(self, text: str) -> tuple:
        """
        Dự đoán phân loại message
        Returns: (prediction, probability_scores)
        prediction: 0=legitimate, 1=suspicious, 2=spam
        probability_scores: [prob_legitimate, prob_suspicious, prob_spam]
        """
        if not self.pipeline:
            raise Exception("Model chưa được load hoặc train")
        
        processed_text = self.preprocess_text(text)
        
        # Predict class
        prediction = self.pipeline.predict([processed_text])[0]
        
        # Get probability scores
        probabilities = self.pipeline.predict_proba([processed_text])[0]
        
        return int(prediction), probabilities.tolist()
    
    def get_classification_name(self, prediction: int) -> str:
        """Chuyển đổi số prediction thành tên"""
        mapping = {0: 'legitimate', 1: 'suspicious', 2: 'spam'}
        return mapping.get(prediction, 'unknown')