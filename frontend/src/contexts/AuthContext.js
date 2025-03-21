import React, { createContext, useState, useEffect, useContext } from 'react';
import { 
  loginUser as loginUserService, 
  logoutUser as logoutUserService,
  getCurrentUser,
  initAuth,
  isAuthenticated as checkIsAuthenticated,
  isAdmin as checkIsAdmin,
  isAnalyst as checkIsAnalyst
} from '../services/auth';

// Create auth context
const AuthContext = createContext();

// Auth provider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize authentication on component mount
  useEffect(() => {
    const initializeAuth = () => {
      setLoading(true);
      try {
        if (initAuth()) {
          setUser(getCurrentUser());
        }
      } catch (err) {
        console.error('Authentication initialization error:', err);
        setError('Failed to initialize authentication');
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  // Login handler
  const loginUser = async (username, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await loginUserService(username, password);
      setUser(response.user);
      return response;
    } catch (err) {
      setError(err.message || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Logout handler
  const logoutUser = () => {
    logoutUserService();
    setUser(null);
  };

  // Check if user is authenticated
  const isAuthenticated = () => {
    return checkIsAuthenticated();
  };

  // Check if user is admin
  const isAdmin = () => {
    return checkIsAdmin();
  };

  // Check if user is analyst
  const isAnalyst = () => {
    return checkIsAnalyst();
  };

  // Context value
  const contextValue = {
    user,
    loading,
    error,
    loginUser,
    logoutUser,
    isAuthenticated,
    isAdmin,
    isAnalyst
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
