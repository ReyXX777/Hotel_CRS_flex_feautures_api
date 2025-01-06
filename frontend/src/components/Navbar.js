import React from 'react';

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h1>Hotel Booking</h1>
      </div>
      <ul className="navbar-menu">
        <li><a href="#home">Home</a></li>
        <li><a href="#rooms">Rooms</a></li>
        <li><a href="#about">About Us</a></li>
        <li><a href="#contact">Contact</a></li>
      </ul>
    </nav>
  );
};

export default Navbar;
