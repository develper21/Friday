"""
JeanMax PyTorch Model Training Pipeline
Trains an end-to-end PyTorch Neural Model (JeanMax.pt) for Voice Task Intent Classification & Entity Extraction.
"""

import os
import re
import math
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import sys

# Add data directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))
from conversational_data import CONVERSATIONAL_CORPUS
from command_data import TRAINING_CORPUS, INTENT_MAP, INTENT_TO_ID

# ---------------------------------------------------------
# 2. Text Vectorizer (N-Gram Feature Encoder)
# ---------------------------------------------------------
class TextVectorizer:
    def __init__(self, max_features: int = 500):
        self.max_features = max_features
        self.vocab = {}
        self.idf = {}

    def fit(self, texts):
        doc_freq = {}
        total_docs = len(texts)

        for text in texts:
            tokens = self._tokenize(text)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        # Select top features
        sorted_tokens = sorted(doc_freq.items(), key=lambda x: x[1], reverse=True)[:self.max_features]
        self.vocab = {token: idx for idx, (token, _) in enumerate(sorted_tokens)}

        for token, idx in self.vocab.items():
            self.idf[token] = math.log((1 + total_docs) / (1 + doc_freq[token])) + 1.0

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

        # L2 Normalization
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector


# ---------------------------------------------------------
# 3. PyTorch Deep Neural Network Architecture (Multi-Task)
# ---------------------------------------------------------
class JeanMaxNeuralNet(nn.Module):
    def __init__(self, input_dim: int, num_intents: int, num_responses: int):
        super(JeanMaxNeuralNet, self).__init__()
        self.fc1 = nn.Linear(input_dim, 256)
        self.ln1 = nn.LayerNorm(256)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(0.2)

        self.fc2 = nn.Linear(256, 128)
        self.ln2 = nn.LayerNorm(128)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(0.1)

        # Intent classification head (existing)
        self.intent_head = nn.Linear(128, num_intents)
        
        # Response generation head (new for conversational AI)
        self.response_head = nn.Linear(128, num_responses)

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


# ---------------------------------------------------------
# 4. Dataset Class (Multi-Task)
# ---------------------------------------------------------
class MultiTaskDataset(Dataset):
    def __init__(self, X, y_intent, y_response):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y_intent = torch.tensor(y_intent, dtype=torch.long)
        self.y_response = torch.tensor(y_response, dtype=torch.long)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y_intent[idx], self.y_response[idx]


# ---------------------------------------------------------
# 5. Transfer Learning Helper Functions
# ---------------------------------------------------------
def load_existing_model(model_path, device):
    """
    Load existing model checkpoint for fine-tuning
    
    Returns:
        checkpoint, intent_map, vocab, idf
    """
    if not os.path.exists(model_path):
        return None, None, None, None
    
    try:
        checkpoint = torch.load(model_path, map_location=device)
        return (
            checkpoint, 
            checkpoint.get("intent_map", {}), 
            checkpoint.get("vectorizer_vocab", {}), 
            checkpoint.get("vectorizer_idf", {})
        )
    except Exception as e:
        print(f"⚠️ Could not load existing model: {e}")
        return None, None, None, None


def get_new_intents(existing_intent_map, current_intent_map):
    """
    Identify new intents that need training
    
    Returns:
        List of new intent names
    """
    if not existing_intent_map:
        return list(current_intent_map.values())
    
    existing_intents = set(existing_intent_map.values())
    current_intents = set(current_intent_map.values())
    new_intents = current_intents - existing_intents
    return list(new_intents)


# ---------------------------------------------------------
# 6. Training Pipeline Execution (Multi-Task with Fine-Tuning)
# ---------------------------------------------------------
def train_model(fine_tune: bool = True):
    """
    Train JeanMax model with support for fine-tuning on new intents only.
    
    Args:
        fine_tune: If True and existing model exists, only train new intents (transfer learning)
                  If False, train from scratch
    """
    # Create model directory if it doesn't exist
    model_dir = "/home/narvin/Documents/AI/Friday/model"
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "JeanMax.pt")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load existing model if available
    existing_checkpoint, existing_intent_map, existing_vocab, existing_idf = load_existing_model(model_path, device)
    
    new_intents = get_new_intents(existing_intent_map, INTENT_MAP)
    
    if fine_tune and existing_checkpoint and new_intents:
        print(f"🔄 Fine-tuning mode: Found {len(new_intents)} new intents to train")
        print(f"   New intents: {new_intents}")
        print(f"   Existing intents will be frozen to save training time")
    elif fine_tune and existing_checkpoint and not new_intents:
        print("✅ No new intents detected. Model is already up-to-date.")
        return
    else:
        print("🚀 Training from scratch (no existing model or full retrain requested)")
    
    print("🚀 Initializing JeanMax PyTorch Multi-Task Training Pipeline...")
    
    # Create response mapping from conversational corpus
    all_responses = list(set([item[1] for item in CONVERSATIONAL_CORPUS]))
    RESPONSE_MAP = {i: response for i, response in enumerate(all_responses)}
    RESPONSE_TO_ID = {response: i for i, response in enumerate(all_responses)}
    print(f"📊 Created response mapping with {len(RESPONSE_MAP)} unique responses")
    
    # Combine command corpus and conversational corpus
    command_texts = [item[0] for item in TRAINING_CORPUS]
    command_labels = [item[1] for item in TRAINING_CORPUS]
    
    conversational_texts = [item[0] for item in CONVERSATIONAL_CORPUS]
    conversational_response_labels = [RESPONSE_TO_ID[item[1]] for item in CONVERSATIONAL_CORPUS]
    # For conversational inputs, use GREETING intent as placeholder
    conversational_intent_labels = [INTENT_TO_ID["GREETING"]] * len(conversational_texts)
    
    # Fit Feature Vectorizer on all texts
    all_texts = command_texts + conversational_texts
    vectorizer = TextVectorizer(max_features=500)
    
    # If fine-tuning, try to use existing vectorizer to maintain consistency
    if fine_tune and existing_vocab and existing_idf:
        print("📝 Using existing vectorizer for consistency")
        # Extend existing vocab with new tokens
        vectorizer.vocab = existing_vocab.copy()
        vectorizer.idf = existing_idf.copy()
        # Fit on new texts only to add new tokens
        vectorizer.fit(all_texts)
    else:
        vectorizer.fit(all_texts)

    # Vectorize both datasets
    X_command = np.array([vectorizer.transform(t) for t in command_texts])
    X_conversational = np.array([vectorizer.transform(t) for t in conversational_texts])
    
    # Combine datasets
    X_combined = np.vstack([X_command, X_conversational])
    y_intent_combined = np.array(command_labels + conversational_intent_labels)
    y_response_combined = np.array([-1] * len(command_labels) + conversational_response_labels)  # -1 for no response
    
    dataset = MultiTaskDataset(X_combined, y_intent_combined, y_response_combined)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

    input_dim = len(vectorizer.vocab)
    num_intents = len(INTENT_MAP)
    num_responses = len(RESPONSE_MAP)

    print(f"🖥️ Using training device: {device}")

    # Create model
    model = JeanMaxNeuralNet(input_dim, num_intents, num_responses).to(device)
    
    # Load existing weights if fine-tuning
    if fine_tune and existing_checkpoint:
        try:
            # Load matching layers
            state_dict = existing_checkpoint["model_state_dict"]
            new_state_dict = {}
            
            for key in state_dict:
                # Skip intent_head if number of intents changed
                if "intent_head" in key and num_intents != existing_checkpoint.get("num_intents", 0):
                    print(f"⚠️ Skipping {key} (intent count changed)")
                    continue
                # Skip response_head if number of responses changed
                if "response_head" in key and num_responses != existing_checkpoint.get("num_responses", 0):
                    print(f"⚠️ Skipping {key} (response count changed)")
                    continue
                new_state_dict[key] = state_dict[key]
            
            model.load_state_dict(new_state_dict, strict=False)
            print("✅ Loaded existing model weights for fine-tuning")
            
            # Freeze backbone layers (fc1, fc2) to preserve learned features
            for name, param in model.named_parameters():
                if "fc1" in name or "fc2" in name or "ln1" in name or "ln2" in name:
                    param.requires_grad = False
                    print(f"🔒 Frozen layer: {name}")
            
            # Only unfreeze heads for new intents/responses
            for name, param in model.named_parameters():
                if "intent_head" in name or "response_head" in name:
                    param.requires_grad = True
                    print(f"🔓 Unfrozen layer: {name}")
                    
        except Exception as e:
            print(f"⚠️ Could not load existing weights: {e}")
            print("🔄 Training from scratch instead")
    
    intent_criterion = nn.CrossEntropyLoss(ignore_index=-1)  # Ignore -1 for response loss
    response_criterion = nn.CrossEntropyLoss(ignore_index=-1)  # Ignore -1 for intent loss
    
    # Use lower learning rate for fine-tuning
    learning_rate = 0.0005 if (fine_tune and existing_checkpoint) else 0.003
    optimizer = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=learning_rate, weight_decay=1e-4)

    epochs = 50 if (fine_tune and existing_checkpoint) else 200  # Fewer epochs for fine-tuning
    model.train()
    print(f"⏳ Training JeanMax Multi-Task Neural Model ({'Fine-tuning' if (fine_tune and existing_checkpoint) else 'Full training'} mode)...")
    print(f"   Epochs: {epochs}, Learning Rate: {learning_rate}")

    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        intent_correct = 0
        response_correct = 0
        total = 0

        for batch_x, batch_y_intent, batch_y_response in dataloader:
            batch_x, batch_y_intent, batch_y_response = batch_x.to(device), batch_y_intent.to(device), batch_y_response.to(device)

            optimizer.zero_grad()
            intent_logits, response_logits = model(batch_x)
            
            # Multi-task loss
            intent_loss = intent_criterion(intent_logits, batch_y_intent)
            response_loss = response_criterion(response_logits, batch_y_response)
            loss = intent_loss + 0.5 * response_loss  # Weight response loss lower
            
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * batch_x.size(0)
            
            # Intent accuracy (only for valid intent labels)
            valid_intent_mask = batch_y_intent != -1
            if valid_intent_mask.any():
                _, predicted_intent = torch.max(intent_logits[valid_intent_mask], 1)
                intent_correct += (predicted_intent == batch_y_intent[valid_intent_mask]).sum().item()
            
            # Response accuracy (only for valid response labels)
            valid_response_mask = batch_y_response != -1
            if valid_response_mask.any():
                _, predicted_response = torch.max(response_logits[valid_response_mask], 1)
                response_correct += (predicted_response == batch_y_response[valid_response_mask]).sum().item()
            
            total += batch_x.size(0)

        intent_acc = (intent_correct / total) * 100.0 if total > 0 else 0.0
        response_acc = (response_correct / total) * 100.0 if total > 0 else 0.0
        # Print more frequently for fine-tuning (every 10 epochs), less for full training (every 40)
        print_interval = 10 if (fine_tune and existing_checkpoint) else 40
        if epoch % print_interval == 0 or epoch == epochs:
            print(f"  Epoch [{epoch}/{epochs}] - Loss: {total_loss/total:.4f} - Intent Acc: {intent_acc:.2f}% - Response Acc: {response_acc:.2f}%")

    print("✅ Multi-Task Training completed!")

    # ---------------------------------------------------------
    # 6. Save PyTorch Model Checkpoint (JeanMax.pt with conversational support)
    # ---------------------------------------------------------
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "vectorizer_vocab": vectorizer.vocab,
        "vectorizer_idf": vectorizer.idf,
        "intent_map": INTENT_MAP,
        "intent_to_id": INTENT_TO_ID,
        "response_map": RESPONSE_MAP,
        "response_to_id": RESPONSE_TO_ID,
        "input_dim": input_dim,
        "num_intents": num_intents,
        "num_responses": num_responses
    }

    output_path_jean = os.path.join(model_dir, "JeanMax.pt")

    torch.save(checkpoint, output_path_jean)

    print(f"📦 Multi-Task Model saved successfully to: {output_path_jean}")

    # Validation Test
    model.eval()
    test_phrases = [
        "open chrome", 
        "hello jean", 
        "how are you", 
        "give me system status",
        "where is my phone",
        "start tracking",
        "stop tracking",
        "tracking status"
    ]
    print("\n🔍 Running Quick Inference Validation:")
    for phrase in test_phrases:
        vec = vectorizer.transform(phrase)
        inp = torch.tensor(vec, dtype=torch.float32).unsqueeze(0).to(device)
        with torch.no_grad():
            intent_logits, response_logits = model(inp)
            intent_probs = torch.softmax(intent_logits, dim=1)
            response_probs = torch.softmax(response_logits, dim=1)
            
            intent_confidence, intent_pred = torch.max(intent_probs, 1)
            response_confidence, response_pred = torch.max(response_probs, 1)
            
            intent = INTENT_MAP[intent_pred.item()]
            response = RESPONSE_MAP[response_pred.item()] if response_confidence.item() > 0.3 else "N/A"
            
            print(f"  Phrase: '{phrase}' -> Intent: {intent} (Conf: {intent_confidence.item()*100:.1f}%) | Response: {response[:50]}... (Conf: {response_confidence.item()*100:.1f}%)")

if __name__ == "__main__":
    train_model()
