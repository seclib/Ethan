package logger

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"time"
)

// Level represents log severity
type Level int

const (
	Debug Level = iota
	Info
	Warn
	Error
	Fatal
)

// Logger provides structured logging
type Logger struct {
	level  Level
	output io.Writer
}

// New creates a new Logger
func New(level Level) *Logger {
	return &Logger{
		level:  level,
		output: os.Stdout,
	}
}

// Info logs an info message
func (l *Logger) Info(format string, args ...interface{}) {
	l.log(Info, format, args...)
}

// Warn logs a warning message
func (l *Logger) Warn(format string, args ...interface{}) {
	l.log(Warn, format, args...)
}

// Error logs an error message
func (l *Logger) Error(format string, args ...interface{}) {
	l.log(Error, format, args...)
}

// Fatal logs a fatal message and exits
func (l *Logger) Fatal(format string, args ...interface{}) {
	l.log(Fatal, format, args...)
	os.Exit(1)
}

// log writes a structured log entry
func (l *Logger) log(level Level, format string, args ...interface{}) {
	if level < l.level {
		return
	}

	entry := map[string]interface{}{
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"level":     levelString(level),
		"message":   fmt.Sprintf(format, args...),
	}

	data, _ := json.Marshal(entry)
	fmt.Fprintln(l.output, string(data))
}

// levelString converts Level to string
func levelString(level Level) string {
	switch level {
	case Debug:
		return "debug"
	case Info:
		return "info"
	case Warn:
		return "warn"
	case Error:
		return "error"
	case Fatal:
		return "fatal"
	default:
		return "unknown"
	}
}