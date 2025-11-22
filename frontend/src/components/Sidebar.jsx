import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Video, Users, FileText, Settings } from 'lucide-react';

const Sidebar = () => {
    const location = useLocation();

    const links = [
        { to: '/', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/live', label: 'Live View', icon: Video },
        { to: '/employees', label: 'Employees', icon: Users },
        { to: '/reports', label: 'Reports', icon: FileText },
        { to: '/settings', label: 'Settings', icon: Settings },
    ];

    return (
        <div className="w-64 bg-gray-900 text-white h-screen flex flex-col">
            <div className="p-6 text-2xl font-bold text-blue-400">Attendance AI</div>
            <nav className="flex-1 px-4 space-y-2 mt-4">
                {links.map((link) => {
                    const Icon = link.icon;
                    const isActive = location.pathname === link.to;
                    return (
                        <Link
                            key={link.to}
                            to={link.to}
                            className={`flex items-center px-4 py-3 rounded-lg transition-colors ${isActive ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                }`}
                        >
                            <Icon className="w-5 h-5 mr-3" />
                            {link.label}
                        </Link>
                    );
                })}
            </nav>
            <div className="p-4 text-xs text-gray-600 text-center">
                v1.0.0
            </div>
        </div>
    );
};

export default Sidebar;
