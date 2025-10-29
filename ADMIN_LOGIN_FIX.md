# 🔐 Admin Login Fix

## Quick Fix (2 minutes)

### Step 1: SSH into Railway
```bash
railway ssh
```

### Step 2: Reset Admin Password
```bash
python3 reset_admin_password.py
```

### Step 3: Try Login Again
- Go to your site's `/login`
- Username: `admin`
- Password: `Admin97034122!`
- Should work now! ✅

---

## Alternative: Deploy Script

If you can't SSH, add the script and redeploy:

```bash
git add reset_admin_password.py ADMIN_LOGIN_FIX.md
git commit -m "Add admin password reset script"
git push origin release
```

Then SSH in and run it after deployment.

---

## What This Does

1. Finds admin user (or creates if missing)
2. Sets password to `Admin97034122!`
3. Verifies password works
4. Shows admin status

---

## Expected Output

```
✅ Admin password reset successfully!
   Username: admin
   Password: Admin97034122!
   Email: admin@spscon2025.com
   Is Admin: True
✅ Password verification: SUCCESS
```

---

## Why Login Failed

Possible reasons:
1. Admin user doesn't exist yet
2. Password was corrupted during migration
3. User exists but with wrong password

This script fixes all of these!

---

## After Fix Works

You can then:
- ✅ Log in as admin
- ✅ Access `/admin` panel
- ✅ Manage all features

---

**Run the script on Railway now and you'll be able to log in!** 🚀

