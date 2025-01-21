# Commit: Added logging and input validation to recommend_rooms function

from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from models import Room
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def recommend_rooms(user_preferences):
    if not user_preferences or not isinstance(user_preferences, str):
        logging.error("Invalid user preferences provided.")
        return []

    try:
        rooms = Room.query.all()
        if not rooms:
            logging.warning("No rooms found in the database.")
            return []

        descriptions = [f"{room.room_type} {room.price}" for room in rooms]
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(descriptions)
        
        nn = NearestNeighbors(n_neighbors=5, metric='cosine')
        nn.fit(vectors)
        
        user_vector = vectorizer.transform([user_preferences])
        distances, indices = nn.kneighbors(user_vector)
        
        recommendations = [rooms[i] for i in indices.flatten()]
        logging.info(f"Generated {len(recommendations)} recommendations.")
        return recommendations

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return []
