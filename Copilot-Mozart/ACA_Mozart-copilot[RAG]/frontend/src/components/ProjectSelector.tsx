import React, { useState, useRef, useEffect } from 'react';
import {
    FolderPlus,
    FolderOpen,
    ChevronDown,
    Trash2,
    Clock,
    AlertTriangle,
    Loader2,
    Check
} from 'lucide-react';
import { cn } from '../lib/utils';
import { listProjects, deleteProject, startSessionWithName, type ProjectSummary } from '../lib/api';

/**
 * ProjectSelector - New/Load Project UI Component
 * 
 * Features:
 * - New Project button with name input
 * - Load Project dropdown (max 10)
 * - Delete with CONFIRM protection
 * - Current project indicator
 */

interface ProjectSelectorProps {
    currentSessionId: string | null;
    currentProjectName: string;
    onSessionChange: (sessionId: string, projectName: string) => Promise<void> | void;
    onNewProject: () => void;
    className?: string;
}

export const ProjectSelector: React.FC<ProjectSelectorProps> = ({
    currentSessionId,
    currentProjectName,
    onSessionChange,
    onNewProject,
    className,
}) => {
    // State
    const [isOpen, setIsOpen] = useState(false);
    const [projects, setProjects] = useState<ProjectSummary[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // New project modal
    const [showNewModal, setShowNewModal] = useState(false);
    const [newProjectName, setNewProjectName] = useState('');
    const [isCreating, setIsCreating] = useState(false);

    // Delete confirmation
    const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
    const [deleteConfirm, setDeleteConfirm] = useState('');
    const [isDeleting, setIsDeleting] = useState(false);

    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown on outside click
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Fetch projects when dropdown opens
    useEffect(() => {
        if (isOpen) {
            fetchProjects();
        }
    }, [isOpen]);

    const fetchProjects = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const result = await listProjects();
            setProjects(result.projects);
        } catch (e) {
            setError('ไม่สามารถโหลดโปรเจกต์ได้');
            console.error('Failed to fetch projects:', e);
        } finally {
            setIsLoading(false);
        }
    };

    const handleNewProject = async () => {
        setIsCreating(true);
        try {
            const result = await startSessionWithName(newProjectName || undefined);
            // 🔧 FIX 2026-01-25: Must await onSessionChange to prevent race condition
            // Otherwise sessionId state may still be OLD when user types next command
            await onSessionChange(result.session_id, result.project_name);
            setShowNewModal(false);
            setNewProjectName('');
            setIsOpen(false);
            onNewProject();
        } catch (e) {
            setError('ไม่สามารถสร้างโปรเจกต์ได้');
            console.error('Failed to create project:', e);
        } finally {
            setIsCreating(false);
        }
    };

    const handleLoadProject = async (project: ProjectSummary) => {
        // 🔧 FIX 2026-01-25: Must await to ensure state is updated before closing
        await onSessionChange(project.session_id, project.project_name);
        setIsOpen(false);
    };

    const handleDeleteProject = async (sessionId: string) => {
        if (deleteConfirm !== 'CONFIRM') {
            return;
        }

        setIsDeleting(true);
        try {
            await deleteProject(sessionId, 'CONFIRM');

            // 🆕 FIX: If deleting the currently active project, clear localStorage
            // This prevents the deleted session from reappearing on refresh
            if (sessionId === currentSessionId) {
                localStorage.removeItem('mozart_session_id');
                localStorage.removeItem('mozart_project_name');
                console.log('[DELETE] Cleared localStorage for deleted current project');
                // Trigger new project creation
                onNewProject();
            }

            setDeleteTarget(null);
            setDeleteConfirm('');
            fetchProjects(); // Refresh list
        } catch (e) {
            setError('ไม่สามารถลบโปรเจกต์ได้');
            console.error('Failed to delete project:', e);
        } finally {
            setIsDeleting(false);
        }
    };

    const formatDate = (isoString?: string) => {
        if (!isoString) return '';
        const date = new Date(isoString);
        return date.toLocaleString('th-TH', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className={cn("relative", className)} ref={dropdownRef}>
            {/* Trigger Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-lg transition-colors",
                    "bg-slate-800 hover:bg-slate-700 border border-slate-700",
                    "text-sm text-slate-200"
                )}
                data-testid="project-selector-trigger"
            >
                <FolderOpen size={16} className="text-violet-400" />
                <span className="font-medium truncate max-w-[150px]">
                    {currentProjectName}
                </span>
                <ChevronDown size={14} className={cn(
                    "transition-transform text-slate-400",
                    isOpen && "rotate-180"
                )} />
            </button>

            {/* Dropdown */}
            {isOpen && (
                <div className={cn(
                    "absolute top-full left-0 mt-2 w-80 z-50",
                    "bg-slate-900 border border-slate-700 rounded-lg shadow-xl",
                    "overflow-hidden"
                )}>
                    {/* New Project Button */}
                    <div className="p-2 border-b border-slate-800">
                        <button
                            onClick={() => setShowNewModal(true)}
                            className={cn(
                                "w-full flex items-center gap-2 px-3 py-2 rounded-lg",
                                "bg-gradient-to-r from-violet-600 to-purple-600",
                                "hover:from-violet-500 hover:to-purple-500",
                                "text-white text-sm font-medium transition-colors"
                            )}
                            data-testid="new-project-button"
                        >
                            <FolderPlus size={16} />
                            สร้างโปรเจกต์ใหม่
                        </button>
                    </div>

                    {/* Project List */}
                    <div className="max-h-64 overflow-y-auto">
                        {isLoading ? (
                            <div className="p-4 text-center text-slate-500">
                                <Loader2 size={20} className="animate-spin mx-auto mb-2" />
                                กำลังโหลด...
                            </div>
                        ) : error ? (
                            <div className="p-4 text-center text-red-400 text-sm">
                                {error}
                            </div>
                        ) : projects.length === 0 ? (
                            <div className="p-4 text-center text-slate-500 text-sm">
                                ยังไม่มีโปรเจกต์
                            </div>
                        ) : (
                            <div className="p-2 space-y-1">
                                {projects.map((project) => (
                                    <div
                                        key={project.session_id}
                                        className={cn(
                                            "group flex items-center justify-between p-2 rounded-lg",
                                            "hover:bg-slate-800 transition-colors",
                                            project.session_id === currentSessionId && "bg-slate-800 border border-violet-500/30"
                                        )}
                                    >
                                        <button
                                            onClick={() => handleLoadProject(project)}
                                            className="flex-1 text-left"
                                            data-testid={`load-project-${project.session_id}`}
                                        >
                                            <div className="flex items-center gap-2">
                                                <FolderOpen size={14} className="text-slate-400" />
                                                <span className="text-sm text-slate-200 truncate">
                                                    {project.project_name}
                                                </span>
                                                {project.session_id === currentSessionId && (
                                                    <Check size={12} className="text-violet-400" />
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                                                <Clock size={10} />
                                                {formatDate(project.updated_at)}
                                                {project.loads_count !== undefined && (
                                                    <span>• {project.loads_count} โหลด</span>
                                                )}
                                            </div>
                                        </button>

                                        {/* Delete button */}
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setDeleteTarget(project.session_id);
                                            }}
                                            className={cn(
                                                "p-1.5 rounded opacity-0 group-hover:opacity-100",
                                                "text-slate-500 hover:text-red-400 hover:bg-red-500/10",
                                                "transition-all"
                                            )}
                                            data-testid={`delete-project-${project.session_id}`}
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* New Project Modal */}
            {showNewModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-96 shadow-2xl">
                        <h3 className="text-lg font-semibold text-white mb-4">
                            สร้างโปรเจกต์ใหม่
                        </h3>
                        <input
                            type="text"
                            value={newProjectName}
                            onChange={(e) => setNewProjectName(e.target.value)}
                            placeholder="ชื่อโปรเจกต์ (เช่น บ้านคุณสมชาย)"
                            className={cn(
                                "w-full px-3 py-2 rounded-lg",
                                "bg-slate-800 border border-slate-700",
                                "text-white placeholder:text-slate-500",
                                "focus:outline-none focus:border-violet-500"
                            )}
                            autoFocus
                            data-testid="new-project-name-input"
                        />
                        <p className="text-xs text-slate-500 mt-2">
                            หากไม่กรอก จะใช้ชื่อ "บ้านนายสมหญิง"
                        </p>
                        <div className="flex gap-2 mt-4">
                            <button
                                onClick={() => {
                                    setShowNewModal(false);
                                    setNewProjectName('');
                                }}
                                className="flex-1 px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                            >
                                ยกเลิก
                            </button>
                            <button
                                onClick={handleNewProject}
                                disabled={isCreating}
                                className={cn(
                                    "flex-1 px-4 py-2 rounded-lg",
                                    "bg-violet-600 hover:bg-violet-500 text-white",
                                    "flex items-center justify-center gap-2",
                                    "disabled:opacity-50"
                                )}
                                data-testid="create-project-submit"
                            >
                                {isCreating && <Loader2 size={14} className="animate-spin" />}
                                สร้าง
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {deleteTarget && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="bg-slate-900 border border-red-500/30 rounded-xl p-6 w-96 shadow-2xl">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-2 rounded-lg bg-red-500/10">
                                <AlertTriangle size={20} className="text-red-400" />
                            </div>
                            <h3 className="text-lg font-semibold text-white">
                                ยืนยันการลบโปรเจกต์
                            </h3>
                        </div>
                        <p className="text-sm text-slate-400 mb-4">
                            การลบโปรเจกต์จะลบข้อมูลทั้งหมดอย่างถาวร พิมพ์ <span className="font-mono text-red-400">CONFIRM</span> เพื่อยืนยัน
                        </p>
                        <input
                            type="text"
                            value={deleteConfirm}
                            onChange={(e) => setDeleteConfirm(e.target.value)}
                            placeholder="พิมพ์ CONFIRM"
                            className={cn(
                                "w-full px-3 py-2 rounded-lg",
                                "bg-slate-800 border",
                                deleteConfirm === 'CONFIRM' ? "border-green-500" : "border-slate-700",
                                "text-white placeholder:text-slate-500 font-mono",
                                "focus:outline-none"
                            )}
                            data-testid="delete-confirm-input"
                        />
                        <div className="flex gap-2 mt-4">
                            <button
                                onClick={() => {
                                    setDeleteTarget(null);
                                    setDeleteConfirm('');
                                }}
                                className="flex-1 px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                            >
                                ยกเลิก
                            </button>
                            <button
                                onClick={() => handleDeleteProject(deleteTarget)}
                                disabled={deleteConfirm !== 'CONFIRM' || isDeleting}
                                className={cn(
                                    "flex-1 px-4 py-2 rounded-lg",
                                    "bg-red-600 hover:bg-red-500 text-white",
                                    "flex items-center justify-center gap-2",
                                    "disabled:opacity-50 disabled:cursor-not-allowed"
                                )}
                                data-testid="delete-confirm-submit"
                            >
                                {isDeleting && <Loader2 size={14} className="animate-spin" />}
                                ลบโปรเจกต์
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProjectSelector;
