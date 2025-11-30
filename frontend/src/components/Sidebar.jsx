import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Video, Users, FileText, Settings } from 'lucide-react';

const Sidebar = ({ isOpen, onClose }) => {
    const location = useLocation();

    const links = [
        { to: '/', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/live', label: 'Live View', icon: Video },
        { to: '/employees', label: 'Employees', icon: Users },
        { to: '/reports', label: 'Reports', icon: FileText },
        { to: '/settings', label: 'Settings', icon: Settings },
    ];

    return (
        <>
            {/* Mobile Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
                    onClick={onClose}
                />
            )}

            {/* Sidebar */}
            <div className={`
                fixed inset-y-0 left-0 z-30 w-64 bg-gray-900 text-white transform transition-transform duration-300 ease-in-out
                md:relative md:translate-x-0
                ${isOpen ? 'translate-x-0' : '-translate-x-full'}
            `}>
                <div className="flex items-center justify-between p-6">
                    <div className="text-2xl font-bold text-blue-400">Attendance AI</div>
                    {/* Close button for mobile */}
                    <button
                        onClick={onClose}
                        className="md:hidden text-gray-400 hover:text-white focus:outline-none"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <nav className="flex-1 px-4 space-y-2 mt-4">
                    {links.map((link) => {
                        const Icon = link.icon;
                        const isActive = location.pathname === link.to;
                        return (
                            <Link
                                key={link.to}
                                to={link.to}
                                onClick={() => onClose()} // Close sidebar on link click (mobile)
                                className={`flex items-center px-4 py-3 rounded-lg transition-colors ${isActive ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                    }`}
                            >
                                <Icon className="w-5 h-5 mr-3" />
                                {link.label}
                            </Link>
                        );
                    })}
                </nav>
                <div className="p-4 border-t border-gray-800 text-xs text-gray-500 flex flex-col items-center space-y-1">
                    <div className="flex justify-between w-full">
                        <span>v2.11.0</span>
                        <span>© 2025</span>
                    </div>
                    <div className="text-blue-400 font-semibold tracking-wider pt-2 opacity-80">
                        Powered by AIRBAND
                    </div>
                </div>
            </div >
        </>
    );
};

export default Sidebar;
