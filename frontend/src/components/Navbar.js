import React from 'react';
import { Link } from 'react-router-dom'; // Added React Router for navigation
import './Navbar.css'; // Added CSS for styling

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h1>Hotel Booking</h1>
      </div>
      <ul className="navbar-menu">
        <li><Link to="/">Home</Link></li> {/* Replaced anchor tags with React Router Link */}
        <li><Link to="/rooms">Rooms</Link></li>
        <li><Link to="/about">About Us</Link></li>
        <li><Link to="/contact">Contact</Link></li>
      </ul>
      <div className="navbar-auth"> {/* Added authentication links */}
        <Link to="/login" className="auth-link">Login</Link>
        <Link to="/register" className="auth-link">Register</Link>
      </div>
    </nav>
  );
};

export default Navbar;
