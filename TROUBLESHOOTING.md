# Troubleshooting Guide

## HTTPS Errors on Development Server

If you see errors like "You're accessing the development server over HTTPS, but it only supports HTTP", here are the solutions:

### **Quick Fixes**

1. **Clear Browser Data**
   ```
   - Open your browser
   - Press Ctrl+Shift+Delete
   - Clear browsing data, cookies, and cache
   - Restart browser
   ```

2. **Use Different Port**
   ```bash
   python manage.py runserver 127.0.0.1:8002
   ```

3. **Use Incognito/Private Mode**
   - Open browser in private/incognito mode
   - Visit http://127.0.0.1:8000 (not https)

4. **Disable HTTPS Redirects**
   - Type `chrome://net-internals/#hsts` in Chrome
   - Delete security policies for localhost and 127.0.0.1

### **Common Causes**

1. **Browser Cache**: Browser remembering HTTPS redirect
2. **Antivirus Software**: Some antivirus software intercepts connections
3. **Proxy Settings**: Corporate or system proxy forcing HTTPS
4. **Browser Extensions**: Security extensions forcing HTTPS

### **Solutions by Browser**

#### Chrome/Edge
```
1. Go to chrome://settings/security
2. Disable "Always use secure connections"
3. Clear HSTS settings: chrome://net-internals/#hsts
4. Delete domain security policies for localhost
```

#### Firefox
```
1. Go to about:config
2. Search for security.tls.insecure_fallback_hosts
3. Add "localhost,127.0.0.1" to the list
```

### **Alternative Startup Methods**

#### Method 1: Different Port
```bash
python manage.py runserver 0.0.0.0:8002
```

#### Method 2: Safe Startup Script
```bash
python start_server.py
```

#### Method 3: Manual Check
```bash
# Test if server starts
python manage.py check
python manage.py runserver --help
```

### **Network Diagnostics**

#### Check Port Usage
```bash
# Windows
netstat -an | findstr :8000

# Check if something is using the port
```

#### Test Connection
```bash
# Use curl if available
curl -v http://127.0.0.1:8000/

# Or use PowerShell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -UseBasicParsing
```

### **Environment Issues**

#### Check Environment Variables
```bash
# Verify .env file
type .env

# Check if variables are loaded
python -c "from decouple import config; print(config('SECRET_KEY'))"
```

#### Verify Dependencies
```bash
pip list | findstr Django
pip install -r requirements.txt --upgrade
```

### **Security Software**

Some antivirus software can interfere:

1. **Windows Defender**: May scan connections
2. **Kaspersky**: Has web protection features
3. **Norton**: May redirect connections
4. **Corporate Firewalls**: May force HTTPS

**Solution**: Temporarily disable web protection or add localhost to exceptions.

### **Development Workarounds**

#### 1. Use Different IP
```bash
python manage.py runserver 192.168.1.100:8000
```

#### 2. Use Different Domain
Add to `C:\Windows\System32\drivers\etc\hosts`:
```
127.0.0.1 jiyash.local
```

Then use: `http://jiyash.local:8000`

#### 3. Use Docker (Advanced)
```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### **Production Notes**

The HTTPS errors only affect development. In production:

1. Use proper web server (Nginx/Apache)
2. Configure SSL certificates
3. Use HTTPS properly
4. Set `SECURE_SSL_REDIRECT=True`

### **Still Having Issues?**

1. **Check Windows Event Logs**
2. **Disable all browser extensions**
3. **Try a different browser**
4. **Use Windows Subsystem for Linux (WSL)**
5. **Contact system administrator if on corporate network**

### **Emergency Fallback**

If nothing works, you can still develop by:

1. Making changes to code
2. Running tests: `python manage.py test`
3. Using Django shell: `python manage.py shell`
4. Accessing admin via different port: `python manage.py runserver 127.0.0.1:9000`

The website functionality is not affected - this is purely a development server access issue.
