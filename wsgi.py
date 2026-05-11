from app import app

# Vercel requires the application object to be exposed as 'app'
# Do NOT include app.run() here as it causes the 'FUNCTION_INVOCATION_FAILED' crash.
app = app

