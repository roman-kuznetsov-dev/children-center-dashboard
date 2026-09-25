import { apiClient } from './client';

export const salesAPI = {
  // Получить данные для главной страницы
  getDashboardSummary: async () => {
    const response = await apiClient.get('/orders/dashboard_summary/');
    return response.data;
  },

  // Получить сравнительную таблицу клубов
  getClubsComparison: async () => {
    const response = await apiClient.get('/orders/clubs_comparison/');
    return response.data;
  },

  // Вход в систему
  login: async (username: string, password: string) => {
    const response = await apiClient.post('/token/', { username, password });
    return response.data;
  },
};