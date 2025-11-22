import React, { useEffect, useState } from 'react';
import api from '../api';
import { AlertCircle, CheckCircle, XCircle } from 'lucide-react';

const Reports = () => {
    const [employees, setEmployees] = useState([]);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    // Filtered lists
    const [entryNoExit, setEntryNoExit] = useState([]);
    const [exitNoEntry, setExitNoEntry] = useState([]);
    const [noLogs, setNoLogs] = useState([]);
    const [insufficientWorkTime, setInsufficientWorkTime] = useState([]);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [empRes, logRes] = await Promise.all([
                api.get('/employees/'),
                api.get('/attendance/')
            ]);
            setEmployees(empRes.data);
            setLogs(logRes.data);
            analyzeAttendance(empRes.data, logRes.data);
        } catch (err) {
            console.error('Failed to fetch data', err);
        } finally {
            setLoading(false);
        }
    };

    const analyzeAttendance = (emps, allLogs) => {
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Filter today's logs
        const todayLogs = allLogs.filter(log => {
            const logDate = new Date(log.timestamp);
            logDate.setHours(0, 0, 0, 0);
            return logDate.getTime() === today.getTime();
        });

        const entryNoExitList = [];
        const exitNoEntryList = [];
        const noLogsList = [];
        const insufficientWorkTimeList = [];

        emps.forEach(emp => {
            const empLogs = todayLogs.filter(log => log.employee_id === emp.id);

            if (empLogs.length === 0) {
                noLogsList.push(emp);
            } else if (empLogs.length === 1) {
                const logType = empLogs[0].type;
                if (logType === 'ENTRY') {
                    entryNoExitList.push({ ...emp, entryTime: empLogs[0].timestamp });
                } else if (logType === 'EXIT') {
                    exitNoEntryList.push({ ...emp, exitTime: empLogs[0].timestamp });
                }
            } else if (empLogs.length >= 2) {
                // Check work time
                const entryLog = empLogs.find(log => log.type === 'ENTRY');
                const exitLog = empLogs.find(log => log.type === 'EXIT');

                if (entryLog && exitLog) {
                    const entryTime = new Date(entryLog.timestamp);
                    const exitTime = new Date(exitLog.timestamp);
                    const workHours = (exitTime - entryTime) / (1000 * 60 * 60);

                    if (workHours < 5) {
                        insufficientWorkTimeList.push({
                            ...emp,
                            entryTime: entryLog.timestamp,
                            exitTime: exitLog.timestamp,
                            workHours: workHours.toFixed(2)
                        });
                    }
                }
            }
        });

        setEntryNoExit(entryNoExitList);
        setExitNoEntry(exitNoEntryList);
        setNoLogs(noLogsList);
        setInsufficientWorkTime(insufficientWorkTimeList);
    };

    if (loading) {
        return <div className="text-center py-8">Loading...</div>;
    }

    return (
        <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-6">Attendance Reports</h1>

            {/* Entry without Exit */}
            <div className="mb-8 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center mb-4">
                    <AlertCircle className="w-6 h-6 text-yellow-500 mr-2" />
                    <h2 className="text-xl font-bold text-gray-800">Entry Without Exit ({entryNoExit.length})</h2>
                </div>
                {entryNoExit.length === 0 ? (
                    <p className="text-gray-500">No employees with entry but no exit today.</p>
                ) : (
                    <table className="w-full text-left text-sm text-gray-600">
                        <thead className="bg-gray-50 text-gray-700 uppercase font-medium">
                            <tr>
                                <th className="px-4 py-2">ID</th>
                                <th className="px-4 py-2">Name</th>
                                <th className="px-4 py-2">Department</th>
                                <th className="px-4 py-2">Entry Time</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {entryNoExit.map(emp => (
                                <tr key={emp.id} className="hover:bg-gray-50">
                                    <td className="px-4 py-2">{emp.id}</td>
                                    <td className="px-4 py-2 font-medium">{emp.name}</td>
                                    <td className="px-4 py-2">{emp.department}</td>
                                    <td className="px-4 py-2">{new Date(emp.entryTime).toLocaleTimeString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Exit without Entry */}
            <div className="mb-8 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center mb-4">
                    <XCircle className="w-6 h-6 text-red-500 mr-2" />
                    <h2 className="text-xl font-bold text-gray-800">Exit Without Entry ({exitNoEntry.length})</h2>
                </div>
                {exitNoEntry.length === 0 ? (
                    <p className="text-gray-500">No employees with exit but no entry today.</p>
                ) : (
                    <table className="w-full text-left text-sm text-gray-600">
                        <thead className="bg-gray-50 text-gray-700 uppercase font-medium">
                            <tr>
                                <th className="px-4 py-2">ID</th>
                                <th className="px-4 py-2">Name</th>
                                <th className="px-4 py-2">Department</th>
                                <th className="px-4 py-2">Exit Time</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {exitNoEntry.map(emp => (
                                <tr key={emp.id} className="hover:bg-gray-50">
                                    <td className="px-4 py-2">{emp.id}</td>
                                    <td className="px-4 py-2 font-medium">{emp.name}</td>
                                    <td className="px-4 py-2">{emp.department}</td>
                                    <td className="px-4 py-2">{new Date(emp.exitTime).toLocaleTimeString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* No Entry and No Exit */}
            <div className="mb-8 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center mb-4">
                    <CheckCircle className="w-6 h-6 text-gray-500 mr-2" />
                    <h2 className="text-xl font-bold text-gray-800">No Attendance Today ({noLogs.length})</h2>
                </div>
                {noLogs.length === 0 ? (
                    <p className="text-gray-500">All employees have logged attendance today.</p>
                ) : (
                    <table className="w-full text-left text-sm text-gray-600">
                        <thead className="bg-gray-50 text-gray-700 uppercase font-medium">
                            <tr>
                                <th className="px-4 py-2">ID</th>
                                <th className="px-4 py-2">Name</th>
                                <th className="px-4 py-2">Department</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {noLogs.map(emp => (
                                <tr key={emp.id} className="hover:bg-gray-50">
                                    <td className="px-4 py-2">{emp.id}</td>
                                    <td className="px-4 py-2 font-medium">{emp.name}</td>
                                    <td className="px-4 py-2">{emp.department}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Insufficient Work Time */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center mb-4">
                    <AlertCircle className="w-6 h-6 text-orange-500 mr-2" />
                    <h2 className="text-xl font-bold text-gray-800">Insufficient Work Time - Less than 5 hours ({insufficientWorkTime.length})</h2>
                </div>
                {insufficientWorkTime.length === 0 ? (
                    <p className="text-gray-500">All employees have worked at least 5 hours today.</p>
                ) : (
                    <table className="w-full text-left text-sm text-gray-600">
                        <thead className="bg-gray-50 text-gray-700 uppercase font-medium">
                            <tr>
                                <th className="px-4 py-2">ID</th>
                                <th className="px-4 py-2">Name</th>
                                <th className="px-4 py-2">Department</th>
                                <th className="px-4 py-2">Entry</th>
                                <th className="px-4 py-2">Exit</th>
                                <th className="px-4 py-2">Work Hours</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {insufficientWorkTime.map(emp => (
                                <tr key={emp.id} className="hover:bg-gray-50">
                                    <td className="px-4 py-2">{emp.id}</td>
                                    <td className="px-4 py-2 font-medium">{emp.name}</td>
                                    <td className="px-4 py-2">{emp.department}</td>
                                    <td className="px-4 py-2">{new Date(emp.entryTime).toLocaleTimeString()}</td>
                                    <td className="px-4 py-2">{new Date(emp.exitTime).toLocaleTimeString()}</td>
                                    <td className="px-4 py-2">
                                        <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">
                                            {emp.workHours}h / 5h required
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};

export default Reports;
