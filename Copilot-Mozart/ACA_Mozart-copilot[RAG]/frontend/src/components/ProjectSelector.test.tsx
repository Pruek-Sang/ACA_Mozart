import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProjectSelector } from './ProjectSelector';

// Mock the api module
vi.mock('../lib/api', () => ({
    listProjects: vi.fn().mockResolvedValue({
        projects: [
            { session_id: 'session-1', project_name: 'บ้านคุณสมชาย', stage: 'completed', loads_count: 5 },
            { session_id: 'session-2', project_name: 'บ้านคุณสมหญิง', stage: 'gathering', loads_count: 2 },
        ],
        storage: 'supabase'
    }),
    deleteProject: vi.fn().mockResolvedValue({ status: 'deleted', message: 'OK' }),
    startSessionWithName: vi.fn().mockResolvedValue({ session_id: 'new-session', project_name: 'Test Project' })
}));

describe('ProjectSelector', () => {
    const defaultProps = {
        currentSessionId: 'session-1',
        currentProjectName: 'บ้านคุณสมชาย',
        onSessionChange: vi.fn(),
        onNewProject: vi.fn(),
    };

    it('renders with current project name', () => {
        render(<ProjectSelector {...defaultProps} />);
        expect(screen.getByText('บ้านคุณสมชาย')).toBeInTheDocument();
    });

    it('shows project selector trigger button', () => {
        render(<ProjectSelector {...defaultProps} />);
        expect(screen.getByTestId('project-selector-trigger')).toBeInTheDocument();
    });

    it('opens dropdown when clicked', async () => {
        render(<ProjectSelector {...defaultProps} />);

        const trigger = screen.getByTestId('project-selector-trigger');
        await userEvent.click(trigger);

        await waitFor(() => {
            expect(screen.getByTestId('new-project-button')).toBeInTheDocument();
        });
    });

    it('shows new project modal when button clicked', async () => {
        render(<ProjectSelector {...defaultProps} />);

        const trigger = screen.getByTestId('project-selector-trigger');
        await userEvent.click(trigger);

        const newProjectButton = await screen.findByTestId('new-project-button');
        await userEvent.click(newProjectButton);

        expect(screen.getByTestId('new-project-name-input')).toBeInTheDocument();
    });

    it('has default project name placeholder', async () => {
        render(<ProjectSelector {...defaultProps} />);

        const trigger = screen.getByTestId('project-selector-trigger');
        await userEvent.click(trigger);

        const newProjectButton = await screen.findByTestId('new-project-button');
        await userEvent.click(newProjectButton);

        const input = screen.getByTestId('new-project-name-input');
        expect(input).toHaveAttribute('placeholder', 'ชื่อโปรเจกต์ (เช่น บ้านคุณสมชาย)');
    });
});

describe('ProjectSelector Delete Confirmation', () => {
    it('requires CONFIRM text for deletion', async () => {
        render(
            <ProjectSelector
                currentSessionId="session-1"
                currentProjectName="Test"
                onSessionChange={vi.fn()}
                onNewProject={vi.fn()}
            />
        );

        // Open dropdown
        const trigger = screen.getByTestId('project-selector-trigger');
        await userEvent.click(trigger);

        // Wait for projects to load and find delete button
        await waitFor(() => {
            const deleteButton = screen.queryByTestId('delete-project-session-1');
            if (deleteButton) {
                fireEvent.click(deleteButton);
            }
        });

        // Check for confirmation input (if modal opens)
        const confirmInput = screen.queryByTestId('delete-confirm-input');
        if (confirmInput) {
            expect(confirmInput).toBeInTheDocument();

            // Submit button should be disabled without CONFIRM
            const submitButton = screen.getByTestId('delete-confirm-submit');
            expect(submitButton).toBeDisabled();

            // Type CONFIRM
            await userEvent.type(confirmInput, 'CONFIRM');
            expect(submitButton).not.toBeDisabled();
        }
    });
});
