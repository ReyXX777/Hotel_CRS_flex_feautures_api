import React from 'react';
import PropTypes from 'prop-types';
import './RoomCard.css'; // Import external CSS for styling

const RoomCard = ({ room, onAction }) => {
  const handleAction = () => {
    if (room.available) {
      onAction('book', room.id); // Call the booking action
    } else {
      onAction('release', room.id); // Call the release action
    }
  };

  return (
    <div className="room-card">
      <h2 className="room-type">{room.room_type}</h2>
      <p className="room-price">Price: ${room.price.toFixed(2)}</p>
      <p className={`room-status ${room.available ? 'available' : 'booked'}`}>
        {room.available ? 'Available' : 'Booked'}
      </p>
      <button
        className="room-action-btn"
        onClick={handleAction}
        disabled={!room.available && room.status === 'booked'}
      >
        {room.available ? 'Book Now' : 'Release Room'}
      </button>
    </div>
  );
};

RoomCard.propTypes = {
  room: PropTypes.shape({
    id: PropTypes.number.isRequired,
    room_type: PropTypes.string.isRequired,
    price: PropTypes.number.isRequired,
    available: PropTypes.bool.isRequired,
  }).isRequired,
  onAction: PropTypes.func.isRequired, // Function to handle booking/releasing actions
};

export default RoomCard;
