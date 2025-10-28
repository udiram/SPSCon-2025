# Railway Deployment Guide for SPSCon 2025

## 🚀 Quick Start

### 1. Prerequisites
- Railway account (free tier available)
- GitHub repository with your code
- Local development environment set up

### 2. Railway Setup

#### Step 1: Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select your SPSCon-2025 repository

#### Step 2: Add PostgreSQL Database
1. In your Railway project dashboard
2. Click "New" → "Database" → "PostgreSQL"
3. Railway will automatically create a `DATABASE_URL` environment variable

#### Step 3: Configure Environment Variables
Go to your service settings and add these environment variables:

```bash
# Required
SECRET_KEY=your-super-secure-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=False

# Optional
CUSTOM_DOMAIN=your-domain.com
```

**Important:** Generate a secure SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Data Migration Strategy

#### Option A: Fresh Start (Recommended for first deployment)
- Deploy with empty database
- Use the admin panel to import your Excel data
- All existing local data will be preserved in your local SQLite file

#### Option B: Migrate Existing Data
If you have important data in your local database:

1. **Export your local data:**
   ```bash
   python -c "
   from app import create_app
   from models import db, Poster, User
   import json
   
   app = create_app()
   with app.app_context():
       posters = [{'id': p.id, 'poster_number': p.poster_number, 'session': p.session, 'first_name': p.first_name, 'last_name': p.last_name, 'institution': p.institution, 'title': p.title, 'category': p.category, 'tags': p.tags} for p in Poster.query.all()]
       users = [{'id': u.id, 'username': u.username, 'email': u.email, 'first_name': u.first_name, 'last_name': u.last_name, 'is_admin': u.is_admin} for u in User.query.all()]
       
       with open('local_data_export.json', 'w') as f:
           json.dump({'posters': posters, 'users': users}, f, indent=2)
   "
   ```

2. **Deploy to Railway**

3. **Import data via admin panel** (if you have admin access) or use the API

### 4. Deployment Process

#### Automatic Deployment
Railway will automatically deploy when you push to your main branch.

#### Manual Deployment
1. Push your code to GitHub
2. Railway will detect changes and redeploy automatically
3. The `start.sh` script will handle database migration

### 5. Post-Deployment Steps

#### Verify Deployment
1. Check your Railway service logs for any errors
2. Visit your Railway URL to ensure the app loads
3. Test key functionality:
   - User registration/login
   - Poster browsing
   - Search functionality
   - Admin panel (if applicable)

#### Set Up Custom Domain (Optional)
1. In Railway dashboard → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Set `CUSTOM_DOMAIN` environment variable

### 6. Monitoring & Maintenance

#### Health Checks
- Railway automatically monitors your app via the `/` endpoint
- Check logs regularly in the Railway dashboard

#### Database Backups
Railway PostgreSQL includes automatic backups, but you can also:
1. Use Railway's database backup feature
2. Export data periodically via admin panel
3. Set up automated backups (advanced)

#### Updates & Redeployments
- Push changes to GitHub → automatic deployment
- Monitor logs during deployment
- Test functionality after each deployment

### 7. Troubleshooting

#### Common Issues

**Database Connection Errors:**
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL service is running
- Ensure database migration completed successfully

**Import Errors:**
- Check all dependencies in `requirements.txt`
- Verify Python version compatibility
- Check build logs for missing packages

**Performance Issues:**
- Monitor Railway metrics
- Consider upgrading to paid plan for better resources
- Optimize database queries if needed

#### Getting Help
- Check Railway documentation: [docs.railway.app](https://docs.railway.app)
- Railway Discord community
- Check application logs in Railway dashboard

### 8. Environment-Specific Notes

#### Development vs Production
- Local: Uses SQLite (`sqlite:///spscon.db`)
- Railway: Uses PostgreSQL (automatic `DATABASE_URL`)
- Environment variables handle the difference automatically

#### Security Considerations
- Never commit `.env` files to Git
- Use strong, unique `SECRET_KEY` for production
- Enable HTTPS (automatic with Railway)
- Consider rate limiting for production use

### 9. Cost Optimization

#### Free Tier Limits
- Railway free tier: 500 hours/month
- PostgreSQL free tier: 1GB storage
- Monitor usage in Railway dashboard

#### Scaling Up
- Upgrade to paid plan for unlimited usage
- Add more resources as needed
- Consider caching strategies for high traffic

---

## 🎯 Success Checklist

- [ ] Railway project created
- [ ] PostgreSQL database added
- [ ] Environment variables configured
- [ ] Code deployed successfully
- [ ] App accessible via Railway URL
- [ ] Database migration completed
- [ ] Key functionality tested
- [ ] Custom domain configured (optional)
- [ ] Monitoring set up
- [ ] Backup strategy in place

## 📞 Support

For issues specific to this application:
1. Check the application logs in Railway dashboard
2. Verify environment variables are set correctly
3. Test locally first to isolate Railway-specific issues
4. Contact the development team with specific error messages
