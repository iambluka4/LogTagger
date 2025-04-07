/**
 * Форматує часову мітку ISO до локалізованого рядка дати та часу
 * @param {string} timestamp - Часова мітка ISO
 * @param {object} options - Опції для форматування (див. Intl.DateTimeFormat)
 * @returns {string} Локалізований рядок дати та часу
 */
export const formatTimestamp = (timestamp, options = {}) => {
  if (!timestamp) return 'N/A';
  
  try {
    const date = new Date(timestamp);
    
    // Перевірка на валідність дати
    if (isNaN(date.getTime())) {
      console.error('Invalid timestamp:', timestamp);
      return timestamp;
    }
    
    // За замовчуванням відображати дату і час у локальному форматі
    const defaultOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    };
    
    const formatter = new Intl.DateTimeFormat(
      navigator.language || 'en-US', 
      { ...defaultOptions, ...options }
    );
    
    return formatter.format(date);
  } catch (e) {
    console.error('Error formatting timestamp:', e);
    return timestamp;
  }
};

/**
 * Перевіряє, чи є рядок пустим або містить лише пробіли
 * @param {string} str - Рядок для перевірки
 * @returns {boolean} true, якщо рядок пустий або містить лише пробіли
 */
export const isEmptyString = (str) => {
  return typeof str !== 'string' || str.trim() === '';
};

/**
 * Генерує CSS-класи залежно від умов
 * @param {object} classMap - Об'єкт, де ключі - назви класів, а значення - булеві умови
 * @returns {string} Рядок з CSS-класами
 */
export const classNames = (classMap) => {
  return Object.entries(classMap)
    .filter(([_, condition]) => Boolean(condition))
    .map(([className]) => className)
    .join(' ');
};
