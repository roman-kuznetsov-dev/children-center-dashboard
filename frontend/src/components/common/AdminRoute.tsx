import React from 'react';
import { Navigate } from 'react-router-dom';

interface AdminRouteProps {
  children: React.ReactNode;
}

export const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
  const token = localStorage.getItem('access_token');
  const username = localStorage.getItem('username') || '';

  // Если нет токена — отправляем на страницу входа
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Список пользователей, которым разрешена страница сравнения
  const allowedUsers = ['admin', 'boss_1', 'boss_2', 'boss_3'];
  const isAllowed = allowedUsers.includes(username);

  // Если не админ — отправляем на дашборд
  if (!isAllowed) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};