# Railway Deployment Checklist

## Pre-Deployment
- [ ] Code committed to GitHub repository
- [ ] All tests passing locally
- [ ] Environment variables documented
- [ ] Database migration scripts tested
- [ ] Backup of local data created (if needed)

## Railway Setup
- [ ] Railway account created
- [ ] New project created from GitHub repo
- [ ] PostgreSQL database service added
- [ ] Environment variables configured:
  - [ ] `SECRET_KEY` (secure random key)
  - [ ] `FLASK_ENV=production`
  - [ ] `FLASK_DEBUG=False`
  - [ ] `DATABASE_URL` (auto-provided by Railway)

## Deployment
- [ ] Initial deployment successful
- [ ] Database migration completed
- [ ] Application accessible via Railway URL
- [ ] Health check passing

## Post-Deployment Testing
- [ ] Homepage loads correctly
- [ ] User registration works
- [ ] User login works
- [ ] Poster search functionality works
- [ ] Poster detail pages load
- [ ] Favorites/visited functionality works
- [ ] Admin panel accessible (if applicable)
- [ ] QR codes generate correctly

## Data Migration (if applicable)
- [ ] Local data exported
- [ ] Data imported to Railway database
- [ ] Data integrity verified
- [ ] User accounts working
- [ ] Poster data complete

## Monitoring
- [ ] Railway logs monitored
- [ ] Performance metrics checked
- [ ] Error rates acceptable
- [ ] Database connections stable

## Optional Enhancements
- [ ] Custom domain configured
- [ ] SSL certificate active
- [ ] Backup strategy implemented
- [ ] Monitoring alerts set up

## Rollback Plan
- [ ] Previous version tagged
- [ ] Database backup available
- [ ] Rollback procedure documented
- [ ] Team notified of deployment

---

## Quick Commands

### Generate secure SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Export local data:
```bash
python export_data.py
```

### Check deployment status:
```bash
# Check Railway logs in dashboard
# Verify health check endpoint responds
```

### Test locally with production settings:
```bash
export FLASK_ENV=production
export FLASK_DEBUG=False
python app.py
```
