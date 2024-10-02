import React, { useEffect, useState } from 'react';
import RoomCard from './RoomCard';
import api from '../services/api';

const RoomList = () => {
  const [rooms, setRooms] = useState([]);

  useEffect(() => {
    api.get('/rooms').then((response) => {
      setRooms(response.data);
    });
  }, []);

  return (
    <div>
      {rooms.map((room) => (
        <RoomCard key={room.room_number} room={room} />
      ))}
    </div>
  );
};

export default RoomList;
