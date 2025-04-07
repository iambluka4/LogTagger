import React, { createContext, useState, useContext, useEffect } from 'react';

// Створюємо контекст для керування демо-режимом
const DemoModeContext = createContext();

export const useDemoMode = () => useContext(DemoModeContext);

export const DemoModeProvider = ({ children }) => {
  const [demoModeEnabled, setDemoModeEnabled] = useState(false);
  
  // Завантажуємо стан демо-режиму при ініціалізації
  useEffect(() => {
    // Спочатку перевіряємо локальне сховище
    const storedValue = localStorage.getItem('demoModeEnabled');
    if (storedValue !== null) {
      setDemoModeEnabled(storedValue === 'true');
    }
  }, []);
  
  // Функція для оновлення стану демо-режиму
  const updateDemoMode = (isEnabled) => {
    setDemoModeEnabled(isEnabled);
    // Зберігаємо стан у локальному сховищі
    localStorage.setItem('demoModeEnabled', isEnabled.toString());
    return true;
  };
  
  return (
    <DemoModeContext.Provider value={{ demoModeEnabled, updateDemoMode }}>
      {children}
    </DemoModeContext.Provider>
  );
};
