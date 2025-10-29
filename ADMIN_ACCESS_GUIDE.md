# 🔐 Admin Access Guide - SPSCon 2025

## Overview
Secure admin system with proper authentication and authorization using `is_admin` boolean field.

---

## 🚀 Quick Start

### Default Admin Account (Auto-Created on Deployment)

**Credentials:**
- **URL**: `https://your-domain.com/admin`
- **Username**: `admin`
- **Password**: `Admin97034122!`
- **Email**: `admin@spscon2025.com`

The system automatically creates this admin account when the database is set up. You can log in immediately after deployment!

---

## 🔒 Security Features

### 1. `is_admin` Boolean Field
- New `is_admin` column added to User model (default: `False`)
- Stored in database, not hardcoded
- Proper authorization checks on all admin routes

### 2. `@admin_required` Decorator
All admin routes are protected with:
```python
@admin_required
def admin_panel():
    ...
```

This decorator:
- ✅ Checks if user is logged in
- ✅ Checks if `current_user.is_admin == True`
- ✅ Returns 403 Forbidden if not admin
- ✅ Redirects to login if not authenticated

### 3. Protected Routes
All these routes require admin privileges:
- `/admin` - Admin panel dashboard
- `/admin/assign-presenter` - Assign posters
- `/admin/auto-assign` - Auto-assign function
- `/admin/unassign-all` - Bulk unassign
- `/api/admin/change-requests` - View all change requests
- `/api/admin/change-request/:id/approve` - Approve requests
- `/api/admin/change-request/:id/deny` - Deny requests

---

## 🎯 How to Access Admin Panel

### Step 1: Log In
1. Go to: `https://your-domain.com/login`
2. Enter credentials:
   - Username: `admin`
   - Password: `Admin97034122!`
3. Click "Sign In"

### Step 2: Access Admin Panel
1. Once logged in, go to: `https://your-domain.com/admin`
2. Or click "Admin" in the user dropdown menu (top right)

### What You'll See
- **Dashboard Tab**: System statistics and quick actions
- **Change Requests Tab**: Review and approve/deny user change requests
- **Users Tab**: View all registered users and their activity
- **Posters Tab**: Manage poster assignments

---

## 👥 Making Other Users Admin

### Option 1: Using the `make_admin.py` Script (Recommended)

Run this command on your server:

```bash
# By email
python make_admin.py john@example.com

# By username
python make_admin.py john

# List all current admins
python make_admin.py --list
```

**Example Output:**
```
✅ SUCCESS! User 'john' (john@example.com) is now an admin!

They can now access the admin panel at: /admin
```

### Option 2: Via Database (Direct)

If you have direct database access:

```sql
-- Make a user admin
UPDATE user SET is_admin = TRUE WHERE username = 'john';

-- Check who is admin
SELECT username, email, is_admin FROM user WHERE is_admin = TRUE;

-- Remove admin privileges
UPDATE user SET is_admin = FALSE WHERE username = 'john';
```

### Option 3: Via Python Shell (Railway)

On Railway, you can use the Python shell:

```bash
# SSH into Railway container
railway ssh

# Run Python
python3

# Then in Python:
from app import create_app
from models import db, User

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='john').first()
    user.is_admin = True
    db.session.commit()
    print(f"✅ {user.username} is now an admin!")
```

---

## 🔄 Migration Details

### Migration 003: Add is_admin Column

The system automatically adds the `is_admin` column on deployment:

```sql
ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL;
```

**What Happens:**
1. Migration system checks if column exists
2. If not, adds it with `DEFAULT FALSE`
3. All existing users get `is_admin = False`
4. Admin user is created/updated with `is_admin = True`
5. Migration is marked as complete

**Safe to Run Multiple Times:**
- If column already exists, migration is skipped
- Existing admin users keep their privileges
- No data loss

---

## 📋 Admin Capabilities

### Dashboard
- View system statistics
- See pending change request count
- Quick access to all features
- Progress tracking for poster assignments

### Change Request Management
- **View All Requests**: Filter by pending/approved/denied
- **Review Details**: See what user wants to change and why
- **Approve**: Automatically updates user data in database
- **Deny**: Add reason for denial, notifies user
- **Admin Notes**: Add internal notes to requests

### User Management
- View all registered users
- See user activity (favorites, visits)
- See assigned posters per user
- View registration dates

### Poster Management
- Assign/unassign presenters to posters
- Auto-assign by name matching
- Bulk unassign all
- See assignment status

---

## 🛡️ Security Best Practices

### 1. Change Default Password IMMEDIATELY

After first login:
1. Go to Settings
2. Request a password change via change request
3. Approve it yourself
4. Or use the database to update it directly

To change password via script:
```python
from app import create_app
from models import db, User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.set_password('YourNewSecurePassword123!')
    db.session.commit()
    print("✅ Password updated!")
```

### 2. Limit Admin Accounts
- Only give admin privileges to trusted users
- Remove admin from users who no longer need it
- Regularly audit who has admin access: `python make_admin.py --list`

### 3. Monitor Admin Activity
- Check change request history
- Review who approved/denied requests
- Watch for suspicious activity

### 4. Use Strong Passwords
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Don't reuse passwords
- Consider using a password manager

---

## 🔍 Troubleshooting

### "403 Forbidden" When Accessing /admin

**Problem**: User is not an admin

**Solutions:**
1. Check if user has admin privileges:
   ```bash
   python make_admin.py --list
   ```

2. Make yourself admin:
   ```bash
   python make_admin.py your@email.com
   ```

3. Verify in database:
   ```sql
   SELECT username, email, is_admin FROM user WHERE username = 'your_username';
   ```

### Can't Log In as Admin

**Problem**: Password might be wrong or account doesn't exist

**Solutions:**
1. Reset password:
   ```python
   from app import create_app
   from models import db, User
   
   app = create_app()
   with app.app_context():
       admin = User.query.filter_by(username='admin').first()
       if admin:
           admin.set_password('Admin97034122!')
           db.session.commit()
           print("✅ Password reset!")
       else:
           print("❌ Admin user doesn't exist!")
   ```

2. Re-run deployment script to recreate admin:
   ```bash
   python deploy.py
   ```

### Admin Menu Not Showing

**Problem**: Frontend doesn't know user is admin

**Check:**
1. Is `is_admin` field in database?
   ```sql
   DESCRIBE user;
   ```

2. Did migration 003 run?
   ```sql
   SELECT * FROM migrations WHERE migration_name = '003_add_is_admin';
   ```

3. Re-run migrations:
   ```bash
   python migrations.py
   ```

---

## 📊 Database Schema

### User Table (Updated)

```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(120) UNIQUE NOT NULL,
    username VARCHAR(80) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,  -- NEW!
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎯 Common Admin Tasks

### Task 1: Approve a User's Email Change
1. Log in to `/admin`
2. Go to "Change Requests" tab
3. Click "Review" on the request
4. Read their reason
5. Add admin notes (optional)
6. Click "Approve"
7. ✅ User's email is updated automatically!

### Task 2: Assign Posters to Users
1. Go to "Posters" tab
2. Find the poster
3. Select user from dropdown
4. Click "✓" button
5. ✅ User can now manage that poster!

### Task 3: View User Activity
1. Go to "Users" tab
2. See all registered users
3. View their:
   - Favorites count
   - Visits count
   - Assigned posters
   - Registration date

### Task 4: Bulk Auto-Assign
1. Go to "Dashboard" tab
2. Click "Auto-assign Posters"
3. System matches users to posters by first/last name
4. ✅ All matching posters get assigned!

---

## 📞 Support

### Check Logs
Railway logs will show:
- ✅ Admin user creation
- ✅ Migration status
- ❌ Any errors

### Manual Verification
```bash
# Check if admin exists
python3 -c "from app import create_app; from models import db, User; app = create_app(); app.app_context().push(); admin = User.query.filter_by(username='admin').first(); print(f'Admin exists: {admin is not None}'); print(f'Is admin: {admin.is_admin if admin else False}')"
```

---

## 🎉 Summary

### Access Admin Panel:
1. **URL**: `/admin`
2. **Username**: `admin`
3. **Password**: `Admin97034122!`
4. **Change password ASAP!**

### Make Others Admin:
```bash
python make_admin.py their@email.com
```

### Security:
- ✅ Proper `is_admin` field in database
- ✅ `@admin_required` decorator on all routes
- ✅ Auto-created on deployment
- ✅ Proper authorization checks

**You're all set! 🚀**

