import React, { useEffect } from 'react';
import RoomList from './components/RoomList';
import Navbar from './components/Navbar';
import './App.css'; // Import CSS for global styling

function App() {
  useEffect(() => {
    document.title = 'Hotel Booking App'; // Set a meaningful document title
  }, []);

  return (
    <div className="app-container">
      <header>
        <Navbar />
      </header>
      <main>
        <RoomList />
      </main>
    </div>
  );
}

export default App;
