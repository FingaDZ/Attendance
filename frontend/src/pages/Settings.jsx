import React, { useEffect, useState } from 'react';
import api from '../api';
import { Plus, Trash2, Camera, Power, CheckCircle } from 'lucide-react';

const Settings = () => {
    const [wanDomain, setWanDomain] = useState('');
    const [loadingWan, setLoadingWan] = useState(false);

    const fetchCameras = async () => {
        try {
            const response = await api.get('/cameras/');
            if (Array.isArray(response.data)) {
                setCameras(response.data);
            } else {
                setCameras([]);
                console.error("Invalid cameras data:", response.data);
            }
        } catch (err) {
            console.error("Failed to fetch cameras", err);
            setCameras([]);
        }
    };

    const fetchSettings = async () => {
        try {
            const response = await api.get('/settings/wan_domain');
            setWanDomain(response.data.value || '');
        } catch (err) {
            console.error("Failed to fetch WAN domain", err);
        }
    };

    useEffect(() => {
        fetchCameras();
        fetchSettings();
    }, []);

    const handleSaveWanDomain = async (e) => {
        e.preventDefault();
        setLoadingWan(true);
        try {
            const formData = new FormData();
            formData.append('key', 'wan_domain');
            formData.append('value', wanDomain);
            formData.append('description', 'Public domain for WAN access');

            await api.post('/settings/', formData);
            alert('WAN Domain saved successfully!');
        } catch (err) {
            console.error("Failed to save WAN domain", err);
            alert('Failed to save settings.');
        } finally {
            setLoadingWan(false);
        }
    };

    const handleAddCamera = async (e) => {
        e.preventDefault();
        if (!newCamName || !newCamSource) return;

        try {
            await api.post(`/cameras/?name=${newCamName}&source=${encodeURIComponent(newCamSource)}`);
            setNewCamName('');
            setNewCamSource('');
            fetchCameras();
        } catch (err) {
            alert("Failed to add camera.");
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Delete this camera?")) return;
        try {
            await api.delete(`/cameras/${id}`);
            fetchCameras();
        } catch (err) {
            console.error("Failed to delete", err);
        }
    };

    const handleToggleActive = async (id) => {
        try {
            await api.put(`/cameras/${id}/toggle`);
            fetchCameras();
        } catch (err) {
            console.error("Failed to toggle camera", err);
        }
    };

    const handleSelectCamera = async (id) => {
        try {
            await api.put(`/cameras/${id}/select`);
            fetchCameras();
        } catch (err) {
            console.error("Failed to select camera", err);
        }
    };

    return (
        <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-6">Settings</h1>

            {/* WAN Domain Configuration */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
                <h2 className="text-lg font-semibold text-gray-800 mb-4">WAN Domain Configuration</h2>
                <form onSubmit={handleSaveWanDomain} className="flex gap-4 items-end">
                    <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Public Domain URL</label>
                        <input
                            type="text"
                            value={wanDomain}
                            onChange={(e) => setWanDomain(e.target.value)}
                            placeholder="https://your-domain.com"
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                        />
                        <p className="text-xs text-gray-500 mt-1">Used for generating correct links when accessing from outside.</p>
                    </div>
                    <button
                        type="submit"
                        disabled={loadingWan}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg flex items-center mb-[1px] disabled:opacity-50"
                    >
                        {loadingWan ? 'Saving...' : 'Save'}
                    </button>
                </form>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
                <h2 className="text-lg font-semibold text-gray-800 mb-4">Add Camera</h2>
                <form onSubmit={handleAddCamera} className="flex gap-4 items-end">
                    <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Camera Name</label>
                        <input
                            type="text"
                            value={newCamName}
                            onChange={(e) => setNewCamName(e.target.value)}
                            placeholder="e.g. Entrance"
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                            required
                        />
                    </div>
                    <div className="flex-[2]">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Source (URL or Index)</label>
                        <input
                            type="text"
                            value={newCamSource}
                            onChange={(e) => setNewCamSource(e.target.value)}
                            placeholder="rtsp://... or 0"
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                            required
                        />
                    </div>
                    <button
                        type="submit"
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center mb-[1px]"
                    >
                        <Plus className="w-5 h-5 mr-2" />
                        Add
                    </button>
                </form>
                <div className="mt-4 p-4 bg-blue-50 rounded-lg text-sm text-blue-800">
                    <p className="font-semibold mb-2">How to add an IP Camera (RTSP):</p>
                    <p className="mb-1">Use the RTSP URL format provided by your camera manufacturer.</p>
                    <p className="mb-2"><strong>Example (Dahua):</strong></p>
                    <code className="bg-blue-100 px-2 py-1 rounded block mb-2">
                        rtsp://admin:admin@192.168.1.5:554/cam/realmonitor?channel=1&subtype=0
                    </code>
                    <p className="text-xs text-blue-600">
                        Replace <code>admin:admin</code> with your username:password and <code>192.168.1.5</code> with your camera IP.
                    </p>
                    <p className="mt-2 font-semibold">Mobile Camera:</p>
                    <p className="text-xs text-blue-600">
                        Use an "IP Webcam" app on your phone to get an RTSP link, or simply open this app in your phone's browser to use the phone's camera directly in Live View.
                    </p>
                </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-800">Configured Cameras</h2>
                </div>
                <table className="w-full text-left text-sm text-gray-600">
                    <thead className="bg-gray-50 text-gray-700 uppercase font-medium">
                        <tr>
                            <th className="px-6 py-3">Select</th>
                            <th className="px-6 py-3">Status</th>
                            <th className="px-6 py-3">Name</th>
                            <th className="px-6 py-3">Source</th>
                            <th className="px-6 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                        {Array.isArray(cameras) && cameras.map((cam) => (
                            <tr key={cam.id} className="hover:bg-gray-50 transition-colors">
                                <td className="px-6 py-4">
                                    <button
                                        onClick={() => handleSelectCamera(cam.id)}
                                        className={`w-6 h-6 rounded-full border flex items-center justify-center ${cam.is_selected
                                            ? 'bg-blue-600 border-blue-600 text-white'
                                            : 'border-gray-300 text-transparent hover:border-blue-400'
                                            }`}
                                        title="Select for Live View"
                                    >
                                        <CheckCircle size={14} />
                                    </button>
                                </td>
                                <td className="px-6 py-4">
                                    <button
                                        onClick={() => handleToggleActive(cam.id)}
                                        className="flex items-center focus:outline-none"
                                        title="Toggle Active Status"
                                    >
                                        <div className={`w-3 h-3 rounded-full mr-2 ${cam.is_active ? 'bg-green-500' : 'bg-red-500'}`}></div>
                                        <span className={cam.is_active ? 'text-green-700' : 'text-red-700'}>
                                            {cam.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </button>
                                </td>
                                <td className="px-6 py-4 font-medium text-gray-900 flex items-center">
                                    <Camera size={16} className="mr-2 text-gray-400" />
                                    {cam.name}
                                </td>
                                <td className="px-6 py-4 font-mono text-xs">{cam.source}</td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={() => handleDelete(cam.id)}
                                        className="text-red-500 hover:text-red-700 p-1"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {(!Array.isArray(cameras) || cameras.length === 0) && (
                            <tr>
                                <td colSpan="5" className="px-6 py-8 text-center text-gray-500">
                                    No cameras configured.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Settings;
