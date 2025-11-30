import React, { useEffect, useState } from 'react';
import api from '../api';
import { Clock, UserCheck, Lock, Trash2, Download, Filter, UserX, LogIn, LogOut, Camera, X } from 'lucide-react';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

const Dashboard = () => {
    const [logs, setLogs] = useState([]);
    const [filteredLogs, setFilteredLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [employees, setEmployees] = useState([]);

    // Initialize with today's date for performance
    const getTodayString = () => {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    const getFirstDayOfMonthString = () => {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        return `${year}-${month}-01`;
    };

    // ✅ MODIFICATION: Afficher uniquement les logs du jour par défaut (au lieu du mois entier)
    const [startDate, setStartDate] = useState(getTodayString());  // Changé de getFirstDayOfMonthString() à getTodayString()
    const [endDate, setEndDate] = useState(getTodayString());
    const [selectedEmployee, setSelectedEmployee] = useState('');
    const [selectedCamera, setSelectedCamera] = useState('');

    // Stats
    const [stats, setStats] = useState({
        totalEmployees: 0,
        entryToday: 0,
        exitToday: 0,
        absenceToday: 0
    });

    // PIN Verification
    const [showPinModal, setShowPinModal] = useState(false);
    const [pinEmpId, setPinEmpId] = useState('');
    const [pinCode, setPinCode] = useState('');
    const [pinStatus, setPinStatus] = useState(null);

    // v2.11.0: Photo Modal
    const [selectedPhoto, setSelectedPhoto] = useState(null);
    const [showPhotoModal, setShowPhotoModal] = useState(false);

    const openPhotoModal = (logId) => {
        setSelectedPhoto(`/api/logs/${logId}/photo`);
        setShowPhotoModal(true);
    };

    const closePhotoModal = () => {
        setShowPhotoModal(false);
        setSelectedPhoto(null);
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [startDate, endDate, selectedEmployee, selectedCamera]);

    const fetchData = async () => {
        // setLoading(true); // Optional: avoid flickering on auto-refresh
        try {
            const params = { limit: 1000 };
            if (startDate) params.start_date = startDate;
            if (endDate) params.end_date = endDate;
            if (selectedEmployee) params.employee_id = selectedEmployee;
            if (selectedCamera) params.camera_id = selectedCamera;

            const [logsRes, employeesRes] = await Promise.all([
                api.get('/attendance/', { params }),
                api.get('/employees/')
            ]);

            const logsData = Array.isArray(logsRes.data) ? logsRes.data : [];
            const employeesData = Array.isArray(employeesRes.data) ? employeesRes.data : [];

            setLogs(logsData);
            setFilteredLogs(logsData);
            setEmployees(employeesData);
            calculateStats(logsData, employeesData);
        } catch (err) {
            console.error("Failed to fetch data", err);
        } finally {
            setLoading(false);
        }
    };

    const calculateStats = (currentLogs, currentEmployees) => {
        const today = new Date().toDateString();
        // If we filtered by date in backend, currentLogs might already be just today's logs.
        // But to be safe for stats (in case filter is wider), we filter by today again.
        const todayLogs = currentLogs.filter(log => new Date(log.timestamp).toDateString() === today);

        const uniqueEntries = new Set(todayLogs.filter(l => l.type === 'ENTRY').map(l => l.employee_id));
        const uniqueExits = new Set(todayLogs.filter(l => l.type === 'EXIT').map(l => l.employee_id));

        setStats({
            totalEmployees: currentEmployees.length,
            entryToday: uniqueEntries.size,
            exitToday: uniqueExits.size,
            absenceToday: currentEmployees.length - uniqueEntries.size
        });
    };

    const handlePinSubmit = async (e) => {
        e.preventDefault();
        setPinStatus(null);
        try {
            const formData = new FormData();
            formData.append('employee_id', pinEmpId);
            formData.append('pin', pinCode);

            await api.post('/verify-pin/', formData);
            setPinStatus('success');
            setTimeout(() => {
                setShowPinModal(false);
                setPinEmpId('');
                setPinCode('');
                setPinStatus(null);
                fetchData();
            }, 1500);
        } catch (err) {
            setPinStatus('error');
        }
    };

    const handleDeleteLog = async (logId) => {
        if (!window.confirm('Delete this attendance record?')) return;
        try {
            await api.delete(`/attendance/${logId}`);
            fetchData();
        } catch (err) {
            console.error('Failed to delete log', err);
        }
    };

    const formatWorkedTime = (minutes) => {
        if (!minutes && minutes !== 0) return '-';
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        return `${h} H ${m} Minutes`;
    };

    const exportToExcel = () => {
        const ws = XLSX.utils.json_to_sheet(filteredLogs.map(log => ({
            Date: new Date(log.timestamp).toLocaleDateString(),
            Time: new Date(log.timestamp).toLocaleTimeString(),
            Employee: log.employee_name,
            Type: log.type,
            Camera: log.camera_id,
            Confidence: (log.confidence * 100).toFixed(1) + '%',
            WorkedHours: formatWorkedTime(log.worked_minutes)
        })));
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Attendance");
        XLSX.writeFile(wb, "attendance_report.xlsx");
    };

    const exportToCSV = () => {
        const ws = XLSX.utils.json_to_sheet(filteredLogs.map(log => ({
            Date: new Date(log.timestamp).toLocaleDateString(),
            Time: new Date(log.timestamp).toLocaleTimeString(),
            Employee: log.employee_name,
            Type: log.type,
            Camera: log.camera_id,
            Confidence: (log.confidence * 100).toFixed(1) + '%',
            WorkedHours: formatWorkedTime(log.worked_minutes)
        })));
        const csv = XLSX.utils.sheet_to_csv(ws);
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", "attendance_report.csv");
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const exportToPDF = () => {
        const doc = new jsPDF();
        doc.text("Attendance Report", 14, 15);

        const tableColumn = ["Date", "Time", "Employee", "Type", "Camera", "Confidence", "Worked Hours"];
        const tableRows = [];

        filteredLogs.forEach(log => {
            const logData = [
                new Date(log.timestamp).toLocaleDateString(),
                new Date(log.timestamp).toLocaleTimeString(),
                log.employee_name,
                log.type || 'N/A',
                log.camera_id,
                (log.confidence * 100).toFixed(1) + '%',
                formatWorkedTime(log.worked_minutes)
            ];
            tableRows.push(logData);
        });

        doc.autoTable({
            head: [tableColumn],
            body: tableRows,
            startY: 20,
        });
        doc.save("attendance_report.pdf");
    };

    return (
        <div className="p-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
                    <p className="text-gray-500 mt-1">Overview and attendance logs</p>
                </div>
                <div className="flex flex-wrap gap-3">
                    <button onClick={exportToExcel} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center transition-colors shadow-sm">
                        <Download className="w-4 h-4 mr-2" /> Excel
                    </button>
                    <button onClick={exportToCSV} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center transition-colors shadow-sm">
                        <Download className="w-4 h-4 mr-2" /> CSV
                    </button>
                    <button disabled className="bg-gray-300 text-gray-500 px-4 py-2 rounded-lg flex items-center cursor-not-allowed opacity-60">
                        <Download className="w-4 h-4 mr-2" /> PDF
                    </button>
                    <button
                        onClick={async () => {
                            if (window.confirm('Delete ALL attendance logs?')) {
                                try {
                                    await api.delete('/attendance/');
                                    fetchData();
                                } catch (err) {
                                    console.error('Failed to delete all logs', err);
                                }
                            }
                        }}
                        className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg flex items-center transition-colors shadow-sm"
                    >
                        <Trash2 className="w-4 h-4 mr-2" /> Clear
                    </button>
                    <button
                        onClick={() => setShowPinModal(true)}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg flex items-center transition-colors shadow-sm"
                    >
                        <Lock className="w-4 h-4 mr-2" /> PIN
                    </button>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 text-sm font-medium">Total Employees</h3>
                        <UserCheck className="text-blue-500 w-6 h-6" />
                    </div>
                    <p className="text-3xl font-bold text-gray-800">{stats.totalEmployees}</p>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 text-sm font-medium">Entry Today</h3>
                        <LogIn className="text-green-500 w-6 h-6" />
                    </div>
                    <p className="text-3xl font-bold text-gray-800">{stats.entryToday}</p>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 text-sm font-medium">Exit Today</h3>
                        <LogOut className="text-orange-500 w-6 h-6" />
                    </div>
                    <p className="text-3xl font-bold text-gray-800">{stats.exitToday}</p>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 text-sm font-medium">Absence Today</h3>
                        <UserX className="text-red-500 w-6 h-6" />
                    </div>
                    <p className="text-3xl font-bold text-gray-800">{stats.absenceToday}</p>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 mb-6">
                <div className="flex items-center mb-4 text-gray-700 font-medium">
                    <Filter className="w-5 h-5 mr-2" /> Filters
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Start Date</label>
                        <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">End Date</label>
                        <input
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Employee</label>
                        <select
                            value={selectedEmployee}
                            onChange={(e) => setSelectedEmployee(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                        >
                            <option value="">All Employees</option>
                            {employees.map(emp => (
                                <option key={emp.id} value={emp.id}>{emp.name}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Camera</label>
                        <input
                            type="text"
                            placeholder="Camera ID..."
                            value={selectedCamera}
                            onChange={(e) => setSelectedCamera(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                        />
                    </div>
                </div>
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-gray-600">
                        <thead className="bg-gray-50 text-gray-700 uppercase font-medium">
                            <tr>
                                <th className="px-6 py-3">Date</th>
                                <th className="px-6 py-3">Time</th>
                                <th className="px-6 py-3">Employee</th>
                                <th className="px-6 py-3">Type</th>
                                <th className="px-6 py-3">Camera</th>
                                <th className="px-6 py-3">Photo</th>
                                <th className="px-6 py-3">Confidence</th>
                                <th className="px-6 py-3">Worked Hours</th>
                                <th className="px-6 py-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {filteredLogs.map((log) => (
                                <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 font-medium text-gray-900">
                                        {new Date(log.timestamp).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 text-gray-500">
                                        {new Date(log.timestamp).toLocaleTimeString()}
                                    </td>
                                    <td className="px-6 py-4 font-medium text-gray-900">{log.employee_name}</td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${log.type === 'ENTRY' ? 'bg-green-100 text-green-700' :
                                            log.type === 'EXIT' ? 'bg-orange-100 text-orange-700' :
                                                'bg-gray-100 text-gray-700'
                                            }`}>
                                            {log.type || 'N/A'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded-full text-xs ${log.camera_id === 'PIN' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-700'
                                            }`}>
                                            {log.camera_id}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        {log.photo_capture ? (
                                            <button
                                                onClick={() => openPhotoModal(log.id)}
                                                className="text-blue-600 hover:text-blue-800 flex items-center"
                                            >
                                                <Camera className="w-4 h-4 mr-1" /> View
                                            </button>
                                        ) : (
                                            <span className="text-gray-400 text-xs">-</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4">{(log.confidence * 100).toFixed(1)}%</td>
                                    <td className="px-6 py-4 font-medium">
                                        {formatWorkedTime(log.worked_minutes)}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button
                                            onClick={() => handleDeleteLog(log.id)}
                                            className="text-red-500 hover:text-red-700 p-1"
                                            title="Delete log"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {filteredLogs.length === 0 && (
                                <tr>
                                    <td colSpan="8" className="px-6 py-8 text-center text-gray-500">
                                        No attendance logs found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* PIN Modal */}
            {showPinModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl p-6 w-full max-w-sm">
                        <h2 className="text-xl font-bold mb-4 flex items-center">
                            <Lock className="w-5 h-5 mr-2 text-indigo-600" />
                            PIN Verification
                        </h2>
                        <form onSubmit={handlePinSubmit}>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Employee ID</label>
                                <input
                                    type="number"
                                    value={pinEmpId}
                                    onChange={(e) => setPinEmpId(e.target.value)}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"
                                    required
                                    autoFocus
                                />
                            </div>
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-700 mb-1">PIN Code</label>
                                <input
                                    type="password"
                                    maxLength="4"
                                    value={pinCode}
                                    onChange={(e) => setPinCode(e.target.value)}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"
                                    required
                                />
                            </div>

                            {pinStatus === 'success' && (
                                <div className="mb-4 p-2 bg-green-100 text-green-700 rounded text-center text-sm">
                                    Verified! Attendance Logged.
                                </div>
                            )}
                            {pinStatus === 'error' && (
                                <div className="mb-4 p-2 bg-red-100 text-red-700 rounded text-center text-sm">
                                    Invalid ID or PIN.
                                </div>
                            )}

                            <div className="flex justify-end space-x-3">
                                <button
                                    type="button"
                                    onClick={() => setShowPinModal(false)}
                                    className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                                >
                                    Verify
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* v2.11.0: Photo Modal */}
            {showPhotoModal && (
                <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 p-4" onClick={closePhotoModal}>
                    <div className="bg-white rounded-xl overflow-hidden max-w-2xl w-full relative" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b">
                            <h3 className="text-lg font-bold">Captured Photo</h3>
                            <button onClick={closePhotoModal} className="text-gray-500 hover:text-gray-700">
                                <X className="w-6 h-6" />
                            </button>
                        </div>
                        <div className="p-4 flex justify-center bg-gray-100">
                            {selectedPhoto ? (
                                <img
                                    src={selectedPhoto}
                                    alt="Attendance Capture"
                                    className="max-h-[60vh] rounded shadow-lg"
                                    onError={(e) => {
                                        e.target.onerror = null;
                                        e.target.src = 'https://via.placeholder.com/640x480?text=Photo+Error';
                                    }}
                                />
                            ) : (
                                <div className="h-64 flex items-center justify-center text-gray-400">Loading...</div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Dashboard;
