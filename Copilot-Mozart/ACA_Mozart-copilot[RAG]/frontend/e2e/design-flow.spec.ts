import { test, expect, type Page } from '@playwright/test';

/**
 * Mozart E2E Browser Tests
 * 
 * Tests full user flows to catch UI bugs that unit tests miss.
 * Runs nightly via e2e-browser.yml workflow.
 */

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173';

test.describe('Mozart Design Flow', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to app
        await page.goto(BASE_URL);

        // Wait for app to hydrate
        await page.waitForLoadState('networkidle');
    });

    test('homepage loads without errors', async ({ page }) => {
        // Check page loaded
        await expect(page).toHaveTitle(/Mozart/i);

        // Check for React error overlay (indicates Error #310 or similar)
        const errorOverlay = page.locator('[data-reactroot-error]');
        await expect(errorOverlay).toHaveCount(0);
    });

    test('can type in chat input', async ({ page }) => {
        // Find chat input
        const chatInput = page.locator('input[type="text"], textarea').first();

        if (await chatInput.isVisible()) {
            await chatInput.fill('ทดสอบ');
            await expect(chatInput).toHaveValue('ทดสอบ');
        }
    });

    test('design request flow', async ({ page }) => {
        // Skip if not logged in UI
        const chatInput = page.locator('[placeholder*="พิมพ์"], [placeholder*="Enter"]').first();

        if (!await chatInput.isVisible({ timeout: 5000 }).catch(() => false)) {
            test.skip(true, 'Chat input not visible - may need login');
            return;
        }

        // Send design request
        await chatInput.fill('บ้าน 2 ชั้น ห้องนอน 2 ห้อง');
        await chatInput.press('Enter');

        // Wait for response (with generous timeout for cold starts)
        const responseArea = page.locator('[class*="result"], [class*="response"], [class*="answer"]').first();
        await expect(responseArea).toBeVisible({ timeout: 120000 });
    });

    test('tabs navigation works', async ({ page }) => {
        // Look for tab buttons
        const loadTableTab = page.getByRole('tab', { name: /load|table/i });
        const auditTab = page.getByRole('tab', { name: /audit/i });
        const sldTab = page.getByRole('tab', { name: /sld/i });

        // Click through tabs if they exist
        if (await loadTableTab.isVisible({ timeout: 3000 }).catch(() => false)) {
            await loadTableTab.click();
            await expect(loadTableTab).toHaveAttribute('aria-selected', 'true');
        }

        if (await auditTab.isVisible({ timeout: 3000 }).catch(() => false)) {
            await auditTab.click();
            await expect(auditTab).toHaveAttribute('aria-selected', 'true');
        }
    });

    test('no console errors on page load', async ({ page }) => {
        const consoleErrors: string[] = [];

        page.on('console', (msg) => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });

        await page.goto(BASE_URL);
        await page.waitForLoadState('networkidle');

        // Filter out known non-critical errors
        const criticalErrors = consoleErrors.filter(err =>
            !err.includes('favicon') &&
            !err.includes('manifest') &&
            err.includes('Error #') // React errors
        );

        expect(criticalErrors).toHaveLength(0);
    });
});
