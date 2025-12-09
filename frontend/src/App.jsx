import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, User, Shield, Send, CheckCircle, XCircle, Sparkles, FileText, BarChart2, AlertTriangle, ThumbsDown, ThumbsUp, Moon, Sun, Globe, Trash2, Database, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// --- Shared Components ---

const Toast = ({ message, type, onClose }) => {
    useEffect(() => {
        const timer = setTimeout(onClose, 3000);
        return () => clearTimeout(timer);
    }, [onClose]);

    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500'
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.3 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5, transition: { duration: 0.2 } }}
            className={`${colors[type] || 'bg-gray-800'} text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 mb-3 backdrop-blur-md bg-opacity-90`}
        >
            {type === 'success' && <CheckCircle size={18} />}
            {type === 'error' && <AlertTriangle size={18} />}
            {type === 'info' && <Sparkles size={18} />}
            <span className="font-medium text-sm">{message}</span>
        </motion.div>
    );
};

// --- Customer Tab ---

const CustomerTab = ({ addToast }) => {
    const [customerId] = useState(() => {
        const stored = localStorage.getItem('customer_id');
        if (stored) return stored;
        const newId = 'cust_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('customer_id', newId);
        return newId;
    });

    const [tickets, setTickets] = useState([]);
    const [activeTicket, setActiveTicket] = useState(null);
    const [newTicketText, setNewTicketText] = useState('');
    const [replyText, setReplyText] = useState('');

    const fetchTickets = async () => {
        try {
            const res = await fetch(`${API_BASE}/tickets?customer_id=${customerId}`);
            const data = await res.json();
            setTickets(data);
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        fetchTickets();
        const interval = setInterval(fetchTickets, 5000);
        return () => clearInterval(interval);
    }, [customerId]);

    const createTicket = async () => {
        if (!newTicketText.trim()) return;
        try {
            await fetch(`${API_BASE}/tickets`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ customer_id: customerId, text: newTicketText })
            });
            setNewTicketText('');
            fetchTickets();
            addToast('Ticket created successfully!', 'success');
        } catch (err) {
            addToast('Failed to create ticket', 'error');
        }
    };

    const sendReply = async () => {
        if (!replyText.trim() || !activeTicket) return;
        await fetch(`${API_BASE}/tickets/${activeTicket.id}/reply`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role: 'customer', content: replyText })
        });
        setReplyText('');
        fetchTickets();
    };

    const deleteTicket = async (ticketId) => {
        if (!confirm("Are you sure you want to delete this ticket?")) return;
        try {
            await fetch(`${API_BASE}/tickets/${ticketId}`, { method: 'DELETE' });
            addToast('Ticket deleted', 'success');
            if (activeTicket?.id === ticketId) setActiveTicket(null);
            fetchTickets();
        } catch (err) {
            addToast('Failed to delete ticket', 'error');
        }
    };

    const activeTicketData = tickets.find(t => t.id === activeTicket?.id);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 max-w-5xl mx-auto"
        >
            <div className="mb-8 flex justify-between items-center">
                <h2 className="text-3xl font-bold flex items-center gap-3 text-gray-800 dark:text-white">
                    <User className="text-blue-500" /> Customer Portal
                </h2>
                <span className="text-xs font-mono bg-gray-200 dark:bg-gray-700 px-3 py-1 rounded-full text-gray-600 dark:text-gray-300">
                    ID: {customerId}
                </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Ticket List */}
                <div className="glass-card p-6 h-[600px] flex flex-col">
                    <h3 className="font-bold text-lg mb-4 dark:text-gray-200">My Tickets</h3>
                    <div className="mb-4 relative">
                        <input
                            className="w-full p-3 pl-4 pr-12 rounded-xl bg-gray-50 dark:bg-gray-800 border-none focus:ring-2 focus:ring-blue-500 dark:text-white transition-all"
                            placeholder="Describe your issue..."
                            value={newTicketText}
                            onChange={e => setNewTicketText(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && createTicket()}
                        />
                        <button
                            onClick={createTicket}
                            className="absolute right-2 top-2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
                        >
                            <Send size={16} />
                        </button>
                    </div>
                    <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                        <AnimatePresence>
                            {tickets.map(t => (
                                <motion.div
                                    key={t.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -20 }}
                                    onClick={() => setActiveTicket(t)}
                                    className={`p-4 rounded-xl cursor-pointer transition-all border shadow-sm ${activeTicket?.id === t.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-500/30' : 'bg-white dark:bg-gray-800/40 border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/60 hover:shadow-md'}`}
                                >
                                    <div className="font-semibold truncate dark:text-gray-200 mb-1">{t.text}</div>
                                    <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400">
                                        <span>{new Date(t.created_at * 1000).toLocaleDateString()}</span>
                                        <span className={`px-2 py-0.5 rounded-full ${t.status === 'open' ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'}`}>
                                            {t.status}
                                        </span>
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                </div>

                {/* Chat Area */}
                <div className="md:col-span-2 glass-card p-0 h-[600px] flex flex-col relative overflow-hidden">
                    {activeTicketData ? (
                        <>
                            <div className="p-4 border-b dark:border-gray-700/50 flex justify-between items-start">
                                <div>
                                    <h3 className="font-bold text-xl dark:text-white mb-1">{activeTicketData.text}</h3>
                                    <span className="text-xs text-gray-400">Ticket ID: {activeTicketData.id}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    {activeTicketData.status === 'resolved' && (
                                        <>
                                            <span className="bg-gray-100 dark:bg-gray-700 text-gray-500 px-3 py-1 rounded-full text-xs font-bold">
                                                RESOLVED
                                            </span>
                                            <button
                                                onClick={() => deleteTicket(activeTicketData.id)}
                                                className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                                title="Delete Ticket"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </>
                                    )}
                                </div>
                            </div>

                            <div className="flex-1 overflow-y-auto space-y-4 p-4 custom-scrollbar bg-gray-50/50 dark:bg-gray-900/50">
                                {activeTicketData.messages.map((m, i) => (
                                    <motion.div
                                        key={i}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className={`flex ${m.role === 'customer' ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div className={`max-w-[80%] p-4 rounded-2xl shadow-sm ${m.role === 'customer' ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-br-none' : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-bl-none'}`}>
                                            <div className="text-sm leading-relaxed">{m.content}</div>
                                            <div className="text-[10px] opacity-70 mt-2 text-right">
                                                {new Date(m.ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>

                            <div className="p-4 border-t dark:border-gray-700/50">
                                <div className="relative">
                                    <input
                                        className="w-full p-4 pr-14 rounded-xl bg-gray-50 dark:bg-gray-800 border-none focus:ring-2 focus:ring-blue-500 dark:text-white shadow-inner"
                                        placeholder={activeTicketData.status === 'resolved' ? "Ticket resolved. Create a new one for further assistance." : "Type a reply..."}
                                        value={replyText}
                                        onChange={e => setReplyText(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && sendReply()}
                                        disabled={activeTicketData.status === 'resolved'}
                                    />
                                    <button
                                        onClick={sendReply}
                                        disabled={activeTicketData.status === 'resolved'}
                                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-all shadow-md"
                                    >
                                        <Send size={20} />
                                    </button>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                            <MessageSquare size={64} className="mb-6 opacity-10" />
                            <p className="text-lg font-medium">Select a ticket to view conversation</p>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
};

// --- Agent Tab ---

const AgentTab = ({ addToast }) => {
    const [tickets, setTickets] = useState([]);
    const [activeTicket, setActiveTicket] = useState(null);
    const [suggestion, setSuggestion] = useState(null);
    const [loadingSuggestion, setLoadingSuggestion] = useState(false);
    const [replyText, setReplyText] = useState('');
    const [cannedResponses, setCannedResponses] = useState([]);
    const [summary, setSummary] = useState(null);
    const [loadingSummary, setLoadingSummary] = useState(false);
    const [targetLang, setTargetLang] = useState('English');
    const [kbModalOpen, setKbModalOpen] = useState(false);
    const chatEndRef = useRef(null);

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [activeTicket?.messages]);

    useEffect(() => {
        fetch(`${API_BASE}/canned_responses`)
            .then(res => res.json())
            .then(data => setCannedResponses(data))
            .catch(err => console.error(err));
    }, []);

    const fetchTickets = async () => {
        try {
            const res = await fetch(`${API_BASE}/tickets?status=open`);
            const data = await res.json();
            setTickets(data);
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        fetchTickets();
        const interval = setInterval(fetchTickets, 5000);
        return () => clearInterval(interval);
    }, []);

    const loadTicket = async (t) => {
        setActiveTicket(t);
        setSuggestion(null);
        setSummary(null);
        setReplyText('');
        const res = await fetch(`${API_BASE}/tickets/${t.id}`);
        const data = await res.json();
        setActiveTicket(data);
    };

    const generateSuggestion = async () => {
        if (!activeTicket) return;
        setLoadingSuggestion(true);
        try {
            const res = await fetch(`${API_BASE}/tickets/${activeTicket.id}/suggest`, { method: 'POST' });
            const data = await res.json();
            setSuggestion(data);
            setReplyText(data.answer || '');
            addToast('AI Suggestion generated', 'info');
        } catch (err) {
            console.error(err);
            addToast('Failed to generate suggestion', 'error');
        } finally {
            setLoadingSuggestion(false);
        }
    };

    const generateSummary = async () => {
        if (!activeTicket) return;
        setLoadingSummary(true);
        try {
            const res = await fetch(`${API_BASE}/tickets/${activeTicket.id}/summarize`, { method: 'POST' });
            const data = await res.json();
            setSummary(data.summary);
            addToast('Summary generated', 'info');
        } catch (err) {
            console.error(err);
            addToast('Failed to generate summary', 'error');
        } finally {
            setLoadingSummary(false);
        }
    };

    const translateReply = async () => {
        if (!replyText) return;
        try {
            const res = await fetch(`${API_BASE}/translate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: replyText, target_lang: targetLang })
            });
            const data = await res.json();
            setReplyText(data.translated_text);
            addToast(`Translated to ${targetLang}`, 'success');
        } catch (err) {
            addToast('Translation failed', 'error');
        }
    };

    const sendReply = async (resolve = false) => {
        if (!replyText.trim() || !activeTicket) return;

        try {
            await fetch(`${API_BASE}/tickets/${activeTicket.id}/reply`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role: 'agent', content: replyText })
            });

            if (resolve) {
                await fetch(`${API_BASE}/tickets/${activeTicket.id}/resolve`, { method: 'POST' });
                addToast('Ticket resolved', 'success');
            } else {
                addToast('Reply sent', 'success');
            }

            if (suggestion) {
                await fetch(`${API_BASE}/feedback`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ticket_text: activeTicket.messages[0].content,
                        accepted: true,
                        comment: "Agent accepted suggestion",
                        used_citations: suggestion.evidence.map(e => e.chunk_id)
                    })
                });
            }

            setReplyText('');
            setSuggestion(null);
            setSummary(null);
            fetchTickets();
            setActiveTicket(null);
        } catch (err) {
            addToast('Failed to send reply', 'error');
        }
    };

    const [langOpen, setLangOpen] = useState(false);
    const langTimeoutRef = useRef(null);

    const handleLangEnter = () => {
        if (langTimeoutRef.current) clearTimeout(langTimeoutRef.current);
        setLangOpen(true);
    };

    const handleLangLeave = () => {
        langTimeoutRef.current = setTimeout(() => {
            setLangOpen(false);
        }, 500);
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="p-6 max-w-[1600px] mx-auto h-[calc(100vh-80px)] flex flex-col"
        >
            <div className="mb-4 flex justify-between items-center shrink-0">
                <h2 className="text-2xl font-bold flex items-center gap-3 text-purple-700 dark:text-purple-400">
                    <Shield /> Agent Workspace
                </h2>
                <div className="flex gap-4">
                    <button
                        onClick={() => setKbModalOpen(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm font-medium dark:text-gray-200"
                    >
                        <Database size={16} /> Knowledge Base
                    </button>
                    <button onClick={fetchTickets} className="text-sm text-blue-600 hover:underline dark:text-blue-400">Refresh List</button>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
                {/* Left: Ticket List (3 cols) */}
                <div className="col-span-3 glass-card p-4 overflow-hidden flex flex-col">
                    <h3 className="font-bold text-gray-700 dark:text-gray-200 mb-4 px-2">Queue ({tickets.length})</h3>
                    <div className="flex-1 overflow-y-auto space-y-3 p-2 custom-scrollbar pb-10">
                        {tickets.map(t => (
                            <motion.div
                                key={t.id}
                                layoutId={t.id}
                                onClick={() => loadTicket(t)}
                                className={`p-4 rounded-xl cursor-pointer transition-all border-l-4 shadow-sm ${activeTicket?.id === t.id
                                    ? 'bg-purple-50 dark:bg-purple-900/20 border-purple-500 ring-1 ring-purple-500/30'
                                    : 'bg-white dark:bg-gray-800 border-transparent hover:bg-gray-50 dark:hover:bg-gray-700'
                                    }`}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <div className="font-semibold text-sm text-gray-900 dark:text-gray-100 line-clamp-2">{t.text}</div>
                                    {t.priority === 'high' && <span className="h-2 w-2 rounded-full bg-red-500 shrink-0 mt-1"></span>}
                                </div>
                                <div className="flex flex-wrap gap-1 mb-2">
                                    {t.sentiment === 'negative' && <span className="text-[10px] px-1.5 py-0.5 bg-red-100 text-red-700 rounded-full">Angry</span>}
                                    {t.tags?.slice(0, 2).map(tag => (
                                        <span key={tag} className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded-full capitalize">{tag}</span>
                                    ))}
                                </div>
                                <div className="text-xs text-gray-400">
                                    {new Date(t.created_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>

                {/* Middle: Chat (6 cols) */}
                <div className="col-span-6 glass-card p-0 flex flex-col overflow-hidden relative">
                    {activeTicket ? (
                        <>
                            <div className="p-4 border-b dark:border-gray-700/50 bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm z-10">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h3 className="font-bold text-lg dark:text-white">{activeTicket.text}</h3>
                                        <div className="flex gap-2 mt-1">
                                            <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full font-medium">OPEN</span>
                                            <span className="text-xs text-gray-400 flex items-center gap-1"><User size={10} /> {activeTicket.customer_id}</span>
                                        </div>
                                    </div>
                                    <button
                                        onClick={generateSummary}
                                        disabled={loadingSummary}
                                        className="text-xs bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-lg hover:bg-indigo-100 border border-indigo-200 flex items-center gap-1 transition-colors"
                                    >
                                        {loadingSummary ? <span className="animate-spin">⌛</span> : <FileText size={12} />}
                                        Summarize
                                    </button>
                                </div>
                                {summary && (
                                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="mt-3 p-3 bg-indigo-50/50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 rounded-lg text-sm text-indigo-900 dark:text-indigo-200">
                                        <span className="font-bold block mb-1 text-xs uppercase tracking-wide opacity-70">Summary</span>
                                        {summary}
                                    </motion.div>
                                )}
                            </div>

                            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-gray-50/30 dark:bg-gray-900/30 pb-4">
                                {activeTicket.messages.map((m, i) => (
                                    <motion.div
                                        key={i}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className={`flex ${m.role === 'agent' ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div className={`max-w-[85%] p-3 rounded-2xl text-sm shadow-sm ${m.role === 'agent' ? 'bg-purple-600 text-white rounded-br-none' : 'bg-white dark:bg-gray-800 border dark:border-gray-700 text-gray-800 dark:text-gray-200 rounded-bl-none'}`}>
                                            <span className="font-bold text-[10px] block mb-1 opacity-50 uppercase tracking-wider">{m.role}</span>
                                            {m.content}
                                        </div>
                                    </motion.div>
                                ))}
                                <div ref={chatEndRef} />
                            </div>

                            <div className="p-4 bg-white dark:bg-gray-800 border-t dark:border-gray-700/50">
                                <div className="flex gap-2 mb-3 overflow-x-auto pb-1 no-scrollbar">
                                    {cannedResponses.map(c => (
                                        <button
                                            key={c.id}
                                            onClick={() => setReplyText(prev => prev + (prev ? "\n" : "") + c.text)}
                                            className="whitespace-nowrap px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                                        >
                                            {c.title}
                                        </button>
                                    ))}
                                </div>
                                <div className="relative">
                                    <textarea
                                        className="w-full h-24 p-3 pr-12 border dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-purple-500 resize-none bg-gray-50 dark:bg-gray-900 dark:text-white text-sm"
                                        placeholder="Type your reply..."
                                        value={replyText}
                                        onChange={e => setReplyText(e.target.value)}
                                    />
                                    <div className="absolute bottom-3 right-3 flex gap-2">
                                        <div
                                            className="relative"
                                            onMouseEnter={handleLangEnter}
                                            onMouseLeave={handleLangLeave}
                                        >
                                            <button
                                                onClick={translateReply}
                                                className="p-1.5 text-gray-400 hover:text-purple-600 transition-colors"
                                                title={`Translate to ${targetLang}`}
                                            >
                                                <Globe size={16} />
                                            </button>
                                            <AnimatePresence>
                                                {langOpen && (
                                                    <motion.div
                                                        initial={{ opacity: 0, y: 10 }}
                                                        animate={{ opacity: 1, y: 0 }}
                                                        exit={{ opacity: 0, y: 10 }}
                                                        className="absolute bottom-full right-0 mb-2 bg-white dark:bg-gray-800 shadow-xl rounded-lg p-2 border dark:border-gray-700 min-w-[140px] z-50 grid grid-cols-2 gap-1"
                                                    >
                                                        {['English', 'Hindi', 'Bengali', 'Telugu', 'Tamil', 'Marathi', 'Gujarati', 'Kannada', 'Malayalam', 'Spanish', 'French'].map(lang => (
                                                            <div
                                                                key={lang}
                                                                onClick={() => { setTargetLang(lang); setTimeout(translateReply, 0); setLangOpen(false); }}
                                                                className={`px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded cursor-pointer text-xs dark:text-gray-200 ${targetLang === lang ? 'bg-purple-50 dark:bg-purple-900/30 text-purple-600' : ''}`}
                                                            >
                                                                {lang}
                                                            </div>
                                                        ))}
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex justify-between items-center mt-3">
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => sendReply(false)}
                                            className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-sm font-medium transition-colors"
                                        >
                                            Reply
                                        </button>
                                        <button
                                            onClick={() => sendReply(true)}
                                            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2 text-sm font-medium shadow-lg shadow-purple-500/30 transition-all"
                                        >
                                            <CheckCircle size={16} /> Resolve
                                        </button>
                                    </div>
                                    {activeTicket.status === 'resolved' && (
                                        <button
                                            onClick={async () => {
                                                if (!confirm("Delete ticket?")) return;
                                                await fetch(`${API_BASE}/tickets/${activeTicket.id}`, { method: 'DELETE' });
                                                setActiveTicket(null);
                                                fetchTickets();
                                            }}
                                            className="text-red-500 hover:bg-red-50 p-2 rounded-lg transition-colors"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    )}
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                            <div className="w-20 h-20 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                                <MessageSquare size={32} className="opacity-30" />
                            </div>
                            <p>Select a ticket to start working</p>
                        </div>
                    )}
                </div>

                {/* Right: AI & Info (3 cols) */}
                <div className="col-span-3 glass-card p-4 flex flex-col gap-4 overflow-y-auto custom-scrollbar pb-10">
                    {!activeTicket ? (
                        <div className="text-center text-gray-400 mt-10 text-sm">Select a ticket to see AI insights</div>
                    ) : (
                        <>
                            {/* AI Suggestion Card */}
                            <div className="bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-gray-800 dark:to-gray-800 rounded-xl p-4 border border-purple-100 dark:border-gray-700 shadow-sm">
                                <div className="flex justify-between items-center mb-3">
                                    <h4 className="font-bold text-purple-800 dark:text-purple-300 flex items-center gap-2 text-sm">
                                        <Sparkles size={14} /> AI Copilot
                                    </h4>
                                    {suggestion && <span className="text-[10px] bg-white dark:bg-gray-700 px-2 py-0.5 rounded-full border shadow-sm">{(suggestion.confidence * 100).toFixed(0)}% Conf.</span>}
                                </div>

                                {!suggestion && !loadingSuggestion && (
                                    <button
                                        onClick={generateSuggestion}
                                        className="w-full py-2 bg-white dark:bg-gray-700 border border-purple-200 dark:border-gray-600 rounded-lg text-purple-700 dark:text-purple-300 text-sm font-medium hover:shadow-md transition-all"
                                    >
                                        Generate Draft
                                    </button>
                                )}

                                {loadingSuggestion && <div className="text-center py-4 text-xs text-gray-500 animate-pulse">Analyzing knowledge base...</div>}

                                {suggestion && (
                                    <div className="space-y-3">
                                        <div className="text-xs text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-700/50 p-2 rounded border dark:border-gray-600">
                                            {suggestion.answer}
                                        </div>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => setReplyText(suggestion.answer)}
                                                className="flex-1 py-1.5 bg-purple-600 text-white rounded text-xs hover:bg-purple-700"
                                            >
                                                Use
                                            </button>
                                            <button
                                                onClick={() => {
                                                    fetch(`${API_BASE}/feedback`, {
                                                        method: 'POST',
                                                        headers: { 'Content-Type': 'application/json' },
                                                        body: JSON.stringify({
                                                            ticket_text: activeTicket.messages[activeTicket.messages.length - 1].content,
                                                            accepted: false,
                                                            comment: "Rejected",
                                                            used_citations: suggestion.evidence.map(e => e.chunk_id)
                                                        })
                                                    });
                                                    setSuggestion(null);
                                                }}
                                                className="px-3 py-1.5 border border-red-200 text-red-600 rounded text-xs hover:bg-red-50"
                                            >
                                                Reject
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Context/Metadata Card */}
                            <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border dark:border-gray-700 shadow-sm">
                                <h4 className="font-bold text-gray-700 dark:text-gray-200 mb-3 text-sm">Context</h4>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-xs">
                                        <span className="text-gray-500">Sentiment</span>
                                        <span className={`font-medium ${activeTicket.sentiment === 'negative' ? 'text-red-500' : 'text-green-500'}`}>{activeTicket.sentiment}</span>
                                    </div>
                                    <div className="flex justify-between text-xs">
                                        <span className="text-gray-500">Priority</span>
                                        <span className={`font-medium ${activeTicket.priority === 'high' ? 'text-red-500' : 'text-gray-700 dark:text-gray-300'}`}>{activeTicket.priority}</span>
                                    </div>
                                    <div className="pt-2 border-t dark:border-gray-700">
                                        <span className="text-xs text-gray-500 block mb-1">Tags</span>
                                        <div className="flex flex-wrap gap-1">
                                            {activeTicket.tags?.map(tag => (
                                                <span key={tag} className="text-[10px] px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded-full text-gray-600 dark:text-gray-300 capitalize">{tag}</span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Citations */}
                            {suggestion?.evidence?.length > 0 && (
                                <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border dark:border-gray-700 shadow-sm flex-1 overflow-y-auto">
                                    <h4 className="font-bold text-gray-700 dark:text-gray-200 mb-3 text-sm">Sources</h4>
                                    <div className="space-y-2">
                                        {suggestion.evidence.map((e, i) => (
                                            <div key={i} className="text-xs p-2 bg-gray-50 dark:bg-gray-700/50 rounded border dark:border-gray-600">
                                                <div className="font-semibold text-blue-600 dark:text-blue-400 mb-1 truncate" title={e.title}>{e.title || 'Untitled'}</div>
                                                <div className="text-gray-500 dark:text-gray-400 line-clamp-2">{e.chunk_text}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Knowledge Base Modal */}
            <AnimatePresence>
                {kbModalOpen && (
                    <motion.div
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                        onClick={() => setKbModalOpen(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
                            className="bg-white dark:bg-gray-800 w-full max-w-4xl max-h-[80vh] rounded-2xl shadow-2xl overflow-hidden flex flex-col"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="p-6 border-b dark:border-gray-700 flex justify-between items-center">
                                <h2 className="text-xl font-bold dark:text-white flex items-center gap-2"><Database /> Knowledge Base Editor</h2>
                                <button onClick={() => setKbModalOpen(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full"><XCircle size={20} /></button>
                            </div>
                            <KnowledgeBaseEditor addToast={addToast} />
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

// --- Knowledge Base Editor ---

const KnowledgeBaseEditor = ({ addToast }) => {
    const [chunks, setChunks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchChunks = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/knowledge`);
            const data = await res.json();
            setChunks(data);
        } catch (err) {
            addToast('Failed to load knowledge base', 'error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchChunks();
    }, []);

    const deleteChunk = async (id) => {
        if (!confirm("Are you sure you want to delete this knowledge chunk?")) return;
        try {
            await fetch(`${API_BASE}/knowledge/${id}`, { method: 'DELETE' });
            setChunks(prev => prev.filter(c => c.chunk_id !== id));
            addToast('Chunk deleted', 'success');
        } catch (err) {
            addToast('Failed to delete chunk', 'error');
        }
    };

    const filteredChunks = chunks.filter(c =>
        c.chunk_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.title.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="flex-1 flex flex-col overflow-hidden">
            <div className="p-4 bg-gray-50 dark:bg-gray-900 border-b dark:border-gray-700 flex gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
                    <input
                        className="w-full pl-10 p-2 rounded-lg border dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                        placeholder="Search knowledge base..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500">{filteredChunks.length} chunks</span>
                </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                {loading ? (
                    <div className="text-center py-10 text-gray-500">Loading knowledge base...</div>
                ) : (
                    filteredChunks.map(c => (
                        <div key={c.chunk_id} className="p-4 bg-white dark:bg-gray-700/50 border dark:border-gray-600 rounded-xl flex gap-4 group hover:shadow-md transition-all">
                            <div className="flex-1">
                                <div className="font-bold text-sm text-blue-600 dark:text-blue-400 mb-1">{c.title}</div>
                                <div className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2">{c.chunk_text}</div>
                                <div className="text-xs text-gray-400 mt-2 font-mono">{c.chunk_id}</div>
                            </div>
                            <button
                                onClick={() => deleteChunk(c.chunk_id)}
                                className="self-start p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                title="Delete Chunk"
                            >
                                <Trash2 size={18} />
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

// --- Analytics Tab (Simplified for brevity, but kept functional) ---

const AnalyticsTab = ({ addToast }) => {
    const [data, setData] = useState(null);

    useEffect(() => {
        fetch(`${API_BASE}/analytics/gaps`)
            .then(res => res.json())
            .then(setData)
            .catch(console.error);
    }, []);

    if (!data) return <div className="p-8 text-center dark:text-gray-300">Loading analytics...</div>;

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-6 max-w-6xl mx-auto">
            <h2 className="text-2xl font-bold flex items-center gap-2 mb-6 dark:text-white"><BarChart2 /> Analytics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="glass-card p-6 border-l-4 border-blue-500">
                    <div className="text-gray-500 dark:text-gray-400 text-sm">Total Feedback</div>
                    <div className="text-3xl font-bold dark:text-white">{data.stats.total}</div>
                </div>
                <div className="glass-card p-6 border-l-4 border-red-500">
                    <div className="text-gray-500 dark:text-gray-400 text-sm">Rejected</div>
                    <div className="text-3xl font-bold dark:text-white">{data.stats.rejected}</div>
                </div>
                <div className="glass-card p-6 border-l-4 border-yellow-500">
                    <div className="text-gray-500 dark:text-gray-400 text-sm">Gap Rate</div>
                    <div className="text-3xl font-bold dark:text-white">{(data.stats.gap_rate * 100).toFixed(1)}%</div>
                </div>
            </div>
            {/* Upload Section */}
            <div className="glass-card p-6 mb-8">
                <h3 className="font-bold mb-4 dark:text-white flex items-center gap-2"><FileText size={18} /> Upload Knowledge</h3>
                <input
                    type="file"
                    accept=".pdf"
                    className="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    onChange={async (e) => {
                        const file = e.target.files[0];
                        if (!file) return;
                        const formData = new FormData();
                        formData.append("file", file);
                        try {
                            addToast("Uploading...", "info");
                            const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
                            const data = await res.json();
                            if (data.status === 'success') addToast(`Added ${data.chunks_added} chunks`, 'success');
                            else addToast("Upload failed", 'error');
                        } catch (err) {
                            addToast("Upload failed", 'error');
                        }
                    }}
                />
            </div>
        </motion.div>
    );
};

// --- Main App ---

function App() {
    const [activeTab, setActiveTab] = useState('customer');
    const [darkMode, setDarkMode] = useState(() => {
        if (typeof window !== 'undefined') return localStorage.getItem('darkMode') === 'true';
        return false;
    });
    const [toasts, setToasts] = useState([]);

    const addToast = (message, type = 'info') => {
        const id = Date.now();
        setToasts(prev => [...prev, { id, message, type }]);
    };

    const removeToast = (id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    };

    useEffect(() => {
        if (darkMode) {
            document.documentElement.classList.add('dark');
            document.body.classList.add('dark');
            localStorage.setItem('darkMode', 'true');
        } else {
            document.documentElement.classList.remove('dark');
            document.body.classList.remove('dark');
            localStorage.setItem('darkMode', 'false');
        }
    }, [darkMode]);

    return (
        <div className={`min-h-screen font-sans text-gray-900 dark:text-gray-100 transition-colors duration-300`}>
            {/* Toast Container */}
            <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end pointer-events-none">
                <AnimatePresence>
                    {toasts.map(toast => (
                        <div key={toast.id} className="pointer-events-auto">
                            <Toast message={toast.message} type={toast.type} onClose={() => removeToast(toast.id)} />
                        </div>
                    ))}
                </AnimatePresence>
            </div>

            {/* Header */}
            <header className="glass glass-nav sticky top-0 z-40 border-b border-white/20 dark:border-gray-800 dark:bg-slate-950/90">
                <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-2 rounded-xl shadow-lg">
                            <MessageSquare size={20} />
                        </div>
                        <h1 className="font-bold text-xl tracking-tight dark:text-white">Support<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">AI</span></h1>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex bg-gray-100/50 dark:bg-gray-800/50 p-1 rounded-xl backdrop-blur-sm">
                            {['customer', 'agent', 'analytics'].map(tab => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all capitalize ${activeTab === tab ? 'bg-white dark:bg-gray-700 shadow-sm text-blue-600 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}`}
                                >
                                    {tab}
                                </button>
                            ))}
                        </div>

                        <button
                            onClick={() => {
                                setDarkMode(!darkMode);
                                addToast(darkMode ? 'Light mode enabled' : 'Dark mode enabled', 'info');
                            }}
                            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 transition-colors"
                        >
                            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
                        </button>
                    </div>
                </div>
            </header>

            {/* Content */}
            <main className="pt-6">
                <AnimatePresence mode="wait">
                    {activeTab === 'customer' && <CustomerTab key="cust" addToast={addToast} />}
                    {activeTab === 'agent' && <AgentTab key="agent" addToast={addToast} />}
                    {activeTab === 'analytics' && <AnalyticsTab key="analytics" addToast={addToast} />}
                </AnimatePresence>
            </main>
        </div>
    );
}

export default App;
