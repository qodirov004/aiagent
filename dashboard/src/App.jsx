import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import TeacherCabinet from './TeacherCabinet';
import {
  LayoutDashboard,
  Sparkles,
  FileText,
  TrendingUp,
  Users,
  GraduationCap,
  Calendar,
  CheckCircle2,
  Clock,
  AlertTriangle,
  RefreshCw,
  Send,
  PlusCircle,
  BarChart3,
  Search,
  BookOpen,
  DollarSign,
  Activity,
  Layers,
  Award,
  Sun,
  Moon,
  Share2,
  ExternalLink,
  MessageCircle,
  Camera
} from 'lucide-react';

const InstagramIcon = ({ size = 20, color = "currentColor" }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect width="20" height="20" x="2" y="2" rx="5" ry="5" />
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
    <line x1="17.5" x2="17.51" y1="6.5" y2="6.5" />
  </svg>
);

const API_BASE = 'http://127.0.0.1:8000/api/supervisor';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [apiOnline, setApiOnline] = useState(true);

  // Theme state: default dark or loaded from localStorage
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('educenter_theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('educenter_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  // States
  const [stats, setStats] = useState(null);
  const [summaries, setSummaries] = useState([]);
  const [selectedSummary, setSelectedSummary] = useState(null);
  const [reports, setReports] = useState([]);
  const [marketingList, setMarketingList] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [groups, setGroups] = useState([]);
  const [feedbacks, setFeedbacks] = useState([]);

  // Form states
  const [genDate, setGenDate] = useState(new Date().toISOString().split('T')[0]);
  const [generatingAi, setGeneratingAi] = useState(false);

  // Marketing form
  const [mDate, setMDate] = useState(new Date().toISOString().split('T')[0]);
  const [mLeads, setMLeads] = useState(0);
  const [mSpend, setMSpend] = useState(0);
  const [mNotes, setMNotes] = useState('');
  const [mGenerateAi, setMGenerateAi] = useState(true);
  const [savingMarketing, setSavingMarketing] = useState(false);
  const [selectedMarketing, setSelectedMarketing] = useState(null);
  const [analyzingMarketingDate, setAnalyzingMarketingDate] = useState('');
  const [marketingInstructions, setMarketingInstructions] = useState([]);

  // Instagram & Telegram Broadcast States
  const [instagramData, setInstagramData] = useState(null);
  const [syncingInstagram, setSyncingInstagram] = useState(false);
  const [sendingTelegram, setSendingTelegram] = useState(false);
  const [telegramSentInfo, setTelegramSentInfo] = useState(null);

  // Filter states
  const [reportDateFilter, setReportDateFilter] = useState('');
  const [searchTeacher, setSearchTeacher] = useState('');

  // Initial load
  useEffect(() => {
    fetchStats();
    fetchSummaries();
    fetchReports();
    fetchMarketing();
    fetchMarketingInstructions();
    fetchInstagram();
    fetchTeachers();
    fetchGroups();
    fetchFeedbacks();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats/`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
        setApiOnline(true);
      } else {
        setApiOnline(false);
      }
    } catch {
      setApiOnline(false);
    }
  };

  const fetchSummaries = async () => {
    try {
      const res = await fetch(`${API_BASE}/summaries/`);
      if (res.ok) {
        const data = await res.json();
        setSummaries(data);
        if (data.length > 0 && !selectedSummary) {
          setSelectedSummary(data[0]);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchReports = async (dateVal = '') => {
    try {
      let url = `${API_BASE}/reports/`;
      if (dateVal) url += `?date=${dateVal}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setReports(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchMarketing = async () => {
    try {
      const res = await fetch(`${API_BASE}/marketing/`);
      if (res.ok) {
        const data = await res.json();
        setMarketingList(data);
        if (data.length > 0 && !selectedMarketing) {
          setSelectedMarketing(data[0]);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchMarketingInstructions = async () => {
    try {
      const res = await fetch(`${API_BASE}/marketing/instructions/`);
      if (res.ok) {
        const data = await res.json();
        setMarketingInstructions(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchInstagram = async () => {
    try {
      const res = await fetch(`${API_BASE}/instagram/`);
      if (res.ok) {
        const data = await res.json();
        setInstagramData(data);
      }
    } catch (err) {
      console.error('Instagram fetch xatosi:', err);
    }
  };

  const handleSyncInstagram = async () => {
    setSyncingInstagram(true);
    try {
      const res = await fetch(`${API_BASE}/instagram/sync/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      if (res.ok) {
        await fetchInstagram();
        alert('✅ ' + (data.message || 'Instagram statistikasi muvaffaqiyatli sinxronlandi!'));
      } else {
        alert('Xatolik: ' + (data.error || 'Sinxronizatsiyada xatolik yuz berdi'));
      }
    } catch (err) {
      alert('Tarmoq xatosi: ' + err.message);
    } finally {
      setSyncingInstagram(false);
    }
  };

  const handleSendMarketingTelegram = async () => {
    setSendingTelegram(true);
    try {
      const res = await fetch(`${API_BASE}/marketing/send-telegram/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (res.ok) {
        setTelegramSentInfo({
          time: new Date().toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          chatId: data.chat_id,
          dispatchId: data.dispatch_id
        });
        alert('🚀 Marketing hisoboti Telegram guruhga yuborish navbatiga muvaffaqiyatli joylashtirildi!\nUserbot 1-3 soniyada xabarni guruhga joylaydi.');
      } else {
        alert('Xatolik: ' + (data.error || 'Yuborishda xatolik yuz berdi'));
      }
    } catch (err) {
      alert('Tarmoq xatosi: ' + err.message);
    } finally {
      setSendingTelegram(false);
    }
  };

  const fetchTeachers = async () => {
    try {
      const res = await fetch(`${API_BASE}/teachers/`);
      if (res.ok) {
        const data = await res.json();
        setTeachers(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchGroups = async () => {
    try {
      const res = await fetch(`${API_BASE}/groups/`);
      if (res.ok) {
        const data = await res.json();
        setGroups(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchFeedbacks = async () => {
    try {
      const res = await fetch(`${API_BASE}/feedbacks/`);
      if (res.ok) {
        const data = await res.json();
        setFeedbacks(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Generate new Gemini Summary
  const handleGenerateSummary = async () => {
    setGeneratingAi(true);
    try {
      const res = await fetch(`${API_BASE}/summaries/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date: genDate })
      });
      const data = await res.json();
      if (res.ok) {
        fetchSummaries();
        fetchStats();
        setSelectedSummary(data.summary);
        alert('✅ Gemini AI direktor xulosasi muvaffaqiyatli tuzildi!');
      } else {
        alert('Xatolik: ' + (data.error || 'Generatsiyada xatolik'));
      }
    } catch (err) {
      alert('Tarmoq xatosi: ' + err.message);
    } finally {
      setGeneratingAi(false);
    }
  };

  // Save marketing metric
  const handleSaveMarketing = async (e) => {
    e.preventDefault();
    setSavingMarketing(true);
    try {
      const res = await fetch(`${API_BASE}/marketing/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: mDate,
          leads_count: parseInt(mLeads) || 0,
          ad_spend: parseFloat(mSpend) || 0,
          competitor_analysis_notes: mNotes,
          generate_ai: mGenerateAi
        })
      });
      if (res.ok) {
        const createdData = await res.json();
        alert('✅ Marketing ko\'rsatkichi saqlandi!' + (mGenerateAi ? ' Gemini AI tahlili ham tayyorlandi.' : ''));
        fetchMarketing();
        fetchStats();
        setSelectedMarketing(createdData);
        setMNotes('');
      }
    } catch (err) {
      alert('Xatolik: ' + err.message);
    } finally {
      setSavingMarketing(false);
    }
  };

  // Run AI analysis on any marketing record
  const handleAnalyzeMarketingAI = async (targetDate) => {
    setAnalyzingMarketingDate(targetDate);
    try {
      const res = await fetch(`${API_BASE}/marketing/ai-analyze/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date: targetDate })
      });
      const data = await res.json();
      if (res.ok) {
        fetchMarketing();
        setSelectedMarketing(data.metric);
        alert('🤖 Gemini AI o\'qitilgan qoidalar asosida marketing tahlili va tavsiyalarni tuzib berdi!');
      } else {
        alert('Xatolik: ' + (data.error || 'AI tahlilda xatolik yuz berdi'));
      }
    } catch (err) {
      alert('Tarmoq xatosi: ' + err.message);
    } finally {
      setAnalyzingMarketingDate('');
    }
  };

  const refreshAll = () => {
    setLoading(true);
    Promise.all([
      fetchStats(),
      fetchSummaries(),
      fetchReports(),
      fetchMarketing(),
      fetchMarketingInstructions(),
      fetchInstagram(),
      fetchTeachers(),
      fetchGroups(),
      fetchFeedbacks()
    ]).finally(() => setLoading(false));
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', width: '100%' }}>
      {/* ================= SIDEBAR ================= */}
      <aside
        style={{
          width: '280px',
          background: 'var(--bg-sidebar)',
          borderRight: '1px solid var(--border-subtle)',
          padding: '1.75rem 1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '2rem',
          position: 'sticky',
          top: 0,
          height: '100vh',
          zIndex: 10
        }}
      >
        {/* Brand */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '12px',
                background: 'var(--gradient-brand)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                boxShadow: '0 4px 16px rgba(99, 102, 241, 0.4)'
              }}
            >
              <Sparkles size={22} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
                Edu<span className="text-gradient">Center</span>
              </h2>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Supervayzer Paneli</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', flex: 1 }}>
          <NavItem
            icon={<LayoutDashboard size={18} />}
            label="Umumiy Ko'rinish"
            active={activeTab === 'overview'}
            onClick={() => setActiveTab('overview')}
          />
          <NavItem
            icon={<Sparkles size={18} />}
            label="Gemini AI Xulosalari"
            badge={summaries.length}
            active={activeTab === 'summaries'}
            onClick={() => setActiveTab('summaries')}
          />
          <NavItem
            icon={<FileText size={18} />}
            label="Kunlik DOCX Hisobotlar"
            badge={reports.length}
            active={activeTab === 'reports'}
            onClick={() => setActiveTab('reports')}
          />
          <NavItem
            icon={<TrendingUp size={18} />}
            label="Marketing & Raqobatchilar"
            active={activeTab === 'marketing'}
            onClick={() => setActiveTab('marketing')}
          />
          <NavItem
            icon={<Users size={18} />}
            label="O'qituvchilar & Guruhlar"
            active={activeTab === 'teachers'}
            onClick={() => setActiveTab('teachers')}
          />
          <NavItem
            icon={<Award size={18} />}
            label="Haftalik Baholar"
            badge={feedbacks.length}
            active={activeTab === 'feedbacks'}
            onClick={() => setActiveTab('feedbacks')}
          />
          <NavItem
            icon={<GraduationCap size={18} />}
            label="O'qituvchi Kabineti"
            active={activeTab === 'teacher_cabinet'}
            onClick={() => setActiveTab('teacher_cabinet')}
          />
        </nav>

        {/* Backend status footer */}
        <div
          style={{
            padding: '1rem',
            background: 'var(--bg-inner)',
            borderRadius: '12px',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.8rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Django API:</span>
            <span className={`badge ${apiOnline ? 'badge-emerald' : 'badge-rose'}`}>
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: apiOnline ? '#10b981' : '#f43f5e',
                  display: 'inline-block'
                }}
              />
              {apiOnline ? 'Online' : 'Offline'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>AI Modeli:</span>
            <span style={{ color: 'var(--accent-purple)', fontWeight: 600 }}>Gemini 2.5 Pro</span>
          </div>
        </div>
      </aside>

      {/* ================= MAIN CONTENT ================= */}
      <main style={{ flex: 1, padding: '2rem 2.5rem', overflowY: 'auto', maxHeight: '100vh' }}>
        {/* Top Header */}
        <header
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '2rem',
            paddingBottom: '1.25rem',
            borderBottom: '1px solid var(--border-subtle)'
          }}
        >
          <div>
            <h1 style={{ fontSize: '1.85rem', fontWeight: 800 }}>
              {activeTab === 'overview' && 'Tizim Umumiy Ko\'rinishi'}
              {activeTab === 'summaries' && 'Google Gemini AI Direktor Xulosalari'}
              {activeTab === 'reports' && 'O\'qituvchilar Kunlik DOCX Hisobotlari'}
              {activeTab === 'marketing' && 'Marketing Ko\'rsatkichlari & Raqobat Tahlili'}
              {activeTab === 'teachers' && 'O\'qituvchilar & Guruhlar Boshqaruvi'}
              {activeTab === 'feedbacks' && 'O\'quvchilar Haftalik Baholari (Weekly Feedback)'}
              {activeTab === 'teacher_cabinet' && 'O\'qituvchi Veb-Kabineti (Haftalik Baholash)'}
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.2rem' }}>
              Bugun: {new Date().toLocaleDateString('uz-UZ', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {/* Theme Toggle Button */}
            <button
              className="theme-toggle-btn"
              onClick={toggleTheme}
              title={theme === 'dark' ? "Yorug' rejimga o'tish (Light mode)" : "Qorong'i rejimga o'tish (Dark mode)"}
            >
              <span className="theme-toggle-icon">
                {theme === 'dark' ? <Sun size={16} color="#fbbf24" /> : <Moon size={16} color="#6366f1" />}
              </span>
              <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
            </button>

            <button className="btn-secondary" onClick={refreshAll} disabled={loading} title="Yangilash">
              <RefreshCw size={16} className={loading ? 'pulse-glow' : ''} />
              <span>Yangilash</span>
            </button>
            <button
              className={activeTab === 'teacher_cabinet' ? 'btn-primary' : 'btn-secondary'}
              onClick={() => setActiveTab(activeTab === 'teacher_cabinet' ? 'overview' : 'teacher_cabinet')}
              title="O'qituvchi kabinetiga o'tish"
            >
              <GraduationCap size={16} />
              <span>O'qituvchi Kabineti</span>
            </button>
          </div>
        </header>

        {/* ================= TAB 1: OVERVIEW ================= */}
        {activeTab === 'overview' && (
          <div>
            {/* Top KPI Cards Grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                gap: '1.25rem',
                marginBottom: '2rem'
              }}
            >
              <KpiCard
                title="Faol O'quvchilar"
                value={stats?.students?.active || 0}
                sub={`Jami: ${stats?.students?.total || 0} | Muzlatilgan: ${stats?.students?.frozen || 0}`}
                icon={<GraduationCap size={22} color="var(--accent-cyan)" />}
                gradient="linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(6, 182, 212, 0.02) 100%)"
              />
              <KpiCard
                title="O'rtacha Davomat"
                value={`${stats?.avg_attendance_rate || 0}%`}
                sub={`Bugun topshirilgan hisobotlar: ${stats?.reports_today_count || 0}`}
                icon={<Activity size={22} color="var(--accent-emerald)" />}
                gradient="linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.02) 100%)"
              />
              <KpiCard
                title="Uyga Vazifa Darajasi"
                value={`${stats?.avg_homework_rate || 0}%`}
                sub="O'quvchilarning vazifa topshirishi"
                icon={<Award size={22} color="var(--accent-purple)" />}
                gradient="linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(168, 85, 247, 0.02) 100%)"
              />
              <KpiCard
                title="Bugungi Darslar"
                value={stats?.today_schedules?.total || 0}
                sub={`Xabardor qilingan: ${stats?.today_schedules?.notified || 0}`}
                icon={<Clock size={22} color="var(--accent-primary)" />}
                gradient="linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(99, 102, 241, 0.02) 100%)"
              />
            </div>

            {/* Quick Banner: Today's AI Summary */}
            <div className="glass-panel" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div
                    style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '10px',
                      background: 'rgba(99, 102, 241, 0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--accent-primary)'
                    }}
                  >
                    <Sparkles size={20} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.15rem' }}>Bugungi Gemini AI Executive Summary</h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Direktor uchun avtomatik tayyorlanuvchi kunlik tahlil
                    </p>
                  </div>
                </div>
                <button
                  className="btn-primary"
                  onClick={() => {
                    setActiveTab('summaries');
                  }}
                >
                  Batafsil Ko'rish
                </button>
              </div>

              {stats?.today_summary ? (
                <div
                  style={{
                    background: 'var(--bg-inner)',
                    padding: '1.25rem',
                    borderRadius: '12px',
                    border: '1px solid var(--border-subtle)',
                    maxHeight: '200px',
                    overflowY: 'auto'
                  }}
                  className="markdown-body"
                >
                  <ReactMarkdown>{stats.today_summary.summary_markdown}</ReactMarkdown>
                </div>
              ) : (
                <div
                  style={{
                    background: 'var(--bg-inner)',
                    padding: '2rem',
                    borderRadius: '12px',
                    textAlign: 'center',
                    color: 'var(--text-muted)'
                  }}
                >
                  <Sparkles size={32} style={{ margin: '0 auto 0.75rem', opacity: 0.5 }} />
                  <p>Bugun uchun hali AI xulosasi tuzilmagan.</p>
                  <button
                    className="btn-primary"
                    style={{ marginTop: '1rem' }}
                    onClick={() => {
                      setActiveTab('summaries');
                    }}
                  >
                    Hozir Generatsiya Qilish
                  </button>
                </div>
              )}
            </div>

            {/* Split row: Recent Reports & Marketing stats */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
              {/* Recent DOCX Reports */}
              <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                  <h3 style={{ fontSize: '1.1rem' }}>So'nggi O'qituvchi Hisobotlari</h3>
                  <button
                    style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', fontSize: '0.85rem', cursor: 'pointer' }}
                    onClick={() => setActiveTab('reports')}
                  >
                    Barchasini ko'rish →
                  </button>
                </div>

                {reports.slice(0, 4).length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {reports.slice(0, 4).map((r) => (
                      <div
                        key={r.id}
                        style={{
                          background: 'var(--bg-inner)',
                          padding: '1rem',
                          borderRadius: '10px',
                          border: '1px solid var(--border-subtle)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between'
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{r.teacher_name}</div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            Guruh: {r.group_name} • Mavzu: {r.topic || 'Ko\'rsatilmagan'}
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span className={`badge ${r.attendance_rate >= 80 ? 'badge-emerald' : 'badge-amber'}`}>
                            Davomat: {r.attendance_rate}%
                          </span>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                            {r.date}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    Hali hisobotlar kiritilmagan.
                  </div>
                )}
              </div>

              {/* Marketing snapshot */}
              <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '1.25rem' }}>Marketing Ko'rsatkichi</h3>
                {stats?.marketing ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div style={{ background: 'var(--bg-inner)', padding: '1rem', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Bugungi Leadlar:</div>
                      <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                        {stats.marketing.leads_count} ta
                      </div>
                    </div>
                    <div style={{ background: 'var(--bg-inner)', padding: '1rem', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Reklama Xarajati:</div>
                      <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>
                        {parseFloat(stats.marketing.ad_spend).toLocaleString()} so'm
                      </div>
                    </div>
                    {stats.marketing.competitor_analysis_notes && (
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        <strong>Raqobatchilar:</strong> {stats.marketing.competitor_analysis_notes}
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    <p style={{ marginBottom: '1rem' }}>Bugun uchun marketing ma'lumotlari kiritilmagan.</p>
                    <button className="btn-secondary" onClick={() => setActiveTab('marketing')}>
                      Ma'lumot Kiritish
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 2: GEMINI AI SUMMARIES ================= */}
        {activeTab === 'summaries' && (
          <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.5rem' }}>
            {/* Left list of dates & generator */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Generator Card */}
              <div className="glass-panel" style={{ padding: '1.25rem' }}>
                <h4 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Sparkles size={16} color="var(--accent-primary)" />
                  Yangi Xulosa Tuzish
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <input
                    type="date"
                    className="input-field"
                    value={genDate}
                    onChange={(e) => setGenDate(e.target.value)}
                  />
                  <button
                    className="btn-primary"
                    style={{ width: '100%', justifyContent: 'center' }}
                    onClick={handleGenerateSummary}
                    disabled={generatingAi}
                  >
                    {generatingAi ? (
                      <>
                        <RefreshCw size={16} className="pulse-glow" />
                        Gemini Tahlil Qilmoqda...
                      </>
                    ) : (
                      <>
                        <Sparkles size={16} />
                        Xulosa Yaratish
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* History List */}
              <div className="glass-panel" style={{ padding: '1.25rem', flex: 1, maxHeight: '600px', overflowY: 'auto' }}>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                  O'tgan Xulosalar ({summaries.length})
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {summaries.map((s) => (
                    <div
                      key={s.id}
                      onClick={() => setSelectedSummary(s)}
                      style={{
                        padding: '0.85rem 1rem',
                        borderRadius: '10px',
                        background: selectedSummary?.id === s.id ? 'rgba(99, 102, 241, 0.15)' : 'var(--bg-inner)',
                        border: selectedSummary?.id === s.id ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{s.date}</span>
                        {s.is_sent_to_director ? (
                          <span className="badge badge-emerald">Direktorga bordi</span>
                        ) : (
                          <span className="badge badge-amber">Kutilmoqda</span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                        Yaratilgan: {new Date(s.created_at).toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Markdown Viewer */}
            <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column' }}>
              {selectedSummary ? (
                <>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      paddingBottom: '1rem',
                      borderBottom: '1px solid var(--border-subtle)',
                      marginBottom: '1.5rem'
                    }}
                  >
                    <div>
                      <h2 style={{ fontSize: '1.4rem' }}>{selectedSummary.date} — Supervayzer Xulosasi</h2>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                        Google Gemini 2.5 Pro tomonidan tayyorlangan
                      </p>
                    </div>
                    <div>
                      {selectedSummary.is_sent_to_director ? (
                        <span className="badge badge-emerald">
                          <CheckCircle2 size={14} /> Telegramga yuborilgan
                        </span>
                      ) : (
                        <span className="badge badge-amber">
                          <Clock size={14} /> Kechki 22:00 da bot orqali jo'natiladi
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="markdown-body" style={{ flex: 1, overflowY: 'auto' }}>
                    <ReactMarkdown>{selectedSummary.summary_markdown}</ReactMarkdown>
                  </div>
                </>
              ) : (
                <div style={{ textAlign: 'center', margin: 'auto', color: 'var(--text-muted)' }}>
                  <Sparkles size={48} style={{ opacity: 0.4, marginBottom: '1rem' }} />
                  <h3>Hech qanday xulosa tanlanmagan</h3>
                  <p>Chap tarafdan sanani tanlang yoki yuqoridagi formadan yangisini yarating.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ================= TAB 3: DOCX REPORTS ================= */}
        {activeTab === 'reports' && (
          <div>
            {/* Filter Bar */}
            <div className="glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Calendar size={18} color="var(--text-muted)" />
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Sana bo'yicha:</span>
                <input
                  type="date"
                  className="input-field"
                  value={reportDateFilter}
                  onChange={(e) => {
                    setReportDateFilter(e.target.value);
                    fetchReports(e.target.value);
                  }}
                />
              </div>
              {reportDateFilter && (
                <button
                  className="btn-secondary"
                  onClick={() => {
                    setReportDateFilter('');
                    fetchReports('');
                  }}
                >
                  Filtrni Tozalash
                </button>
              )}
              <div style={{ marginLeft: 'auto', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Jami hisobotlar: <strong>{reports.length} ta</strong>
              </div>
            </div>

            {/* Reports Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1.25rem' }}>
              {reports.map((r) => (
                <div key={r.id} className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <h3 style={{ fontSize: '1.1rem' }}>{r.teacher_name}</h3>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                        Guruh: <strong>{r.group_name}</strong> • Sana: {r.date}
                      </p>
                    </div>
                    <span className="badge badge-indigo">#{r.id}</span>
                  </div>

                  {/* Rates */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                    <div style={{ background: 'var(--bg-inner)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Davomat:</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: r.attendance_rate >= 80 ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
                        {r.attendance_rate}%
                      </div>
                    </div>
                    <div style={{ background: 'var(--bg-inner)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Uyga vazifa:</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-purple)' }}>
                        {r.homework_rate}%
                      </div>
                    </div>
                  </div>

                  {/* Topic */}
                  <div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Mavzu:</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>{r.topic || 'Ko\'rsatilmagan'}</div>
                  </div>

                  {/* Issues */}
                  {r.issues && r.issues.length > 0 && (
                    <div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--accent-rose)', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <AlertTriangle size={14} /> Aniqlangan muammolar:
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                        {r.issues.map((issue, idx) => (
                          <span key={idx} className="badge badge-rose" style={{ fontSize: '0.7rem' }}>
                            {issue}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* AI Summary */}
                  {r.ai_summary && (
                    <div
                      style={{
                        background: 'rgba(99, 102, 241, 0.08)',
                        border: '1px solid rgba(99, 102, 241, 0.25)',
                        padding: '0.85rem',
                        borderRadius: '8px',
                        fontSize: '0.825rem',
                        lineHeight: 1.5,
                        color: 'var(--text-secondary)'
                      }}
                    >
                      <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '0.25rem' }}>AI Tahlili:</strong>
                      {r.ai_summary}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {reports.length === 0 && (
              <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <FileText size={48} style={{ opacity: 0.4, marginBottom: '1rem' }} />
                <h3>Ushbu sana uchun DOCX hisobotlar topilmadi</h3>
                <p>O'qituvchilar Telegram guruhiga .docx hisobot yuborganida ular avtomatik tahlil qilinadi.</p>
              </div>
            )}
          </div>
        )}

        {/* ================= TAB 4: MARKETING ================= */}
        {activeTab === 'marketing' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
            {/* Top Bar: Instagram Live Stats & Telegram Marketing Broadcast */}
            <div
              className="glass-panel"
              style={{
                padding: '1.5rem',
                display: 'grid',
                gridTemplateColumns: '1.3fr 1fr',
                gap: '1.5rem',
                background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%)',
                border: '1px solid rgba(236, 72, 153, 0.25)',
                borderRadius: '16px'
              }}
            >
              {/* Instagram Card */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    <div
                      style={{
                        width: '38px',
                        height: '38px',
                        borderRadius: '10px',
                        background: 'linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white'
                      }}
                    >
                      <InstagramIcon size={20} color="white" />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        @{instagramData?.config?.instagram_username || 'diamond_academy_uz'}
                        <a
                          href={`https://instagram.com/${instagramData?.config?.instagram_username || 'diamond_academy_uz'}`}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: 'var(--text-muted)', display: 'inline-flex' }}
                          title="Instagramda ochish"
                        >
                          <ExternalLink size={14} />
                        </a>
                      </h3>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {instagramData?.latest_metric?.sync_source || 'Avtomatik Instagram monitoring'}
                      </span>
                    </div>
                  </div>

                  <button
                    className="btn-secondary"
                    onClick={handleSyncInstagram}
                    disabled={syncingInstagram}
                    style={{ padding: '0.45rem 0.85rem', fontSize: '0.82rem' }}
                  >
                    <RefreshCw size={14} className={syncingInstagram ? 'pulse-glow' : ''} />
                    <span>{syncingInstagram ? 'Sinxronlanmoqda...' : 'Instagramni Sinxronlash'}</span>
                  </button>
                </div>

                {/* 4 Instagram Metric badges */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
                  <div style={{ background: 'var(--bg-inner)', padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Obunachilar:</div>
                    <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      {instagramData?.latest_metric?.followers_count ? instagramData.latest_metric.followers_count.toLocaleString() : '14,872'}
                      <span className="badge badge-emerald" style={{ fontSize: '0.68rem', padding: '1px 5px' }}>
                        +{instagramData?.latest_metric?.new_followers_today || 18}
                      </span>
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-inner)', padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Kunlik Qamrov:</div>
                    <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                      {instagramData?.latest_metric?.reach_count ? instagramData.latest_metric.reach_count.toLocaleString() : '5,799'}
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-inner)', padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Profil ko'rishlar:</div>
                    <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--accent-purple)' }}>
                      {instagramData?.latest_metric?.profile_views ? instagramData.latest_metric.profile_views.toLocaleString() : '927'}
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-inner)', padding: '0.75rem', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Postlar / Reels:</div>
                    <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                      {instagramData?.latest_metric?.media_count || '129'} ta
                    </div>
                  </div>
                </div>
              </div>

              {/* Telegram Dispatch Card */}
              <div
                style={{
                  background: 'var(--bg-inner)',
                  padding: '1.25rem',
                  borderRadius: '12px',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '0.75rem'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-primary)' }}>
                      <Send size={16} color="var(--accent-primary)" />
                      Telegram Marketing Guruhiga Yuborish
                    </span>
                    <span className="badge badge-indigo" style={{ fontSize: '0.7rem' }}>
                      Har kuni 21:30 da avto
                    </span>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                    Instagram statistikasi, leadlar, CAC va Gemini AI strategik tavsiyalarini o'z ichiga olgan hisobotni marketing guruhiga yuboring.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <button
                    className="btn-primary"
                    onClick={handleSendMarketingTelegram}
                    disabled={sendingTelegram}
                    style={{ padding: '0.55rem 1.1rem', fontSize: '0.85rem' }}
                  >
                    <Send size={15} className={sendingTelegram ? 'pulse-glow' : ''} />
                    <span>{sendingTelegram ? 'Guruhga jo\'natilmoqda...' : 'Telegram Guruhga Yuborish'}</span>
                  </button>

                  {telegramSentInfo ? (
                    <span className="badge badge-emerald" style={{ fontSize: '0.72rem' }}>
                      ✅ Jo'natildi: {telegramSentInfo.time}
                    </span>
                  ) : (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      💬 Bot buyrug'i: <code style={{ color: 'var(--accent-cyan)' }}>/marketing</code>
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '1.5rem' }}>
              {/* Left Column: Input Form & AI Knowledge Base Info */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {/* Input Form */}
                <div className="glass-panel" style={{ padding: '1.5rem' }}>
                  <h3 style={{ fontSize: '1.15rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <PlusCircle size={20} color="var(--accent-cyan)" />
                    Marketing Kiritish
                  </h3>
                  <form onSubmit={handleSaveMarketing} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                        Sana:
                      </label>
                      <input
                        type="date"
                        className="input-field"
                        style={{ width: '100%' }}
                        value={mDate}
                        onChange={(e) => setMDate(e.target.value)}
                        required
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                        Leadlar Soni:
                      </label>
                      <input
                        type="number"
                        min="0"
                        className="input-field"
                        style={{ width: '100%' }}
                        value={mLeads}
                        onChange={(e) => setMLeads(e.target.value)}
                        required
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                        Reklama Xarajati (so'm):
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="1000"
                        className="input-field"
                        style={{ width: '100%' }}
                        value={mSpend}
                        onChange={(e) => setMSpend(e.target.value)}
                        required
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                        Raqobatchilar Yangiliklari / Aksiyalari:
                      </label>
                      <textarea
                        className="input-field"
                        rows="3"
                        style={{ width: '100%', resize: 'vertical' }}
                        placeholder="Masalan: Najot Ta'lim 20% chegirma berdi..."
                        value={mNotes}
                        onChange={(e) => setMNotes(e.target.value)}
                      />
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0.25rem 0' }}>
                      <input
                        type="checkbox"
                        id="generateAiCheck"
                        checked={mGenerateAi}
                        onChange={(e) => setMGenerateAi(e.target.checked)}
                        style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                      />
                      <label htmlFor="generateAiCheck" style={{ fontSize: '0.825rem', color: 'var(--text-primary)', cursor: 'pointer' }}>
                        🤖 Saqlashda Gemini AI tahlili va tavsiyalarni tuzsin
                      </label>
                    </div>

                    <button type="submit" className="btn-primary" disabled={savingMarketing} style={{ justifyContent: 'center' }}>
                      {savingMarketing ? 'AI Tahlil qilinmoqda...' : 'Saqlash va Tahlil'}
                    </button>
                  </form>
                </div>

                {/* AI Knowledge Base / Instructions Card */}
                <div className="glass-panel" style={{ padding: '1.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <h4 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <Sparkles size={16} color="var(--accent-primary)" />
                      AI ni O'qitish Qoidalari ({marketingInstructions.length})
                    </h4>
                    <a
                      href="http://127.0.0.1:8000/admin/core/marketingaiinstruction/"
                      target="_blank"
                      rel="noreferrer"
                      className="badge badge-indigo"
                      style={{ textDecoration: 'none', cursor: 'pointer' }}
                      title="Django Admindan o'qitish qoidalarini qo'shish va tahrirlash"
                    >
                      Admin Panelda Tahrirlash ↗
                    </a>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                    Gemini barcha marketing xulosalarini quyidagi o'qitilgan qoidalar asosida ishlab chiqadi:
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                    {marketingInstructions.map((inst) => (
                      <div
                        key={inst.id}
                        style={{
                          padding: '0.75rem',
                          borderRadius: '8px',
                          background: 'var(--bg-inner)',
                          border: '1px solid var(--border-subtle)',
                          fontSize: '0.8rem'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                          <strong style={{ color: 'var(--text-primary)' }}>{inst.title}</strong>
                          <span style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)' }}>{inst.category_display?.split(' ')[0]}</span>
                        </div>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.77rem', whiteSpace: 'pre-line', margin: 0 }}>
                          {inst.instruction_text.slice(0, 120)}...
                        </p>
                      </div>
                    ))}
                    {marketingInstructions.length === 0 && (
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        O'qitish qoidalari yuklanmagan.
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Right Column: History Table & Selected AI Analysis Card */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {/* Table */}
                <div className="glass-panel" style={{ padding: '1.5rem', overflowX: 'auto' }}>
                  <h3 style={{ fontSize: '1.15rem', marginBottom: '1.25rem' }}>Kunlik Marketing Ko'rsatkichlari Tarixi</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                        <th style={{ padding: '0.75rem 1rem' }}>Sana</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Leadlar</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Reklama Xarajati</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Lead Narxi (CAC)</th>
                        <th style={{ padding: '0.75rem 1rem' }}>AI Tahlil Holati</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Amal</th>
                      </tr>
                    </thead>
                    <tbody>
                      {marketingList.map((m) => {
                        const isSelected = selectedMarketing?.id === m.id;
                        const cpl = m.cost_per_lead || (m.leads_count > 0 ? (m.ad_spend / m.leads_count).toFixed(0) : 0);
                        const isAnalyzing = analyzingMarketingDate === m.date;

                        return (
                          <tr
                            key={m.id}
                            onClick={() => setSelectedMarketing(m)}
                            style={{
                              borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                              background: isSelected ? 'var(--bg-subtle-hover)' : 'transparent',
                              cursor: 'pointer'
                            }}
                          >
                            <td style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>{m.date}</td>
                            <td style={{ padding: '0.85rem 1rem' }}>
                              <span className="badge badge-cyan">{m.leads_count} ta</span>
                            </td>
                            <td style={{ padding: '0.85rem 1rem', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                              {parseFloat(m.ad_spend).toLocaleString()} so'm
                            </td>
                            <td style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>
                              {cpl > 0 ? `${parseFloat(cpl).toLocaleString()} so'm` : '—'}
                            </td>
                            <td style={{ padding: '0.85rem 1rem' }}>
                              {m.ai_analysis ? (
                                <span className="badge badge-emerald">✅ AI Tahlil mavjud</span>
                              ) : (
                                <span className="badge badge-amber">⏳ Tahlil qilinmagan</span>
                              )}
                            </td>
                            <td style={{ padding: '0.85rem 1rem' }}>
                              <button
                                className="btn-secondary"
                                style={{ padding: '0.35rem 0.65rem', fontSize: '0.78rem' }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleAnalyzeMarketingAI(m.date);
                                }}
                                disabled={isAnalyzing}
                              >
                                {isAnalyzing ? <RefreshCw size={13} className="pulse-glow" /> : <Sparkles size={13} />}
                                <span>{isAnalyzing ? 'Tahlil...' : (m.ai_analysis ? 'Qayta Tahlil' : 'AI Tahlil')}</span>
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>

                  {marketingList.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                      Marketing ma'lumotlari mavjud emas.
                    </div>
                  )}
                </div>

                {/* Selected Marketing AI Showcase Card */}
                {selectedMarketing && (
                  <div
                    className="glass-panel"
                    style={{
                      padding: '1.75rem',
                      border: '1px solid var(--border-accent)',
                      animation: 'fadeIn 0.3s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                      <div>
                        <h3 style={{ fontSize: '1.2rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <Sparkles size={20} color="var(--accent-primary)" />
                          {selectedMarketing.date} uchun Gemini AI Marketing Tahlili
                        </h3>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                          Leadlar: <strong>{selectedMarketing.leads_count} ta</strong> •
                          Xarajat: <strong>{parseFloat(selectedMarketing.ad_spend).toLocaleString()} so'm</strong> •
                          1 ta lead: <strong>{parseFloat(selectedMarketing.cost_per_lead || 0).toLocaleString()} so'm</strong>
                        </p>
                      </div>

                      <button
                        className="btn-primary"
                        style={{ padding: '0.45rem 0.95rem', fontSize: '0.85rem' }}
                        onClick={() => handleAnalyzeMarketingAI(selectedMarketing.date)}
                        disabled={analyzingMarketingDate === selectedMarketing.date}
                      >
                        <RefreshCw size={14} className={analyzingMarketingDate === selectedMarketing.date ? 'pulse-glow' : ''} />
                        <span>AI Tahlilni Yangilash</span>
                      </button>
                    </div>

                    {selectedMarketing.competitor_analysis_notes && (
                      <div
                        style={{
                          padding: '0.85rem 1rem',
                          borderRadius: '10px',
                          background: 'var(--bg-inner)',
                          border: '1px solid var(--border-subtle)',
                          marginBottom: '1.25rem',
                          fontSize: '0.875rem'
                        }}
                      >
                        <strong style={{ color: 'var(--accent-rose)' }}>⚔️ Raqobatchilar yangiliklari: </strong>
                        <span>{selectedMarketing.competitor_analysis_notes}</span>
                      </div>
                    )}

                    {selectedMarketing.ai_analysis || selectedMarketing.ai_recommendations ? (
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                        {/* Analysis Box */}
                        <div
                          style={{
                            padding: '1.25rem',
                            borderRadius: '12px',
                            background: 'var(--bg-inner)',
                            border: '1px solid var(--border-accent)'
                          }}
                        >
                          <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--accent-cyan)' }}>
                            📊 Marketing Tahlili va Xulosasi
                          </h4>
                          <div className="markdown-body" style={{ fontSize: '0.875rem' }}>
                            <ReactMarkdown>{selectedMarketing.ai_analysis || 'Tahlil matni mavjud emas.'}</ReactMarkdown>
                          </div>
                        </div>

                        {/* Recommendations Box */}
                        <div
                          style={{
                            padding: '1.25rem',
                            borderRadius: '12px',
                            background: 'var(--bg-inner)',
                            border: '1px solid var(--accent-emerald)'
                          }}
                        >
                          <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--accent-emerald)' }}>
                            💡 AI Strategik Maslahatlari (Action Points)
                          </h4>
                          <div className="markdown-body" style={{ fontSize: '0.875rem' }}>
                            <ReactMarkdown>{selectedMarketing.ai_recommendations || 'Maslahatlar kiritilmagan.'}</ReactMarkdown>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '2rem', background: 'var(--bg-inner)', borderRadius: '12px' }}>
                        <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
                          Ushbu sana uchun hali Gemini AI tahlili yaratilmagan.
                        </p>
                        <button
                          className="btn-primary"
                          onClick={() => handleAnalyzeMarketingAI(selectedMarketing.date)}
                          disabled={analyzingMarketingDate === selectedMarketing.date}
                        >
                          <Sparkles size={16} />
                          <span>Gemini AI bilan Hozir Tahlil Qilish</span>
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 5: TEACHERS & GROUPS ================= */}
        {activeTab === 'teachers' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* Teachers Section */}
            <div>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Users size={22} color="var(--accent-primary)" />
                Faol O'qituvchilar ({teachers.length})
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
                {teachers.map((t) => (
                  <div key={t.id} className="glass-panel" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                      <div>
                        <h4 style={{ fontSize: '1.1rem' }}>{t.full_name}</h4>
                        <p style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>@{t.telegram_username}</p>
                      </div>
                      <span className="badge badge-emerald">Faol</span>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                      <strong>Fanlar:</strong> {t.subjects}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                      <strong>Telefon:</strong> {t.phone}
                    </div>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '0.5rem',
                        paddingTop: '0.75rem',
                        borderTop: '1px solid var(--border-subtle)'
                      }}
                    >
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Guruhlar:</div>
                        <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{t.groups_count} ta</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Faol O'quvchilar:</div>
                        <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>
                          {t.active_students_count} ta
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Groups Section */}
            <div>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Layers size={22} color="var(--accent-purple)" />
                Guruhlar Ro'yxati ({groups.length})
              </h3>
              <div className="glass-panel" style={{ padding: '1.5rem', overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '0.75rem 1rem' }}>Guruh Nomi</th>
                      <th style={{ padding: '0.75rem 1rem' }}>O'qituvchi</th>
                      <th style={{ padding: '0.75rem 1rem' }}>Dars Kunlari</th>
                      <th style={{ padding: '0.75rem 1rem' }}>Dars Vaqti</th>
                      <th style={{ padding: '0.75rem 1rem' }}>Xona</th>
                      <th style={{ padding: '0.75rem 1rem' }}>Faol O'quvchilar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groups.map((g) => (
                      <tr key={g.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                        <td style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>{g.name}</td>
                        <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)' }}>{g.teacher_name}</td>
                        <td style={{ padding: '0.85rem 1rem' }}>
                          <div style={{ display: 'flex', gap: '0.25rem' }}>
                            {g.schedule_days &&
                              g.schedule_days.map((day, idx) => (
                                <span key={idx} className="badge badge-indigo" style={{ textTransform: 'uppercase', fontSize: '0.65rem' }}>
                                  {day}
                                </span>
                              ))}
                          </div>
                        </td>
                        <td style={{ padding: '0.85rem 1rem' }}>
                          {g.lesson_start_time} - {g.lesson_end_time}
                        </td>
                        <td style={{ padding: '0.85rem 1rem' }}>{g.room_number ? `${g.room_number}-xona` : '—'}</td>
                        <td style={{ padding: '0.85rem 1rem' }}>
                          <span className="badge badge-emerald">{g.students_count} ta</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 6: WEEKLY FEEDBACKS ================= */}
        {activeTab === 'feedbacks' && (
          <div className="glass-panel" style={{ padding: '1.5rem', overflowX: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem' }}>O'quvchilar Haftalik O'zlashtirish Baholari</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  O'qituvchilar veb-kabineti orqali qo'yilgan baholar
                </p>
              </div>
              <span className="badge badge-indigo">{feedbacks.length} ta yozuv</span>
            </div>

            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>O'quvchi</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Guruh</th>
                  <th style={{ padding: '0.75rem 1rem' }}>O'qituvchi</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Hafta Boshi</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Bahosi</th>
                  <th style={{ padding: '0.75rem 1rem' }}>O'qituvchi Izohi</th>
                </tr>
              </thead>
              <tbody>
                {feedbacks.map((f) => {
                  let badgeClass = 'badge-indigo';
                  if (f.performance_status === 'excellent') badgeClass = 'badge-emerald';
                  if (f.performance_status === 'good') badgeClass = 'badge-cyan';
                  if (f.performance_status === 'average') badgeClass = 'badge-amber';
                  if (f.performance_status === 'bad') badgeClass = 'badge-rose';

                  return (
                    <tr key={f.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>{f.student_name}</td>
                      <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)' }}>{f.group_name}</td>
                      <td style={{ padding: '0.85rem 1rem', color: 'var(--text-muted)' }}>{f.teacher_name}</td>
                      <td style={{ padding: '0.85rem 1rem', fontSize: '0.85rem' }}>{f.week_start_date}</td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <span className={`badge ${badgeClass}`}>{f.performance_display}</span>
                      </td>
                      <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)', maxWidth: '300px' }}>
                        {f.comment || <span style={{ color: 'var(--text-muted)' }}>Izoh qoldirilmagan</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {feedbacks.length === 0 && (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                Hali haftalik baholar kiritilmagan.
              </div>
            )}
          </div>
        )}

        {/* ================= TAB 7: TEACHER CABINET ================= */}
        {activeTab === 'teacher_cabinet' && (
          <TeacherCabinet />
        )}
      </main>
    </div>
  );
}

// Subcomponents
function NavItem({ icon, label, badge, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '0.75rem 1rem',
        borderRadius: '10px',
        border: 'none',
        background: active ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
        color: active ? 'var(--accent-primary)' : 'var(--text-secondary)',
        fontWeight: active ? 700 : 500,
        fontSize: '0.875rem',
        cursor: 'pointer',
        textAlign: 'left',
        width: '100%',
        transition: 'all 0.2s',
        borderLeft: active ? '3px solid var(--accent-primary)' : '3px solid transparent'
      }}
    >
      <span style={{ color: active ? 'var(--accent-primary)' : 'var(--text-muted)' }}>{icon}</span>
      <span style={{ flex: 1 }}>{label}</span>
      {badge !== undefined && (
        <span
          style={{
            background: active ? 'var(--accent-primary)' : 'var(--bg-inner)',
            color: active ? '#ffffff' : 'var(--text-secondary)',
            fontSize: '0.7rem',
            padding: '0.15rem 0.5rem',
            borderRadius: '999px',
            fontWeight: 600,
            border: '1px solid var(--border-subtle)'
          }}
        >
          {badge}
        </span>
      )}
    </button>
  );
}

function KpiCard({ title, value, sub, icon, gradient }) {
  return (
    <div
      className="glass-panel"
      style={{
        padding: '1.5rem',
        background: gradient || 'var(--bg-card)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: '0.75rem'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 500 }}>{title}</span>
        <div
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'var(--bg-inner)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '1px solid var(--border-subtle)'
          }}
        >
          {icon}
        </div>
      </div>
      <div>
        <div style={{ fontSize: '1.85rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>{value}</div>
        {sub && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>{sub}</div>}
      </div>
    </div>
  );
}
