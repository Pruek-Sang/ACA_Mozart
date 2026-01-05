/**
 * Remote Logger (Aura's Eyes)
 * Sends frontend logs to the backend for Cloud Logging ingestion.
 */

const API_LOG_ENDPOINT = '/api/v1/logs';

type LogLevel = 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';

interface LogContext {
    [key: string]: any;
}

class RemoteLogger {
    private static instance: RemoteLogger;
    private isDev: boolean;

    private constructor() {
        this.isDev = import.meta.env.DEV;
    }

    public static getInstance(): RemoteLogger {
        if (!RemoteLogger.instance) {
            RemoteLogger.instance = new RemoteLogger();
        }
        return RemoteLogger.instance;
    }

    /**
     * Send log to backend
     */
    private async sendLog(level: LogLevel, message: string, context: LogContext = {}) {
        // Always print to console
        const timestamp = new Date().toISOString();
        const consoleMsg = `[${level}] ${message}`;

        if (level === 'ERROR') {
            console.error(consoleMsg, context);
        } else if (level === 'WARNING') {
            console.warn(consoleMsg, context);
        } else {
            console.log(consoleMsg, context);
        }

        // Prepare context with default metadata
        const enrichedContext = {
            ...context,
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp
        };

        try {
            // Fire and forget - don't await response to avoid blocking UI
            fetch(API_LOG_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    level,
                    message,
                    context: enrichedContext
                })
            }).catch(err => {
                // Fallback if backend logging fails (don't create infinite loop)
                console.warn('Failed to send log to backend:', err);
            });
        } catch (e) {
            // Ignore network errors for logging
        }
    }

    public info(message: string, context?: LogContext) {
        this.sendLog('INFO', message, context);
    }

    public warn(message: string, context?: LogContext) {
        this.sendLog('WARNING', message, context);
    }

    public error(message: string, context?: LogContext) {
        this.sendLog('ERROR', message, context);
    }

    public debug(message: string, context?: LogContext) {
        if (this.isDev) {
            this.sendLog('DEBUG', message, context);
        }
    }
}

export const logger = RemoteLogger.getInstance();
