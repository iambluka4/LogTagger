import React, { createContext, useContext } from 'react';

// Створюємо порожній контекст, який не робить перевірку аутентифікації
export const AuthContext = createContext({
  isAuthenticated: true, // Завжди аутентифікований
  user: { role: 'admin' },  // Додаємо фіктивні дані користувача
  login: () => {},
  logout: () => {},
});

export const AuthProvider = ({ children }) => {
  // Порожній провайдер, який завжди показує, що користувач аутентифікований
  const authValues = {
    isAuthenticated: true,
    user: { role: 'admin' },
    login: () => {},
    logout: () => {},
  };

  return (
    <AuthContext.Provider value={authValues}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

// Замінюємо будь-яку функцію захисту маршрутів на таку, що завжди дозволяє доступ
export const ProtectedRoute = ({ children }) => {
  return children;
};
