import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie } from 'recharts';
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

const CATEGORY_NAMES: Record<string, string> = {
  party: '🎉 Праздники',
  masterclass: '🎨 Мастер-классы',
  face_painting: '🎭 Аквагрим',
  cafe: '☕ Кафе',
  toys: '🧸 Игрушки',
  entrance: '🎟️ Гости (входные билеты)',
};

export const ClubsComparison = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [period, setPeriod] = useState<'today' |'current_month' | 'month' | 'week' | 'custom'>('today');
  const [customDate, setCustomDate] = useState<string>(formatDate(new Date()));
  const [periodLabel, setPeriodLabel] = useState<string>('');
  const [lastUpdate, setLastUpdate] = useState<string>('');

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

    axios.get(`${API_URL}/api/orders/clubs_comparison/?start_date=${startDate}&end_date=${endDate}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
      .then(response => {
        if (Array.isArray(response.data)) {
          setData(response.data);
        } else if (response.data.clubs) {
          setData(response.data.clubs);
        } else {
          setData([]);
        }
        setLoading(false);
        setLastUpdate(new Date().toLocaleTimeString('ru-RU'));
      })
      .catch(error => {
        console.error('❌ Ошибка:', error);
        setError('Ошибка загрузки данных');
        setLoading(false);
      });
  };

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

  if (loading) return <div className="p-6 text-center text-xl">Загрузка...</div>;
  if (error) return <div className="p-6 text-center text-red-500 text-xl">{error}</div>;
  if (data.length === 0) return <div className="p-6 text-center text-gray-500 text-xl">Нет данных</div>;

  const maxRevenue = Math.max(...data.map((club: any) => club.total_revenue));

  const chartData = data.map((club: any) => ({
    name: club.club_name,
    Праздники: club.categories?.party || 0,
    'Мастер-классы': club.categories?.masterclass || 0,
    Аквагрим: club.categories?.face_painting || 0,
    Кафе: club.categories?.cafe || 0,
    Игрушки: club.categories?.toys || 0,
    Гости: club.categories?.entrance || 0,
  }));

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Заголовок */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">📊 Сравнение клубов</h1>
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
            <a href="/dashboard" className="text-blue-600 hover:text-blue-800 py-2">← На главную</a>
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
            className={ ` px-4 py-2 rounded-lg ${period === 'current_month' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'} `}
          >
            📆 Текущий месяц
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

        {/* Общая таблица */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden mb-6">
          <div className="px-6 py-4 bg-gray-50 border-b">
            <h2 className="text-lg font-semibold text-gray-700">Общие показатели</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Клуб</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Выручка</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Наличные</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Безнал</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">QR-код</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Гости</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.map((club: any, index: number) => (
                  <tr key={index} className={club.total_revenue === maxRevenue ? 'bg-green-50' : ''}>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {club.club_name} {club.total_revenue === maxRevenue && '🏆'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 text-right font-bold">{formatCurrency(club.total_revenue)}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 text-right">{formatCurrency(club.cash)}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 text-right">{formatCurrency(club.card)}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 text-right">{formatCurrency(club.qr)}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 text-right">{club.total_guests}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Детализация по категориям */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden mb-6">
          <div className="px-6 py-4 bg-gray-50 border-b">
            <h2 className="text-lg font-semibold text-gray-700">📋 Детализация по категориям</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Категория</th>
                  {data.map((club: any, index: number) => (
                    <th key={index} className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      {club.club_name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.keys(CATEGORY_NAMES).map((catKey) => (
                  <tr key={catKey} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">{CATEGORY_NAMES[catKey]}</td>
                    {data.map((club: any, index: number) => {
                      const count = club.categories_count?.[catKey] || 0;
                      const total = club.categories?.[catKey] || 0;
                      return (
                        <td key={index} className="px-6 py-4 text-sm text-gray-900 text-right">
                          {count} шт. / {formatCurrency(total)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* График сравнения */}
        <div className="bg-white p-6 rounded-xl shadow-md mb-6">
          <h3 className="text-lg font-semibold mb-4">📊 Выручка по категориям (сравнение клубов)</h3>
          <div style={{ width: '100%', overflowX: 'auto' }}>
            <BarChart
              width={900}
              height={400}
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={(v) => `${v / 1000}K`} />
              <Tooltip formatter={(v) => formatCurrency(Number(v))} />
              <Legend />
              <Bar dataKey="Праздники" fill="#3B82F6" />
              <Bar dataKey="Мастер-классы" fill="#10B981" />
              <Bar dataKey="Аквагрим" fill="#8B5CF6" />
              <Bar dataKey="Кафе" fill="#F59E0B" />
              <Bar dataKey="Игрушки" fill="#EC4899" />
              <Bar dataKey="Гости" fill="#06B6D4" />
            </BarChart>
          </div>
        </div>

        {/* Круговые диаграммы */}
        <div className="bg-white p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">💳 Способы оплаты по клубам</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {data.map((club: any, index: number) => {
              const clubPaymentData = [
                { name: 'Наличные', value: Number(club.cash) || 0, fill: '#3B82F6' },
                { name: 'Безнал', value: Number(club.card) || 0, fill: '#10B981' },
                { name: 'QR-код', value: Number(club.qr) || 0, fill: '#8B5CF6' },
              ].filter(item => item.value > 0);

              return (
                <div key={index} className="bg-gray-50 rounded-xl p-4">
                  <h4 className="font-semibold text-center mb-2">{club.club_name}</h4>
                  <PieChart width={250} height={200}>
                    <Pie
                      data={clubPaymentData}
                      cx="50%"
                      cy="50%"
                      outerRadius={60}
                      dataKey="value"
                      label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                    />
                    <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                  </PieChart>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};