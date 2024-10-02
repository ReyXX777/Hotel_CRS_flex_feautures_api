from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from models import Room

def recommend_rooms(user_preferences):
    rooms = Room.query.all()
    descriptions = [f"{room.room_type} {room.price}" for room in rooms]
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(descriptions)
    
    nn = NearestNeighbors(n_neighbors=5, metric='cosine')
    nn.fit(vectors)
    
    user_vector = vectorizer.transform([user_preferences])
    distances, indices = nn.kneighbors(user_vector)
    
    recommendations = [rooms[i] for i in indices.flatten()]
    return recommendations
