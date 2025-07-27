import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white shadow-sm border-b border-secondary-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">S</span>
            </div>
            <span className="text-xl font-bold text-secondary-900">StatEdge</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            {user && (
              <>
                <Link 
                  to="/" 
                  className="text-secondary-600 hover:text-secondary-900 font-medium transition-colors"
                >
                  Dashboard
                </Link>
                <Link 
                  to="/analytics" 
                  className="text-secondary-600 hover:text-secondary-900 font-medium transition-colors"
                >
                  Analytics
                </Link>
                <Link 
                  to="/ai-chat" 
                  className="text-secondary-600 hover:text-secondary-900 font-medium transition-colors"
                >
                  AI Chat
                </Link>
              </>
            )}
          </nav>

          {/* User section */}
          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-secondary-600">
                    {user.email}
                  </span>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    user.tier === 'premium' 
                      ? 'bg-yellow-100 text-yellow-800' 
                      : user.tier === 'basic'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-secondary-100 text-secondary-800'
                  }`}>
                    {user.tier.toUpperCase()}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="btn-secondary text-sm"
                >
                  Logout
                </button>
              </>
            ) : (
              <div className="flex items-center space-x-2">
                <Link to="/login" className="btn-secondary text-sm">
                  Login
                </Link>
                <Link to="/register" className="btn-primary text-sm">
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;