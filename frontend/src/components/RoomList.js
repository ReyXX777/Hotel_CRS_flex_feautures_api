import React, { useEffect, useState } from 'react';
import RoomCard from './RoomCard';
import api from '../services/api';

const RoomList = () => {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch room data from the API
  useEffect(() => {
    const fetchRooms = async () => {
      try {
        const response = await api.get('/rooms');
        setRooms(response.data);
      } catch (err) {
        setError('Failed to fetch rooms. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    fetchRooms();
  }, []);

  // Handle room actions (booking/releasing)
  const handleRoomAction = async (action, roomId) => {
    try {
      const endpoint = `/rooms/${roomId}/${action === 'book' ? 'book' : 'release'}`;
      await api.post(endpoint);
      setRooms((prevRooms) =>
        prevRooms.map((room) =>
          room.id === roomId ? { ...room, available: action !== 'book' } : room
        )
      );
    } catch (err) {
      alert(`Failed to ${action} the room. Please try again.`);
    }
  };

  // Render content
  if (loading) return <p>Loading rooms...</p>;
  if (error) return <p className="error">{error}</p>;
  if (rooms.length === 0) return <p>No rooms available at the moment.</p>;

  return (
    <div className="room-list">
      {rooms.map((room) => (
        <RoomCard
          key={room.id}
          room={room}
          onAction={handleRoomAction}
        />
      ))}
    </div>
  );
};

export default RoomList;
