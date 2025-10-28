# SPSCon 2025 Railway Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Railway account (free tier available)
- GitHub repository with your code
- Local development environment set up

### Railway Setup

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

## 📁 Project Structure

```
SPSCon-2025/
├── app.py                      # Main Flask application
├── models.py                   # Database models
├── config.py                   # Configuration classes
├── deploy.py                   # Database migration script
├── pre_deploy.sh              # Pre-deployment setup script
├── export_data.py             # Data export utility
├── seed_data.py               # Database seeding
├── requirements.txt           # Python dependencies
├── Procfile                   # Railway process definition
├── railway.toml              # Railway configuration
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── static/                   # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── qrcodes/
├── templates/                # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   ├── poster_detail.html
│   └── ...
└── routes/                   # API routes
    └── api.py
```

## 🗄️ Database Schema

### Core Models
- **User**: User accounts with authentication
- **Poster**: Conference poster data
- **Favorite**: User poster favorites
- **Visit**: User poster visits
- **PresenterStatus**: Presenter availability status

### Key Relationships
- Users can favorite multiple posters
- Users can visit multiple posters
- Posters can have assigned presenters
- Presenters can update their availability status

## 🔧 Development

### Tech Stack
- **Backend**: Flask 3.1+, SQLAlchemy, Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Database**: SQLite (development), PostgreSQL (production)
- **Styling**: Bootstrap 5 with custom CSS
- **Charts**: D3.js for data visualization

### Development Setup

1. **Clone and setup:**
   ```bash
   git clone <your-repo>
   cd SPSCon-2025
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database:**
   ```bash
   python deploy.py
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Access the app:**
   - Open http://localhost:5000
   - Browse posters, create favorites, mark visits

## 🚀 Deployment

### Production Deployment

1. **Set production environment variables:**
   ```bash
   FLASK_ENV=production
   FLASK_DEBUG=False
   DATABASE_URL=postgresql://user:pass@host:port/dbname
   SECRET_KEY=your-production-secret-key
   ```

2. **Deploy to Railway:**
   - Push code to GitHub
   - Railway automatically detects changes and deploys
   - The `pre_deploy.sh` script handles setup
   - The `deploy.py` script handles database migration

### Deployment Process

1. **Pre-deployment (`pre_deploy.sh`):**
   - Checks environment configuration
   - Installs/upgrades dependencies
   - Runs database migration
   - Creates necessary directories
   - Sets file permissions

2. **Database Migration (`deploy.py`):**
   - Backs up existing data (if any)
   - Creates/updates database schema
   - Restores data from backup
   - Verifies all tables exist

3. **Application Start:**
   - Flask application starts on Railway's PORT
   - Health checks ensure application is running

## 📊 Data Migration Strategy

### Option A: Fresh Start (Recommended)
- Deploy with empty PostgreSQL database
- Use admin panel to import Excel data
- All existing local data remains in SQLite

### Option B: Migrate Existing Data
1. **Export local data:**
   ```bash
   python export_data.py
   ```

2. **Deploy to Railway**

3. **Import data via admin panel or API**

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Run specific test file
python -m pytest tests/test_poster.py
```

### Test Structure
```
tests/
├── conftest.py              # Test configuration
├── test_auth.py            # Authentication tests
├── test_poster.py          # Poster functionality tests
├── test_search.py          # Search functionality tests
└── test_api.py             # API endpoint tests
```

## 📈 Monitoring & Maintenance

### Health Checks
- Railway automatically monitors your app via the `/` endpoint
- Check logs regularly in the Railway dashboard

### Database Backups
- Railway PostgreSQL includes automatic backups
- Export data periodically using `export_data.py`
- Set up automated backups (advanced)

### Updates & Redeployments
- Push changes to GitHub → automatic deployment
- Monitor logs during deployment
- Test functionality after each deployment

## 🔧 Configuration

### Required Environment Variables

Create a `.env` file in the project root:

```bash
# Flask Configuration
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=1

# Database Configuration
DATABASE_URL=sqlite:///spscon.db

# Server Configuration
PORT=5000
```

### Railway Environment Variables

```bash
# Production
SECRET_KEY=your-production-secret-key
FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_URL=postgresql://... (auto-provided by Railway)
```

## 🛠️ Troubleshooting

### Common Issues

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
- Consider upgrading to paid plan
- Optimize database queries if needed

### Getting Help
- Check Railway documentation: [docs.railway.app](https://docs.railway.app)
- Railway Discord community
- Check application logs in Railway dashboard

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: This README
- **Railway Support**: Railway dashboard support

## 🔮 Roadmap

### Upcoming Features
- **Mobile App**: React Native mobile application
- **Advanced Analytics**: More sophisticated poster analytics
- **Real-time Updates**: WebSocket integration for live updates
- **API Access**: Public API for third-party integrations
- **Enhanced Search**: Full-text search with Elasticsearch
- **Social Features**: Enhanced community features

### Version History
- **v1.0.0** - Initial release with core features
- **v1.1.0** - Added favorites and visited functionality
- **v1.2.0** - Enhanced search and filtering
- **v1.3.0** - Railway deployment optimization

---

**Made with ❤️ for SPSCon 2025**

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Flask** community for the excellent web framework
- **Railway** for seamless deployment platform
- **Bootstrap** for the beautiful CSS framework
- **D3.js** for data visualization capabilities
