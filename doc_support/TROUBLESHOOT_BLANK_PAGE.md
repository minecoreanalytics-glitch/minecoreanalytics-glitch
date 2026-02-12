# Troubleshooting Blank Page

The app is loading correctly on the server side. Here's how to diagnose the issue:

## Step 1: Open Browser Developer Tools

1. Open http://localhost:3000/ in your browser
2. Press `F12` (Windows/Linux) or `Cmd + Option + I` (Mac)
3. Go to the **Console** tab

## Step 2: Look for Errors

Check for any red error messages. Common issues:

### If you see: "Failed to fetch" or CORS errors
The frontend can't reach the backend. This is normal - just continue.

### If you see: React/JavaScript errors
Take a screenshot and share it - there may be a code issue.

### If you see: No errors at all
The page may actually be rendering but with issues.

## Step 3: Check the Elements

1. In Developer Tools, go to the **Elements** tab (or **Inspector** in Firefox)
2. Look for `<div id="root">`
3. Expand it - does it have content inside?

**If YES (has content):**
- The app is rendering but may have CSS issues
- Try zooming out (Cmd/Ctrl + minus key)
- Check if elements are there but invisible

**If NO (empty):**
- React isn't rendering - continue to Step 4

## Step 4: Force Clear Everything

Run these commands in the browser console:

```javascript
// Clear all cache and storage
localStorage.clear();
sessionStorage.clear();
location.reload(true);
```

Or do a hard refresh:
- **Mac**: `Cmd + Shift + R`
- **Windows**: `Ctrl + Shift + F5`

## Step 5: Try Incognito/Private Mode

1. Open a new Incognito/Private window
2. Navigate to http://localhost:3000/
3. Does it work now?

If it works in incognito, the issue is cached data - clear your browser cache.

## Step 6: Check Network Tab

1. In Developer Tools, go to **Network** tab
2. Refresh the page
3. Look for files loading:
   - `index.tsx` - should be 200 OK
   - `App.tsx` - should be 200 OK
   - React dependencies - should be 200 OK

**If any files show errors:**
- 404 = file not found (code issue)
- 500 = server error (backend issue)
- ERR_CONNECTION_REFUSED = server not running

## Manual Verification

Run these commands in your terminal to verify everything is working:

```bash
# Check frontend is serving
curl -I http://localhost:3000/

# Check JavaScript is loading
curl -s http://localhost:3000/index.tsx | head -5

# Check backend is working
curl http://localhost:8000/api/v1/health

# Check integrations endpoint
curl http://localhost:8000/api/v1/integrations/status
```

All should return 200 OK responses.

## Alternative: Try Different Browser

If you're using Safari, try Chrome or Firefox
If you're using Chrome, try Firefox or Edge

Sometimes browser-specific issues occur.

## Still Not Working?

Take screenshots of:
1. **Console tab** (showing any errors)
2. **Elements tab** (showing the #root div)
3. **Network tab** (showing loaded files)

And share them so I can help diagnose further.

## Quick Test: API Documentation

The backend has a built-in documentation page. Try opening:

http://localhost:8000/docs

This should show a Swagger UI page with all the API endpoints. If this works, the backend is fine and the issue is frontend-only.
