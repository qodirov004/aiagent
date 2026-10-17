import React, { useState, useEffect } from 'react';
import {
  GraduationCap,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Save,
  Search,
  Users,
  CheckCircle2,
  Sparkles,
  BookOpen,
  Filter,
  Check,
  RotateCcw,
  DoorOpen,
  Phone,
  Send,
  Loader2,
  AlertTriangle
} from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000/api/teacher/cabinet';

export default function TeacherCabinet() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Data states from API
  const [teachersList, setTeachersList] = useState([]);
  const [currentTeacher, setCurrentTeacher] = useState(null);
  const [selectedTeacherId, setSelectedTeacherId] = useState('');
  const [groups, setGroups] = useState([]);
  const [weekStart, setWeekStart] = useState('');
  const [weekEnd, setWeekEnd] = useState('');
  const [prevWeek, setPrevWeek] = useState('');
  const [nextWeek, setNextWeek] = useState('');
  const [performanceChoices, setPerformanceChoices] = useState([
    { value: 'excellent', label: "A'lo", color: 'emerald' },
    { value: 'good', label: 'Yaxshi', color: 'indigo' },
    { value: 'average', label: "O'rtacha", color: 'amber' },
    { value: 'poor', label: 'Qoniqarsiz', color: 'rose' }
  ]);

  // Local state for evaluations: { [studentId]: { performance_status: '', comment: '' } }
  const [evaluations, setEvaluations] = useState({});
  const [isDirty, setIsDirty] = useState(false);

  // Filters
  const [selectedGroupFilter, setSelectedGroupFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch cabinet data
  const fetchCabinetData = async (teacherId = '', week = '') => {
    setLoading(true);
    setErrorMsg('');
    try {
      let url = `${API_BASE}/`;
      const params = new URLSearchParams();
      if (teacherId) params.append('teacher_id', teacherId);
      if (week) params.append('week', week);

      const queryString = params.toString();
      if (queryString) url += `?${queryString}`;

      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`Server xatosi: ${res.status}`);
      }

      const data = await res.json();
      setTeachersList(data.teachers_list || []);
      setCurrentTeacher(data.teacher);
      if (data.teacher) {
        setSelectedTeacherId(data.teacher.id);
      }
      setGroups(data.groups || []);
      setWeekStart(data.week_start || '');
      setWeekEnd(data.week_end || '');
      setPrevWeek(data.prev_week || '');
      setNextWeek(data.next_week || '');
      if (data.performance_choices) {
        setPerformanceChoices(data.performance_choices);
      }

      // Initialize evaluations state
      const initialEvals = {};
      (data.groups || []).forEach((group) => {
        (group.students || []).forEach((student) => {
          initialEvals[student.id] = {
            performance_status: student.performance_status || '',
            comment: student.comment || ''
          };
        });
      });
      setEvaluations(initialEvals);
      setIsDirty(false);
    } catch (err) {
      console.error('Fetch cabinet error:', err);
      setErrorMsg("Ma'lumotlarni yuklashda xatolik yuz berdi. Backend server ishlayotganini tekshiring.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCabinetData();
  }, []);

  // Change teacher
  const handleTeacherChange = (teacherId) => {
    setSelectedTeacherId(teacherId);
    fetchCabinetData(teacherId, weekStart);
  };

  // Change week
  const handleWeekChange = (targetWeek) => {
    fetchCabinetData(selectedTeacherId, targetWeek);
  };

  // Reset to current week
  const handleCurrentWeek = () => {
    const today = new Date().toISOString().split('T')[0];
    fetchCabinetData(selectedTeacherId, today);
  };

  // Update evaluation for a student
  const handleStatusChange = (studentId, statusValue) => {
    setEvaluations((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        performance_status: prev[studentId]?.performance_status === statusValue ? '' : statusValue
      }
    }));
    setIsDirty(true);
  };

  const handleCommentChange = (studentId, commentValue) => {
    setEvaluations((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        comment: commentValue
      }
    }));
    setIsDirty(true);
  };

  // Quick action: Set all students in current view to "excellent"
  const handleSetAllExcellent = () => {
    setEvaluations((prev) => {
      const updated = { ...prev };
      groups.forEach((group) => {
        if (selectedGroupFilter !== 'all' && group.id.toString() !== selectedGroupFilter) return;
        group.students.forEach((s) => {
          if (!updated[s.id]?.performance_status) {
            updated[s.id] = {
              ...updated[s.id],
              performance_status: 'excellent'
            };
          }
        });
      });
      return updated;
    });
    setIsDirty(true);
  };

  // Save all feedbacks to backend
  const handleSaveFeedbacks = async () => {
    if (!currentTeacher || !weekStart) return;
    setSaving(true);
    setSaveSuccess(false);
    setErrorMsg('');

    try {
      const feedbacksPayload = Object.entries(evaluations)
        .filter(([_, val]) => val && val.performance_status)
        .map(([studentId, val]) => ({
          student_id: parseInt(studentId),
          performance_status: val.performance_status,
          comment: val.comment || ''
        }));

      const res = await fetch(`${API_BASE}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          teacher_id: currentTeacher.id,
          week_start: weekStart,
          feedbacks: feedbacksPayload
        })
      });

      if (!res.ok) {
        throw new Error(`Saqlashda xato: ${res.status}`);
      }

      setSaveSuccess(true);
      setIsDirty(false);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err) {
      console.error('Save error:', err);
      setErrorMsg("Baholarni saqlashda xatolik yuz berdi. Iltimos qayta urinib ko'ring.");
    } finally {
      setSaving(false);
    }
  };

  // Create demo data if no teacher exists
  const handleCreateDemoData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/demo-data/`, { method: 'POST' });
      if (res.ok) {
        fetchCabinetData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Format date range nicely
  const formatDateRange = (start, end) => {
    if (!start || !end) return '';
    try {
      const s = new Date(start);
      const e = new Date(end);
      const options = { day: 'numeric', month: 'short', year: 'numeric' };
      return `${s.toLocaleDateString('uz-UZ', options)} — ${e.toLocaleDateString('uz-UZ', options)}`;
    } catch {
      return `${start} — ${end}`;
    }
  };

  // Filtered groups
  const filteredGroups = groups.filter((g) => {
    if (selectedGroupFilter !== 'all' && g.id.toString() !== selectedGroupFilter) {
      return false;
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Top Banner / Teacher Selector Bar */}
      <div
        className="glass-card"
        style={{
          padding: '1.5rem',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1.25rem'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: '14px',
              background: 'var(--gradient-brand)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              boxShadow: '0 4px 16px rgba(99, 102, 241, 0.4)'
            }}
          >
            <GraduationCap size={28} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h2 style={{ fontSize: '1.35rem', fontWeight: 800 }}>O'qituvchi Kabineti</h2>
              <span className="badge badge-indigo">React Veb-Kabinet</span>
            </div>
            {currentTeacher ? (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
                Ustoz: <strong style={{ color: 'var(--text-primary)' }}>{currentTeacher.full_name}</strong>
                {currentTeacher.subjects && ` • Fan: ${currentTeacher.subjects}`}
                {currentTeacher.telegram_username && ` • @${currentTeacher.telegram_username}`}
              </p>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Hozircha o'qituvchi tanlanmagan
              </p>
            )}
          </div>
        </div>

        {/* Teacher selector dropdown (if multiple teachers) */}
        {teachersList.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>O'qituvchini tanlash:</span>
            <select
              value={selectedTeacherId}
              onChange={(e) => handleTeacherChange(e.target.value)}
              className="custom-select"
              style={{ minWidth: '220px' }}
            >
              {teachersList.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.full_name} ({t.subjects || 'Fan biriktirilmagan'})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Week Navigation & Controls Bar */}
      <div
        className="glass-card"
        style={{
          padding: '1.25rem 1.5rem',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem'
        }}
      >
        {/* Navigation Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            className="btn-secondary"
            onClick={() => handleWeekChange(prevWeek)}
            disabled={loading || !prevWeek}
            title="Oldingi hafta"
          >
            <ChevronLeft size={16} />
            <span>Oldingi hafta</span>
          </button>

          <div
            style={{
              padding: '0.5rem 1.1rem',
              borderRadius: '10px',
              background: 'var(--bg-inner)',
              border: '1px solid var(--border-accent)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
              fontSize: '0.9rem',
              fontWeight: 600,
              color: 'var(--text-primary)'
            }}
          >
            <Calendar size={17} style={{ color: 'var(--accent-primary)' }} />
            <span>{formatDateRange(weekStart, weekEnd)}</span>
          </div>

          <button
            className="btn-secondary"
            onClick={() => handleWeekChange(nextWeek)}
            disabled={loading || !nextWeek}
            title="Keyingi hafta"
          >
            <span>Keyingi hafta</span>
            <ChevronRight size={16} />
          </button>

          <button
            className="btn-secondary"
            onClick={handleCurrentWeek}
            disabled={loading}
            title="Joriy haftaga qaytish"
            style={{ fontSize: '0.8rem', padding: '0.45rem 0.8rem' }}
          >
            <RotateCcw size={14} />
            <span>Joriy hafta</span>
          </button>
        </div>

        {/* Action Buttons: Quick Fill & Save */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {isDirty && (
            <span
              style={{
                fontSize: '0.8rem',
                color: 'var(--accent-amber)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem'
              }}
            >
              <AlertTriangle size={14} />
              O'zgarishlar saqlanmadi
            </span>
          )}

          <button
            className="btn-secondary"
            onClick={handleSetAllExcellent}
            disabled={loading || groups.length === 0}
            title="Baholanmagan o'quvchilarni A'lo qilib belgilash"
          >
            <Sparkles size={16} style={{ color: '#fbbf24' }} />
            <span>Barchasini A'lo</span>
          </button>

          <button
            className="btn-primary"
            onClick={handleSaveFeedbacks}
            disabled={saving || loading || groups.length === 0}
            style={{
              background: saveSuccess ? 'var(--accent-emerald)' : undefined,
              boxShadow: saveSuccess ? '0 0 16px rgba(16, 185, 129, 0.4)' : undefined
            }}
          >
            {saving ? (
              <>
                <Loader2 size={16} className="pulse-glow" />
                <span>Saqlanmoqda...</span>
              </>
            ) : saveSuccess ? (
              <>
                <Check size={16} />
                <span>Saqlandi!</span>
              </>
            ) : (
              <>
                <Save size={16} />
                <span>Baholarni Saqlash</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Success / Error alerts */}
      {saveSuccess && (
        <div
          style={{
            padding: '1rem 1.25rem',
            borderRadius: '12px',
            background: 'var(--badge-emerald-bg)',
            border: '1px solid var(--badge-emerald-border)',
            color: 'var(--badge-emerald-color)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            animation: 'fadeIn 0.3s ease'
          }}
        >
          <CheckCircle2 size={20} />
          <span style={{ fontWeight: 600 }}>
            Haftalik baholar va izohlar bazaga muvaffaqiyatli yozildi!
          </span>
        </div>
      )}

      {errorMsg && (
        <div
          style={{
            padding: '1rem 1.25rem',
            borderRadius: '12px',
            background: 'var(--badge-rose-bg)',
            border: '1px solid var(--badge-rose-border)',
            color: 'var(--badge-rose-color)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem'
          }}
        >
          <AlertTriangle size={20} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      {groups.length > 0 && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem'
          }}
        >
          {/* Group Filter Tabs */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginRight: '0.25rem' }}>
              <Filter size={14} style={{ display: 'inline', marginRight: '4px' }} />
              Guruh:
            </span>
            <button
              onClick={() => setSelectedGroupFilter('all')}
              className={`filter-pill ${selectedGroupFilter === 'all' ? 'active' : ''}`}
            >
              Barcha guruhlar ({groups.length})
            </button>
            {groups.map((g) => (
              <button
                key={g.id}
                onClick={() => setSelectedGroupFilter(g.id.toString())}
                className={`filter-pill ${selectedGroupFilter === g.id.toString() ? 'active' : ''}`}
              >
                {g.name} ({g.students_count})
              </button>
            ))}
          </div>

          {/* Student Search Box */}
          <div style={{ position: 'relative', width: '260px' }}>
            <Search
              size={16}
              style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)'
              }}
            />
            <input
              type="text"
              placeholder="O'quvchini qidirish..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="custom-input"
              style={{ paddingLeft: '2.4rem' }}
            />
          </div>
        </div>
      )}

      {/* Content: Groups & Students Evaluation Cards */}
      {loading ? (
        <div
          className="glass-card"
          style={{ padding: '3.5rem', textAlign: 'center', color: 'var(--text-muted)' }}
        >
          <Loader2 size={32} className="pulse-glow" style={{ margin: '0 auto 1rem', display: 'block' }} />
          <p>O'qituvchi kabineti ma'lumotlari yuklanmoqda...</p>
        </div>
      ) : groups.length === 0 ? (
        <div
          className="glass-card"
          style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            maxWidth: '600px',
            margin: '2rem auto'
          }}
        >
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '20px',
              background: 'var(--bg-inner)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem',
              color: 'var(--accent-primary)'
            }}
          >
            <Users size={32} />
          </div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            O'qituvchi yoki faol guruhlar topilmadi
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem', lineHeight: 1.5 }}>
            Kabinetda baholashni sinab ko'rish uchun test o'qituvchi, guruhlar va o'quvchilarni 1 bosish orqali
            yaratishingiz mumkin.
          </p>
          <button className="btn-primary" onClick={handleCreateDemoData} style={{ margin: '0 auto' }}>
            <Sparkles size={16} />
            <span>Demo Ma'lumotlarni Yaratish</span>
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {filteredGroups.map((group) => {
            // Apply search filter to students
            const visibleStudents = (group.students || []).filter((s) =>
              s.full_name.toLowerCase().includes(searchQuery.toLowerCase())
            );

            return (
              <div key={group.id} className="glass-card" style={{ padding: '1.5rem', overflow: 'hidden' }}>
                {/* Group Header */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    paddingBottom: '1rem',
                    marginBottom: '1.25rem',
                    borderBottom: '1px solid var(--border-subtle)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                    <div
                      style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '10px',
                        background: 'var(--bg-inner)',
                        border: '1px solid var(--border-accent)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--accent-primary)'
                      }}
                    >
                      <BookOpen size={20} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>{group.name}</h3>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.2rem' }}>
                        {group.room_number && (
                          <span
                            style={{
                              fontSize: '0.8rem',
                              color: 'var(--text-secondary)',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.3rem'
                            }}
                          >
                            <DoorOpen size={14} /> {group.room_number}-xona
                          </span>
                        )}
                        {group.schedule_days && (
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            • {group.schedule_days}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <span className="badge badge-indigo">
                    {visibleStudents.length} ta o'quvchi
                  </span>
                </div>

                {/* Students Table */}
                {visibleStudents.length === 0 ? (
                  <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    Qidiruv bo'yicha hech qanday o'quvchi topilmadi.
                  </div>
                ) : (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                      <thead>
                        <tr
                          style={{
                            borderBottom: '1px solid var(--border-subtle)',
                            color: 'var(--text-muted)',
                            fontSize: '0.8rem',
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em'
                          }}
                        >
                          <th style={{ padding: '0.75rem 1rem', width: '48px' }}>#</th>
                          <th style={{ padding: '0.75rem 1rem' }}>O'quvchi</th>
                          <th style={{ padding: '0.75rem 1rem', width: '380px' }}>Haftalik Baho</th>
                          <th style={{ padding: '0.75rem 1rem' }}>Izoh (Tavsiya / Muammo)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {visibleStudents.map((student, idx) => {
                          const currentEval = evaluations[student.id] || {
                            performance_status: '',
                            comment: ''
                          };

                          return (
                            <tr
                              key={student.id}
                              style={{
                                borderBottom: '1px solid var(--border-subtle)',
                                transition: 'background 0.2s ease'
                              }}
                              className="student-table-row"
                            >
                              {/* Index */}
                              <td
                                style={{
                                  padding: '1rem',
                                  fontSize: '0.85rem',
                                  color: 'var(--text-muted)',
                                  fontWeight: 600
                                }}
                              >
                                {idx + 1}
                              </td>

                              {/* Student name & avatar */}
                              <td style={{ padding: '1rem' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                  <div
                                    style={{
                                      width: '36px',
                                      height: '36px',
                                      borderRadius: '50%',
                                      background: 'var(--bg-inner)',
                                      border: '1px solid var(--border-subtle)',
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'center',
                                      fontSize: '0.85rem',
                                      fontWeight: 700,
                                      color: 'var(--accent-primary)'
                                    }}
                                  >
                                    {student.full_name.charAt(0)}
                                  </div>
                                  <div>
                                    <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                                      {student.full_name}
                                    </div>
                                    {student.phone && (
                                      <div
                                        style={{
                                          fontSize: '0.78rem',
                                          color: 'var(--text-muted)',
                                          display: 'flex',
                                          alignItems: 'center',
                                          gap: '0.3rem',
                                          marginTop: '0.1rem'
                                        }}
                                      >
                                        <Phone size={11} /> {student.phone}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </td>

                              {/* Performance Selector Pills */}
                              <td style={{ padding: '1rem' }}>
                                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                                  {performanceChoices.map((choice) => {
                                    const isSelected = currentEval.performance_status === choice.value;

                                    return (
                                      <button
                                        key={choice.value}
                                        type="button"
                                        onClick={() => handleStatusChange(student.id, choice.value)}
                                        className={`eval-pill eval-pill-${choice.color} ${isSelected ? 'selected' : ''}`}
                                      >
                                        {isSelected && <Check size={13} />}
                                        <span>{choice.label}</span>
                                      </button>
                                    );
                                  })}
                                </div>
                              </td>

                              {/* Comment Input */}
                              <td style={{ padding: '1rem' }}>
                                <input
                                  type="text"
                                  placeholder="Qisqa izoh yoki tavsiya yozing..."
                                  value={currentEval.comment || ''}
                                  onChange={(e) => handleCommentChange(student.id, e.target.value)}
                                  className="custom-input"
                                  style={{ width: '100%', fontSize: '0.85rem', padding: '0.5rem 0.8rem' }}
                                />
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Floating Save Bar when dirty */}
      {isDirty && (
        <div
          style={{
            position: 'sticky',
            bottom: '1.5rem',
            padding: '1rem 1.5rem',
            borderRadius: '16px',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--accent-primary)',
            boxShadow: 'var(--shadow-neon)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
            zIndex: 30,
            animation: 'slideUp 0.3s ease'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span
              style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: 'var(--accent-amber)',
                display: 'inline-block'
              }}
            />
            <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>
              Sizda saqlanmagan haftalik baholar mavjud!
            </span>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              className="btn-primary"
              onClick={handleSaveFeedbacks}
              disabled={saving}
              style={{ padding: '0.6rem 1.4rem' }}
            >
              {saving ? <Loader2 size={16} className="pulse-glow" /> : <Save size={16} />}
              <span>{saving ? 'Saqlanmoqda...' : 'O\'zgarishlarni Saqlash'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
