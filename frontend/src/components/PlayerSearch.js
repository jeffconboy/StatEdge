import React, { useState, useEffect, useRef } from 'react';
import { playerAPI, handleAPIError } from '../utils/api';

const PlayerSearch = ({ onPlayerSelect, placeholder = "Search for players..." }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [error, setError] = useState(null);
  
  const searchRef = useRef(null);
  const debounceRef = useRef(null);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (query.length >= 2) {
      debounceRef.current = setTimeout(() => {
        performSearch(query);
      }, 300);
    } else {
      setResults([]);
      setShowResults(false);
    }

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query]);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const performSearch = async (searchQuery) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await playerAPI.search(searchQuery, 8);
      setResults(response.data || []);
      setShowResults(true);
    } catch (error) {
      setError(handleAPIError(error));
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayerClick = (player) => {
    setQuery(player.name);
    setShowResults(false);
    if (onPlayerSelect) {
      onPlayerSelect(player);
    }
  };

  const handleInputChange = (e) => {
    setQuery(e.target.value);
    if (e.target.value.length < 2) {
      setShowResults(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setShowResults(false);
    }
  };

  return (
    <div className="relative" ref={searchRef}>
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= 2 && setShowResults(true)}
          placeholder={placeholder}
          className="input-primary w-full pl-10 pr-4"
        />
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg className="h-5 w-5 text-secondary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        {loading && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
          </div>
        )}
      </div>

      {/* Search Results Dropdown */}
      {showResults && (
        <div className="absolute z-10 mt-1 w-full bg-white rounded-lg shadow-lg border border-secondary-200 max-h-96 overflow-y-auto">
          {error ? (
            <div className="p-4 text-red-600 text-sm">
              {error}
            </div>
          ) : results.length > 0 ? (
            <>
              {results.map((player) => (
                <button
                  key={player.id}
                  onClick={() => handlePlayerClick(player)}
                  className="w-full text-left px-4 py-3 hover:bg-secondary-50 border-b border-secondary-100 last:border-b-0 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-secondary-900">
                        {player.name}
                      </div>
                      <div className="text-sm text-secondary-600">
                        {player.team} • {player.position}
                      </div>
                    </div>
                    <div className="text-xs text-secondary-500">
                      {player.active ? 'Active' : 'Inactive'}
                    </div>
                  </div>
                </button>
              ))}
            </>
          ) : query.length >= 2 && !loading ? (
            <div className="p-4 text-secondary-600 text-sm text-center">
              No players found for "{query}"
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};

export default PlayerSearch;