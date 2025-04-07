import React from 'react';
import { Navigate } from 'react-router-dom';

// Порожній компонент, який завжди перенаправляє на головну
function Login() {
  return <Navigate to="/" replace />;
}

export default Login;
