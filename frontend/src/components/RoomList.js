import React, { useEffect, useState } from 'react';
import RoomCard from './RoomCard';
import api from '../services/api';
import './RoomList.css'; // Added CSS for styling

const RoomList = () => {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // Added filter state
  const [sortBy, setSortBy] = useState('price'); // Added sorting state
  const [searchQuery, setSearchQuery] = useState(''); // Added search query state

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

  // Handle filter change
  const handleFilterChange = (e) => {
    setFilter(e.target.value);
  };

  // Handle sort change
  const handleSortChange = (e) => {
    setSortBy(e.target.value);
  };

  // Handle search query change
  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };

  // Filter rooms based on availability
  const filteredRooms = filter === 'available'
    ? rooms.filter((room) => room.available)
    : rooms;

  // Sort rooms based on selected criteria
  const sortedRooms = [...filteredRooms].sort((a, b) => {
    if (sortBy === 'price') return a.price - b.price;
    if (sortBy === 'rating') return (b.rating || 0) - (a.rating || 0);
    return 0;
  });

  // Search rooms based on query
  const searchedRooms = sortedRooms.filter((room) =>
    room.room_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Render content
  if (loading) return <p>Loading rooms...</p>;
  if (error) return <p className="error">{error}</p>;
  if (searchedRooms.length === 0) return <p>No rooms match your criteria.</p>;

  return (
    <div className="room-list">
      <div className="filter-controls"> {/* Added filter controls */}
        <label>
          Filter by:
          <select value={filter} onChange={handleFilterChange}>
            <option value="all">All Rooms</option>
            <option value="available">Available Rooms</option>
          </select>
        </label>
        <label>
          Sort by:
          <select value={sortBy} onChange={handleSortChange}>
            <option value="price">Price (Low to High)</option>
            <option value="rating">Rating (High to Low)</option>
          </select>
        </label>
        <input
          type="text"
          placeholder="Search by room type..."
          value={searchQuery}
          onChange={handleSearchChange}
        />
      </div>
      {searchedRooms.map((room) => (
        <RoomCard
          key={room.id}
          room={room}
          onAction={handleRoomAction}
          onDetails={(roomId) => alert(`Details for room ${roomId}`)} // Added details handler
        />
      ))}
    </div>
  );
};

export default RoomList;
