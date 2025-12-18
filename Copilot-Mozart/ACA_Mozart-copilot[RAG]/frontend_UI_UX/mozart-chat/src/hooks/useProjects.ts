// useProjects Hook - CRUD operations กับ Supabase
// ทำงานจริง ไม่มี mock

import { useState, useCallback, useEffect } from 'react'
import { supabase, type Project } from '../lib/supabase'
import { useAuthContext } from '../contexts/AuthContext'

interface ProjectInput {
    name: string
    description?: string
    rooms?: any[]
    loads?: any
}

interface UseProjectsReturn {
    projects: Project[]
    loading: boolean
    error: string | null
    fetchProjects: () => Promise<void>
    createProject: (input: ProjectInput) => Promise<Project | null>
    updateProject: (id: string, input: Partial<ProjectInput>) => Promise<boolean>
    deleteProject: (id: string) => Promise<boolean>
    clearError: () => void
}

export function useProjects(): UseProjectsReturn {
    const { user, isAuthenticated } = useAuthContext()
    const [projects, setProjects] = useState<Project[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Fetch all projects for current user (RLS จะ filter ให้อัตโนมัติ)
    const fetchProjects = useCallback(async () => {
        if (!isAuthenticated) return

        setLoading(true)
        setError(null)

        try {
            const { data, error: fetchError } = await supabase
                .from('projects')
                .select('*')
                .order('created_at', { ascending: false })

            if (fetchError) {
                setError(fetchError.message)
                return
            }

            setProjects(data || [])
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch projects')
        } finally {
            setLoading(false)
        }
    }, [isAuthenticated])

    // Create new project
    const createProject = useCallback(async (input: ProjectInput): Promise<Project | null> => {
        if (!user) {
            setError('ต้อง login ก่อน')
            return null
        }

        setLoading(true)
        setError(null)

        try {
            const { data, error: createError } = await supabase
                .from('projects')
                .insert({
                    owner_id: user.id,  // สำคัญ! ผูกกับ user
                    name: input.name,
                    description: input.description || null,
                    rooms: input.rooms || null,
                    loads: input.loads || null,
                })
                .select()
                .single()

            if (createError) {
                setError(createError.message)
                return null
            }

            // เพิ่มใน state
            setProjects(prev => [data, ...prev])
            return data
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create project')
            return null
        } finally {
            setLoading(false)
        }
    }, [user])

    // Update project
    const updateProject = useCallback(async (id: string, input: Partial<ProjectInput>): Promise<boolean> => {
        setLoading(true)
        setError(null)

        try {
            const { error: updateError } = await supabase
                .from('projects')
                .update({
                    ...input,
                    updated_at: new Date().toISOString(),
                })
                .eq('id', id)

            if (updateError) {
                setError(updateError.message)
                return false
            }

            // อัปเดต state
            setProjects(prev => prev.map(p =>
                p.id === id ? { ...p, ...input, updated_at: new Date().toISOString() } : p
            ))
            return true
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to update project')
            return false
        } finally {
            setLoading(false)
        }
    }, [])

    // Delete project
    const deleteProject = useCallback(async (id: string): Promise<boolean> => {
        setLoading(true)
        setError(null)

        try {
            const { error: deleteError } = await supabase
                .from('projects')
                .delete()
                .eq('id', id)

            if (deleteError) {
                setError(deleteError.message)
                return false
            }

            // ลบจาก state
            setProjects(prev => prev.filter(p => p.id !== id))
            return true
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete project')
            return false
        } finally {
            setLoading(false)
        }
    }, [])

    const clearError = useCallback(() => setError(null), [])

    // Auto-fetch เมื่อ login
    useEffect(() => {
        if (isAuthenticated) {
            fetchProjects()
        } else {
            setProjects([])
        }
    }, [isAuthenticated, fetchProjects])

    return {
        projects,
        loading,
        error,
        fetchProjects,
        createProject,
        updateProject,
        deleteProject,
        clearError,
    }
}
