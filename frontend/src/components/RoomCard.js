import React from 'react';

const RoomCard = ({ room }) => {
  return (
    <div>
      <h2>{room.room_type}</h2>
      <p>Price: {room.price}</p>
      <p>{room.available ? 'Available' : 'Booked'}</p>
    </div>
  );
};

export default RoomCard;
