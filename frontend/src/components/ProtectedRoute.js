import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function ProtectedRoute({ children, requiredRole = null }) {
  const { isAuthenticated, isAdmin, isAnalyst, loading } = useAuth();
  const location = useLocation();
  
  // Show loading state if authentication is still initializing
  if (loading) {
    return <div className="loading-container">Loading...</div>;
  }
  
  // Check if user is authenticated
  if (!isAuthenticated()) {
    // Redirect to login page, but save the attempted URL
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  // Check role requirements if specified
  if (requiredRole) {
    if (requiredRole === 'admin' && !isAdmin()) {
      return <Navigate to="/unauthorized" replace />;
    }
    
    if (requiredRole === 'analyst' && !isAnalyst()) {
      return <Navigate to="/unauthorized" replace />;
    }
  }
  
  // If authenticated and has required role, render the protected content
  return children;
}

export default ProtectedRoute;
