# Repository Guidelines

## Odoo 18 Important Changes

### View Terminology
- **Tree views are now called List views** in Odoo 18
- Use `view_type='list'` instead of `view_type='tree'`

### Attribute Changes
- **Use direct attributes instead of attrs**
- Old: `attrs="{'invisible': [('field', '=', value)]}"`
- New: `invisible="field == value"`
- Applies to: invisible, readonly, required attributes

## Module Installation
- **Always use curl/JSON-RPC for module installation**
- Do NOT use command line with -u flag
- Check logs after installation to verify success

## Environment Setup

### Virtual Environment
Always activate the virtual environment before running Python commands:
```bash
source venv/bin/activate
```

## Running Odoo

### Standard Development Command
The server is typically run with streaming output and logging:
```bash
./odoo-bin -c odoo.conf -d salewise --dev=all --limit-time-cpu=600 --limit-time-real=1200 2>&1 | tee -a odoo.log
```

### Important Notes
- The server is usually already running - check `odoo.log` first
- Logs are streamed to console AND saved to `odoo.log`
- Use `tail -f odoo.log` to monitor logs if needed

## Checking Server Status

### Before Starting Odoo
1. Check if server is already running:
```bash
ps aux | grep -E 'odoo|python.*odoo' | grep -v grep
```

2. Check the log file for recent activity:
```bash
tail -100 odoo.log
```

3. Check if port 8069 is in use:
```bash
netstat -tulpn 2>/dev/null | grep 8069 || lsof -i :8069
```

## Interacting with Odoo

### Using JSON-RPC with curl

#### Authentication
```bash
curl -X POST http://localhost:8069/web/session/authenticate \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "db": "salewise",
      "login": "admin",
      "password": "admin"
    },
    "id": 1
  }' -c cookies.txt
```

#### Module Installation Example
```bash
# First search for module ID
curl -X POST http://localhost:8069/web/dataset/call_kw/ir.module.module/search_read \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "model": "ir.module.module",
      "method": "search_read",
      "args": [],
      "kwargs": {
        "fields": ["id", "name", "state"],
        "domain": [["name", "=", "module_name"]],
        "context": {"lang": "en_US", "tz": "Europe/Brussels", "uid": 2}
      }
    },
    "id": 2
  }'

# Then install using the module ID
curl -X POST http://localhost:8069/web/dataset/call_kw/ir.module.module/button_immediate_install \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "model": "ir.module.module",
      "method": "button_immediate_install",
      "args": [[MODULE_ID]],
      "kwargs": {
        "context": {"lang": "en_US", "tz": "Europe/Brussels", "uid": 2}
      }
    },
    "id": 3
  }'
```

### Complex Operations with Python Scripts

For complex operations, create temporary Python scripts:

1. Create script in temp directory:
```bash
mkdir -p /tmp/odoo_scripts
```

2. Write Python script:
```python
#!/usr/bin/env python3
import xmlrpc.client
import sys

# Connection details
url = 'http://localhost:8069'
db = 'salewise'
username = 'admin'
password = 'admin'

# Authenticate
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

if uid:
    # Get object proxy
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    
    # Your operations here
    # Example: Search for modules
    module_ids = models.execute_kw(
        db, uid, password,
        'ir.module.module', 'search',
        [[['name', '=', 'base']]]
    )
    print(f"Found modules: {module_ids}")
else:
    print("Authentication failed")
    sys.exit(1)
```

3. Execute and clean up:
```bash
cd /tmp/odoo_scripts
python3 script_name.py
rm script_name.py
```

## Database Operations

### Direct Database Access
Database credentials are in `odoo.conf`:
- Host: localhost
- Port: 5432
- User: salewise
- Password: salewise
- Database: salewise

Connect directly:
```bash
PGPASSWORD=salewise psql -h localhost -U salewise -d salewise
```

### Checking Database Status
```bash
PGPASSWORD=salewise psql -h localhost -U salewise -d salewise -c "\dt" | head -20
```

### Killing Database Connections
If database is locked by other sessions:
```bash
# Find Odoo processes
ps aux | grep -E 'odoo|python.*odoo' | grep -v grep

# Kill specific process
kill -9 [PID]

# Or kill all database connections (requires superuser)
PGPASSWORD=salewise psql -h localhost -U salewise -d salewise -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'salewise' AND pid <> pg_backend_pid();"
```

## Module Development

### Module Structure
Custom modules are located in `/home/tishmen/salewise-odoo/custom/`

### After Module Changes
1. Restart Odoo with update flag:
```bash
./odoo-bin -c odoo.conf -d salewise -u module_name --stop-after-init
```

2. Or upgrade via UI/API if server is running

### Adding OCA Modules
1. Download to OCA folder:
```bash
cd /home/tishmen/salewise-odoo/OCA
wget [module_url]
# Extract specific module only
```

2. Add to dependencies in `custom/salewise_bootstrap/__manifest__.py`

## Debugging

### Check Logs
```bash
# View recent logs
tail -100 odoo.log

# Search for errors
grep -i error odoo.log | tail -20

# Monitor logs in real-time
tail -f odoo.log
```

### Common Issues

#### Port Already in Use
```bash
# Find process using port 8069
lsof -i :8069
# or
netstat -tulpn | grep 8069
```

#### Module Not Found
- Check addons_path in odoo.conf
- Verify module is in correct directory
- Check __manifest__.py is valid

## Git Workflow

### Before Committing
1. Check git status
2. Review changes with `git diff`
3. Ensure tests pass (if applicable)
4. Check that Odoo server starts without errors

### Commit Message Format
```
Short description of change

- Detail 1
- Detail 2

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Important Files

- Configuration: `/home/tishmen/salewise-odoo/odoo.conf`
- Logs: `/home/tishmen/salewise-odoo/odoo.log`
- Bootstrap module: `/home/tishmen/salewise-odoo/custom/salewise_bootstrap/`
- Virtual environment: `/home/tishmen/salewise-odoo/venv/`

## Testing

### Running Tests
```bash
./odoo-bin -c odoo.conf -d salewise --test-enable --stop-after-init -i module_name
```

### Linting
```bash
# If configured, run linters
ruff check .
# or
pylint custom/
```

## Performance

### CPU and Time Limits
Standard limits for development:
- `--limit-time-cpu=600` (10 minutes CPU time)
- `--limit-time-real=1200` (20 minutes real time)

## Notes

- Always check if server is already running before starting
- Use virtual environment for all Python operations
- Clean up temporary files after script execution
- Monitor log file for errors and debugging
- Database credentials: username=salewise, password=salewise, db=salewise
- Admin credentials: username=admin, password=admin

