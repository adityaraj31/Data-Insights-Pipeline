import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { 
  LayoutDashboard, TrendingUp, Users, PieChart as PieChartIcon, 
  Map, DollarSign, Activity, AlertCircle 
} from 'lucide-react';
import './index.css';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

const COLORS = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

function App() {
  const [data, setData] = useState({
    revenue: [],
    customers: [],
    categories: [],
    regions: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'total_spend', direction: 'desc' });
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch all data in parallel
        const [revRes, custRes, catRes, regRes] = await Promise.all([
          fetch(`${API_BASE_URL}/revenue`),
          fetch(`${API_BASE_URL}/top-customers`),
          fetch(`${API_BASE_URL}/categories`),
          fetch(`${API_BASE_URL}/regions`)
        ]);

        if (!revRes.ok || !custRes.ok || !catRes.ok || !regRes.ok) {
          throw new Error('Failed to fetch data from one or more endpoints.');
        }

        const [revenue, customers, categories, regions] = await Promise.all([
          revRes.json(),
          custRes.json(),
          catRes.json(),
          regRes.json()
        ]);

        setData({ revenue, customers, categories, regions });
        
        if (revenue && revenue.length > 0) {
          const sortedDates = [...revenue].sort((a,b) => a.order_year_month.localeCompare(b.order_year_month));
          setDateRange({
            start: sortedDates[0].order_year_month,
            end: sortedDates[sortedDates.length - 1].order_year_month
          });
        }
        
        setError(null);
      } catch (err) {
        setError(err.message || 'An unexpected error occurred while fetching data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Format currency
  const formatCurrency = (value) => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);

  // Sorting logic for table
  const requestSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedCustomers = [...data.customers].sort((a, b) => {
    if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
    if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  const filteredCustomers = sortedCustomers.filter(cust => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (cust.name && cust.name.toLowerCase().includes(term)) ||
      (cust.region && cust.region.toLowerCase().includes(term))
    );
  });

  const filteredRevenue = data.revenue.filter(item => {
    if (!dateRange.start || !dateRange.end) return true;
    return item.order_year_month >= dateRange.start && item.order_year_month <= dateRange.end;
  });

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <h2>Loading Insights...</h2>
        <p>Crunching the latest data from the backend.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-state">
        <AlertCircle size={48} style={{ marginBottom: '1rem' }} />
        <h2>Data Retrieval Failed</h2>
        <p>{error}</p>
        <p style={{ marginTop: '1rem', fontSize: '0.875rem' }}>
          Ensure the FastAPI backend is running on http://127.0.0.1:8000
        </p>
      </div>
    );
  }

  // Calculate high-level KPIs
  const totalRevenue = data.revenue.reduce((sum, item) => sum + item.total_revenue, 0);
  const totalCustomers = data.regions.reduce((sum, item) => sum + item.customer_count, 0);
  const totalOrders = data.regions.reduce((sum, item) => sum + item.order_count, 0);

  return (
    <div className="dashboard-container">
      <header>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <LayoutDashboard size={32} color="#6366F1" />
          Data Insights Pipeline
        </h1>
        <p style={{ color: 'var(--text-muted)' }}>Interactive Business Dashboard</p>
      </header>

      {/* Top Level KPIs */}
      <div className="kpi-grid" style={{ marginBottom: '2rem' }}>
        <div className="card kpi-card" style={{ borderLeft: '4px solid #4F46E5' }}>
          <div className="kpi-title"><DollarSign size={16} style={{display:'inline', verticalAlign:'text-bottom'}}/> Total Revenue</div>
          <div className="kpi-value">{formatCurrency(totalRevenue)}</div>
          <div className="kpi-sub">Lifetime completed orders</div>
        </div>
        <div className="card kpi-card" style={{ borderLeft: '4px solid #10B981' }}>
          <div className="kpi-title"><Users size={16} style={{display:'inline', verticalAlign:'text-bottom'}}/> Total Customers</div>
          <div className="kpi-value">{totalCustomers}</div>
          <div className="kpi-sub">Across all regions</div>
        </div>
        <div className="card kpi-card" style={{ borderLeft: '4px solid #F59E0B' }}>
          <div className="kpi-title"><Activity size={16} style={{display:'inline', verticalAlign:'text-bottom'}}/> Total Orders</div>
          <div className="kpi-value">{totalOrders}</div>
          <div className="kpi-sub">Successfully fulfilled</div>
        </div>
      </div>

      <div className="dashboard-grid">
        
        {/* Revenue Trend (Line Chart) */}
        <div className="card full-width">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', marginBottom: '1.5rem', gap: '1rem' }}>
            <div className="card-title" style={{ marginBottom: 0 }}><TrendingUp size={20} /> Monthly Revenue Trend</div>
            <div className="date-filter" style={{ display: 'flex', alignItems: 'center' }}>
              <input 
                type="month" 
                value={dateRange.start} 
                onChange={(e) => setDateRange(prev => ({...prev, start: e.target.value}))}
                className="date-input"
              />
              <span style={{ margin: '0 0.5rem', color: 'var(--text-muted)' }}>to</span>
              <input 
                type="month" 
                value={dateRange.end} 
                onChange={(e) => setDateRange(prev => ({...prev, end: e.target.value}))}
                className="date-input"
              />
            </div>
          </div>
          <div style={{ height: 350, width: '100%' }}>
            <ResponsiveContainer>
              <LineChart data={filteredRevenue} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="order_year_month" stroke="#94A3B8" />
                <YAxis 
                  stroke="#94A3B8" 
                  tickFormatter={(value) => `$${value}`} 
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(value) => [formatCurrency(value), "Revenue"]}
                />
                <Line 
                  type="monotone" 
                  dataKey="total_revenue" 
                  stroke="#6366F1" 
                  strokeWidth={3}
                  dot={{ r: 4, strokeWidth: 2 }}
                  activeDot={{ r: 8 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Breakdown (Pie Chart) */}
        <div className="card">
          <div className="card-title"><PieChartIcon size={20} /> Revenue by Category</div>
          <div style={{ height: 300, width: '100%' }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={data.categories}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="total_revenue"
                  nameKey="category"
                  label={({category, percent}) => `${category} ${(percent * 100).toFixed(0)}%`}
                >
                  {data.categories.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(value) => formatCurrency(value)}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Regional Summary (Bar Chart) */}
        <div className="card">
          <div className="card-title"><Map size={20} /> Regional Contribution</div>
          <div style={{ height: 300, width: '100%' }}>
            <ResponsiveContainer>
              <BarChart data={data.regions} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="region" stroke="#94A3B8" />
                <YAxis 
                  stroke="#94A3B8" 
                  tickFormatter={(value) => `$${value}`} 
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(value) => [formatCurrency(value), "Revenue"]}
                />
                <Bar dataKey="total_revenue" radius={[4, 4, 0, 0]}>
                  {data.regions.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[(index+1) % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Customers Table */}
        <div className="card full-width">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', marginBottom: '1.5rem', gap: '1rem' }}>
            <div className="card-title" style={{ marginBottom: 0 }}><Users size={20} /> Top Customers by Spend</div>
            <div className="search-filter">
              <input 
                type="text" 
                placeholder="Search name or region..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="text-input"
              />
            </div>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th onClick={() => requestSort('name')}>Customer Name {sortConfig.key === 'name' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}</th>
                  <th onClick={() => requestSort('region')}>Region {sortConfig.key === 'region' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}</th>
                  <th onClick={() => requestSort('total_spend')}>Total Spend {sortConfig.key === 'total_spend' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}</th>
                  <th onClick={() => requestSort('churned')}>Status {sortConfig.key === 'churned' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}</th>
                </tr>
              </thead>
              <tbody>
                {filteredCustomers.length > 0 ? (
                  filteredCustomers.map((cust) => (
                    <tr key={cust.customer_id}>
                      <td style={{ fontWeight: 500 }}>{cust.name}</td>
                      <td>{cust.region}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: '1rem' }}>{formatCurrency(cust.total_spend)}</td>
                      <td>
                        <span className={`badge ${cust.churned ? 'churned' : 'active'}`}>
                          {cust.churned ? 'Churned Risk' : 'Active'}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" style={{ textAlign: 'center', padding: '2rem' }}>
                      No customers found matching "{searchTerm}"
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}

export default App;
