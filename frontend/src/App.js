import React, { useEffect } from 'react';
import RoomList from './components/RoomList';
import Navbar from './components/Navbar';
import Footer from './components/Footer'; // Added Footer component
import Notification from './components/Notification'; // Added Notification component
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
        <Notification message="Welcome to the Hotel Booking App!" /> {/* Added Notification */}
        <RoomList />
      </main>
      <footer>
        <Footer /> {/* Added Footer */}
      </footer>
    </div>
  );
}

export default App;
