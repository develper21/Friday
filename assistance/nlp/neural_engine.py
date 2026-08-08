"""
JeanMax Neural Engine
Loads PyTorch Neural Model (JeanMax.pt) for intent prediction and conversational response generation.
"""

import os
import torch
import numpy as np
import math
import re
from typing import Optional, Tuple
from assistance.nlp.parser import Intent, ParsedCommand

# Re-create vectorizer for inference loading
class InferenceVectorizer:
    def __init__(self, vocab, idf):
        self.vocab = vocab
        self.idf = idf

    def _tokenize(self, text: str):
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)]
        trigrams = [f"{words[i]}_{words[i+1]}_{words[i+2]}" for i in range(len(words)-2)]
        return words + bigrams + trigrams

    def transform(self, text: str):
        tokens = self._tokenize(text)
        vector = np.zeros(len(self.vocab), dtype=np.float32)
        tf = {}
        for token in tokens:
            if token in self.vocab:
                tf[token] = tf.get(token, 0) + 1

        for token, count in tf.items():
            idx = self.vocab[token]
            vector[idx] = count * self.idf.get(token, 1.0)

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector

# Neural Network Architecture definition matching multi-task JeanMax.pt checkpoint
class JeanMaxNeuralNet(torch.nn.Module):
    def __init__(self, input_dim: int, num_intents: int, num_responses: int):
        super(JeanMaxNeuralNet, self).__init__()
        self.fc1 = torch.nn.Linear(input_dim, 256)
        self.ln1 = torch.nn.LayerNorm(256)
        self.relu1 = torch.nn.ReLU()
        self.dropout1 = torch.nn.Dropout(0.2)

        self.fc2 = torch.nn.Linear(256, 128)
        self.ln2 = torch.nn.LayerNorm(128)
        self.relu2 = torch.nn.ReLU()
        self.dropout2 = torch.nn.Dropout(0.1)

        # Intent classification head
        self.intent_head = torch.nn.Linear(128, num_intents)
        
        # Response generation head
        self.response_head = torch.nn.Linear(128, num_responses)

    def forward(self, x):
        out = self.fc1(x)
        out = self.ln1(out)
        out = self.relu1(out)
        out = self.dropout1(out)

        out = self.fc2(out)
        out = self.ln2(out)
        out = self.relu2(out)
        out = self.dropout2(out)

        # Return both intent logits and response logits
        intent_logits = self.intent_head(out)
        response_logits = self.response_head(out)
        return intent_logits, response_logits


class JeanMaxNeuralEngine:
    """
    Loads JeanMax.pt PyTorch neural model checkpoint and executes inference.
    Now supports multi-task learning: intent classification + conversational response generation.
    """
    def __init__(self, model_path: str = None):
        # Auto-detect model path if not provided
        if model_path is None:
            # Try multiple possible locations
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "../../model/JeanMax.pt"),
                os.path.join(os.path.dirname(__file__), "../../../model/JeanMax.pt"),
                "model/JeanMax.pt",
                "../model/JeanMax.pt",
                "/home/narvin/Documents/AI/Friday/model/JeanMax.pt"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
        
        self.model_path = model_path
        self.model = None
        self.vectorizer = None
        self.intent_map = {}
        self.response_map = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = self.load_model()

    def load_model(self) -> bool:
        """Load PyTorch checkpoint file with multi-task support"""
        if self.model_path is None or not os.path.exists(self.model_path):
            print(f" PyTorch checkpoint not found. Checked multiple locations. Running training first...")
            return False

        try:
            checkpoint = torch.load(self.model_path, map_location=self.device)
            input_dim = checkpoint["input_dim"]
            
            # Check if multi-task model
            if "num_intents" in checkpoint and "num_responses" in checkpoint:
                num_intents = checkpoint["num_intents"]
                num_responses = checkpoint["num_responses"]
                self.intent_map = checkpoint["intent_map"]
                self.response_map = checkpoint["response_map"]
                
                self.vectorizer = InferenceVectorizer(
                    vocab=checkpoint["vectorizer_vocab"],
                    idf=checkpoint["vectorizer_idf"]
                )

                self.model = JeanMaxNeuralNet(input_dim, num_intents, num_responses).to(self.device)
                self.model.load_state_dict(checkpoint["model_state_dict"])
                self.model.eval()

                print(f"🧠 PyTorch JeanMax.pt Multi-Task Model loaded successfully! (Device: {self.device})")
                print(f"   - Intents: {num_intents}, Responses: {num_responses}")
            else:
                # Fallback for old single-task model
                num_classes = checkpoint["num_classes"]
                self.intent_map = checkpoint["intent_map"]
                
                self.vectorizer = InferenceVectorizer(
                    vocab=checkpoint["vectorizer_vocab"],
                    idf=checkpoint["vectorizer_idf"]
                )

                # Create multi-task model with dummy response head
                self.model = JeanMaxNeuralNet(input_dim, num_classes, 1).to(self.device)
                # Load only matching layers
                state_dict = checkpoint["model_state_dict"]
                new_state_dict = {}
                for key in state_dict:
                    if "response_head" not in key:  # Skip response head for old models
                        new_state_dict[key] = state_dict[key]
                self.model.load_state_dict(new_state_dict, strict=False)
                self.model.eval()

                print(f"🧠 PyTorch JeanMax.pt Legacy Model loaded successfully! (Device: {self.device})")
            
            return True
        except Exception as e:
            print(f"❌ Failed to load PyTorch model {self.model_path}: {e}")
            return False

    def predict(self, text: str) -> Tuple[Optional[ParsedCommand], Optional[str]]:
        """
        Run forward pass through JeanMax.pt neural network
        Returns: (ParsedCommand, conversational_response)
        """
        if not self.is_loaded or not text:
            return None, None

        text_clean = text.lower().strip()
        vec = self.vectorizer.transform(text_clean)
        inp = torch.tensor(vec, dtype=torch.float32).unsqueeze(0).to(self.device)

        with torch.no_grad():
            intent_logits, response_logits = self.model(inp)
            intent_probs = torch.softmax(intent_logits, dim=1)
            response_probs = torch.softmax(response_logits, dim=1)
            
            intent_confidence, intent_pred_idx = torch.max(intent_probs, 1)
            response_confidence, response_pred_idx = torch.max(response_probs, 1)

            intent_conf_val = intent_confidence.item()
            response_conf_val = response_confidence.item()
            
            intent_str = self.intent_map.get(intent_pred_idx.item(), "UNKNOWN")

            # Map to Intent Enum
            try:
                intent_enum = Intent[intent_str]
            except KeyError:
                intent_enum = Intent.UNKNOWN

            # Extract entity
            entity = self._extract_entity(text_clean, intent_enum)

            # Get conversational response if confidence is high enough
            conversational_response = None
            if self.response_map and response_conf_val > 0.3:
                response_str = self.response_map.get(response_pred_idx.item(), "")
                if response_str:
                    conversational_response = response_str

            return ParsedCommand(
                intent=intent_enum,
                entity=entity,
                confidence=intent_conf_val
            ), conversational_response

    def _extract_entity(self, text: str, intent: Intent) -> Optional[str]:
        """Extract entity for tasks"""
        if intent in [Intent.OPEN_APP, Intent.CLOSE_APP]:
            for pattern in ["open", "launch", "start", "run", "close", "quit", "exit", "kill", "terminate"]:
                if pattern in text:
                    parts = text.split(pattern)
                    if len(parts) > 1 and parts[1].strip():
                        entity = parts[1].strip()
                        entity = entity.replace("the", "").replace("please", "").replace("can you", "")
                        entity = entity.replace("app", "").replace("application", "").replace("a", "").replace("an", "").strip()
                        if entity:
                            return entity
        elif intent == Intent.WEATHER:
            for pattern in ["weather", "temperature", "forecast", "mausam"]:
                if pattern in text:
                    parts = text.split(pattern)
                    if len(parts) > 1 and parts[1].strip():
                        loc = parts[1].strip().replace("in", "").replace("for", "").strip()
                        if loc:
                            return loc
        elif intent == Intent.SEARCH_WEB:
            for pattern in ["search google for", "search youtube for", "search web for", "google search", "youtube search", "search for", "search"]:
                if pattern in text:
                    parts = text.split(pattern)
                    if len(parts) > 1 and parts[1].strip():
                        return parts[1].strip()
            return text

        return None
