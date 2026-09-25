import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie } from 'recharts';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(value);
};

const formatDate = (d: Date) => {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<'today' |'current_month' | 'month' | 'week' | 'custom'>('today');
  const [customDate, setCustomDate] = useState<string>(formatDate(new Date()));
  const [periodLabel, setPeriodLabel] = useState<string>('');
  const [lastUpdate, setLastUpdate] = useState<string>('');

  // Функция загрузки данных
  const fetchData = () => {
    const token = localStorage.getItem('access_token');
    let startDate = '';
    let endDate = '';
    const today = new Date();

    if (period === 'today') {
      startDate = endDate = formatDate(today);
    } else if (period === 'current_month') {
      const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
      startDate = formatDate(firstDay);
      endDate = formatDate(today);
    } else if (period === 'month') {
      const firstDay = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      const lastDay = new Date(today.getFullYear(), today.getMonth(), 0);
      startDate = formatDate(firstDay);
      endDate = formatDate(lastDay);
    } else if (period === 'week') {
      const dayOfWeek = today.getDay() || 7;
      const lastMonday = new Date(today);
      lastMonday.setDate(today.getDate() - dayOfWeek - 6);
      const lastSunday = new Date(lastMonday);
      lastSunday.setDate(lastMonday.getDate() + 6);
      startDate = formatDate(lastMonday);
      endDate = formatDate(lastSunday);
    } else if (period === 'custom') {
      startDate = endDate = customDate;
    }

    setPeriodLabel(startDate === endDate ? startDate : `${startDate} — ${endDate}`);

    axios.get(`${API_URL}/api/orders/dashboard_summary/?start_date=${startDate}&end_date=${endDate}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
      .then(response => {
        setData(response.data);
        setLoading(false);
        setLastUpdate(new Date().toLocaleTimeString('ru-RU'));
      })
      .catch(error => {
        console.error('❌ Ошибка:', error);
        setLoading(false);
      });
  };

  // Первая загрузка + при смене периода
  useEffect(() => {
    setLoading(true);
    fetchData();
  }, [period, customDate]);

  // Автообновление каждые 5 секунд (только если период = "Сегодня" и "Текущий месяц")
  useEffect(() => {
    if (period !== 'today' && period !== 'current_month') return;

    const interval = setInterval(() => {
      fetchData();
    }, 5000);

    return () => clearInterval(interval);
  }, [period, customDate]);

  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/login';
  };

  const handleZReport = async () => {
    const date = prompt('Введите дату в формате ГГГГ-ММ-ДД:', formatDate(new Date()));
    if (!date) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${API_URL}/api/orders/export_z_report/?date=${date}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob',
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `z_report_${date}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('❌ Ошибка скачивания:', error);
      alert('Ошибка скачивания Z-отчёта.');
    }
  };

  if (loading) return <div className="p-6 text-center text-xl">Загрузка...</div>;
  if (!data || !data.kpi) return <div className="p-6 text-center text-gray-500 text-xl">Нет данных</div>;

  // Для графика сокращаем "Гости (входные билеты)" → "Гости"
  const categoryData = data.categories
    ? Object.values(data.categories).map((cat: any) => ({
        name: cat.name === 'Гости (входные билеты)' ? 'Гости' : cat.name,
        total: Number(cat.total) || 0,
        count: Number(cat.count) || 0,
      }))
    : [];

  const paymentData = [
    { name: 'Наличные', value: Number(data.kpi.cash) || 0, fill: '#3B82F6' },
    { name: 'Безнал', value: Number(data.kpi.card) || 0, fill: '#10B981' },
    { name: 'QR-код', value: Number(data.kpi.qr) || 0, fill: '#8B5CF6' },
  ].filter(item => item.value > 0);

  const username = localStorage.getItem('username') || '';
  const allowedUsers = ['admin', 'boss_1', 'boss_2', 'boss_3'];
  const canSeeComparison = allowedUsers.includes(username);

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Верхняя панель */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">🏠 Дашборд</h1>
            {lastUpdate && (
              <p className="text-xs text-gray-400 mt-1">
                Обновлено: {lastUpdate} (автообновление каждые 5 сек)
              </p>
            )}
          </div>
          <div className="flex gap-3">
            <button onClick={() => fetchData()} className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300">
              🔄 Обновить
            </button>
            <button onClick={handleZReport} className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">
              📥 Z-отчёт
            </button>
            {canSeeComparison && (
              <a href="/comparison" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">📊 Сравнить</a>
            )}
            <button onClick={handleLogout} className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700">🚪 Выйти</button>
          </div>
        </div>

        {/* Фильтр по датам */}
        <div className="flex flex-wrap gap-2 mb-4">
          <button
            onClick={() => setPeriod('today')}
            className={`px-4 py-2 rounded-lg ${period === 'today' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
          >
            📅 Сегодня
          </button>
          <button
            onClick={() => setPeriod('current_month')}
            className={` px-4 py-2 rounded-lg ${period === 'current_month' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'} ` }
          >
            📅 Текущий месяц
          </button>
          <button
            onClick={() => setPeriod('month')}
            className={`px-4 py-2 rounded-lg ${period === 'month' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
          >
            📆 Прошлый месяц
          </button>
          <button
            onClick={() => setPeriod('week')}
            className={`px-4 py-2 rounded-lg ${period === 'week' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
          >
            📅 Прошлая неделя
          </button>
          <button
            onClick={() => {
              const date = prompt('Введите дату в формате ГГГГ-ММ-ДД:', formatDate(new Date()));
              if (date) {
                setCustomDate(date);
                setPeriod('custom');
              }
            }}
            className={`px-4 py-2 rounded-lg ${period === 'custom' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
          >
            🔍 Выбрать дату
          </button>
        </div>

        {/* Период */}
        {periodLabel && (
          <div className="text-sm text-gray-500 mb-4">
            Период: <span className="font-medium">{periodLabel}</span>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-blue-500">
            <p className="text-sm text-gray-500">Выручка</p>
            <p className="text-2xl font-bold">{formatCurrency(Number(data.kpi.total_revenue) || 0)}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-green-500">
            <p className="text-sm text-gray-500">Продаж</p>
            <p className="text-2xl font-bold">{data.kpi.total_orders || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-purple-500">
            <p className="text-sm text-gray-500">Гости (входные билеты)</p>
            <p className="text-2xl font-bold">{data.kpi.total_guests || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-orange-500">
            <p className="text-sm text-gray-500">Ср. чек</p>
            <p className="text-2xl font-bold">{formatCurrency(Number(data.kpi.avg_check) || 0)}</p>
          </div>
        </div>

        {/* Графики */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white p-6 rounded-xl shadow-md">
            <h3 className="text-lg font-semibold mb-4">📊 Выручка по категориям</h3>
            <div style={{ width: '100%', overflowX: 'auto' }}>
              <BarChart
                width={550}
                height={350}
                data={categoryData}
                margin={{ top: 10, right: 10, left: 0, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  interval={0}
                  height={80}
                  tick={{ fontSize: 14, fill: '#1F2937', fontWeight: 600 }}
                />
                <YAxis tickFormatter={(v) => `${v / 1000}K`}
                tick={{ fontSize: 14, fill: '#1F2937', fontWeight: 600}} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="total" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md">
            <h3 className="text-lg font-semibold mb-4">💳 Способы оплаты</h3>
            <div style={{ width: '100%', overflowX: 'auto' }}>
              <PieChart width={500} height={350}>
                <Pie
                  data={paymentData}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  dataKey="value"
                />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
              </PieChart>
            </div>
          </div>
        </div>

        {/* Таблица детализации */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b">
            <h3 className="text-lg font-semibold text-gray-700">📋 Детализация по категориям</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Категория</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Кол-во</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Выручка</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {categoryData.map((cat: any) => (
                  <tr key={cat.name} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">{cat.name}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 text-right">{cat.count} шт.</td>
                    <td className="px-6 py-4 text-sm text-gray-900 text-right font-medium">
                      {formatCurrency(Number(cat.total) || 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};