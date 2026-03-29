# PlacetaID - Vercel Deployment Guide

## Overview

PlacetaID is now fully compatible with Vercel's serverless platform. This guide covers:
- Setting up prerequisites
- Configuring Vercel environment
- Connecting serverless databases
- Deploying to Vercel
- Debugging on Vercel

## Architecture for Vercel

```
PlacetaID on Vercel
├── Frontend (Static/Next.js)
│   ├── pages/
│   ├── components/
│   └── Hosted on Vercel Edge
├── Backend (Serverless Functions)
│   ├── api/index.py → Flask app handler
│   └── Python 3.11 runtime
├── Database (Serverless)
│   ├── Supabase (PostgreSQL) ← RECOMMENDED
│   ├── PlanetScale (MySQL)
│   └── MongoDB Atlas (NoSQL)
└── Cache (Serverless)
    └── Upstash Redis
```

## Prerequisites

1. **Vercel Account**: https://vercel.com (free tier available)
2. **Git Repository**: GitHub, GitLab, or Bitbucket
3. **Database**: Supabase or PlanetScale account
4. **Redis**: Upstash account for serverless Redis

## Step 1: Prepare Database

### Option A: Supabase (Recommended)

**Advantages:**
- Built-in PostgreSQL
- Real-time capabilities
- Free tier: 500MB storage
- Auth integration available

**Setup:**
1. Go to https://supabase.com
2. Create new project
3. Get connection string from Settings → Database → Connection string
4. Format: `postgresql://user:password@host/database?sslmode=require`

### Option B: PlanetScale

**Advantages:**
- MySQL 8.0+
- Compatible with existing schema
- Free tier: 5GB storage
- Faster for simple queries

**Setup:**
1. Go to https://planetscale.com
2. Create new database
3. Get connection string from Connect modal
4. Format: `mysql://user:password@host/database?sslMode=REQUIRE`

### Option C: MongoDB Atlas

**Advantages:**
- NoSQL flexibility
- Horizontal scaling
- Free tier: 512MB storage

**Setup:**
1. Go to https://www.mongodb.com/cloud/atlas
2. Create new cluster
3. Get connection string
4. Format: `mongodb+srv://user:password@cluster.mongodb.net/database`

## Step 2: Configure Redis

### Upstash Redis (Serverless)

1. Go to https://upstash.com
2. Create new Redis database
3. Select **Serverless** option
4. Copy connection string: `redis://default:password@host:port`

**In Vercel Settings:**
```
REDIS_URL=redis://default:password@host.upstash.io:12345
```

## Step 3: Generate Security Keys

Run these commands locally to generate keys:

```bash
# Generate JWT Secret (64 chars)
python -c "import secrets; print(secrets.token_hex(32))"

# Generate Master Encryption Key (base64-encoded 32 bytes)
python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"

# Generate DIP Hash Salt (32 chars)
python -c "import secrets; print(secrets.token_hex(16))"
```

Save these values safely - you'll need them for environment variables.

## Step 4: Deploy to Vercel

### Method 1: Using Vercel CLI (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy project
vercel

# Deploy to production
vercel --prod
```

### Method 2: GitHub Integration (Recommended for CI/CD)

1. Push code to GitHub repository
2. Go to https://vercel.com/import
3. Select "Import Git Repository"
4. Connect your GitHub account
5. Select PlacetaID repository
6. Vercel will auto-detect configurations

## Step 5: Configure Environment Variables

After creating project on Vercel:

1. Go to Project Settings
2. Select "Environment Variables"
3. Add from `.env.vercel.example`:

```
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=your-generated-key
MASTER_ENCRYPTION_KEY=your-generated-key
DIP_HASH_SALT=your-generated-salt
REDIS_URL=redis://...
ALLOWED_ORIGINS=https://yourdomain.com
```

**Important**: Set for all environments (Production, Preview, Development)

## Step 6: Database Initialization (First Time Only)

After first deployment, initialize schema:

```bash
# Using Vercel CLI
vercel env pull

# Run migrations
export DATABASE_URL=$(grep DATABASE_URL .env.local | cut -d '=' -f2)
flask db upgrade
```

Or use Supabase SQL editor to run schema from `database/schema.sql`.

## Step 7: Configure Custom Domain

1. Go to Project Settings → Domains
2. Add custom domain
3. Update DNS records per Vercel instructions
4. Update `ALLOWED_ORIGINS` environment variable

## Monitoring & Debugging

### View Logs

```bash
# Real-time logs
vercel logs

# With tail
vercel logs --tail
```

### Check Function Memory

Vercel dashboard → Deployments → Analytics tab

### Error Tracking

Optional: Add Sentry for error monitoring

```bash
# Set Sentry DSN
vercel env add SENTRY_DSN
```

## Limits on Vercel Free Tier

- **Function Duration**: 60 seconds max
- **Function Memory**: 1024 MB
- **Request Size**: 32 MB
- **Response Size**: 32 MB
- **Concurrency**: Based on plan

### Optimization Tips

```python
# In api/index.py - reduce startup time
from functools import lru_cache

@lru_cache(maxsize=1)
def get_app():
    # App initialization happens once
    from app import create_app
    return create_app('production')

app = get_app()
```

## Cost Estimation

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Vercel | 100 GB bandwidth/month | $20+/month |
| Supabase | 500 MB + 2GB bandwidth | Pay as you go |
| Upstash | 10,000 commands/day | $11/month |
| **Total** | **Free** | **~$40/month** |

## Troubleshooting

### Database Connection Failed
```
Error: 2003 "Can't connect to MySQL server"
```
**Solution:**
- Check DATABASE_URL format
- Verify IP allowlist (Supabase/PlanetScale)
- Test connection locally first

### Redis Connection Timeout
```
Error: ConnectionError: Error -2 connecting to redis
```
**Solution:**
- Verify REDIS_URL format
- Check Upstash credentials
- Increase timeout in config

### Environment Variables Not Loading
```
Error: KeyError: 'JWT_SECRET_KEY'
```
**Solution:**
- Redeploy after adding env vars: `vercel --prod`
- Check env var names exactly match
- Verify across all environments

### Function Timeout
```
Error: Function was interrupted (max duration exceeded)
```
**Solution:**
- Optimize database queries
- Add connection pooling
- Use caching via Redis
- Consider upgrading function memory

### Cold Start Performance
**Solution:**
- Remove unnecessary imports
- Use lazy loading in services
- Implement connection pooling
- Consider Pro/Enterprise plan for concurrency

## Advanced: Serverless Functions Optimization

### Connection Pooling

```python
# In models.py
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 1,
    'max_overflow': 0,  # Critical for serverless
}
```

### Cold Start Reduction

```python
# In api/index.py
import os
from functools import lru_cache

@lru_cache(maxsize=1)
def get_wsgi_app():
    from backend.app import create_app
    app = create_app('production')
    
    # Warm up connections
    with app.app_context():
        from backend.models import db
        db.engine.execute('SELECT 1')
    
    return app

app = get_wsgi_app()
```

### Caching Strategy

```python
# Use Redis for frequently accessed data
from functools import wraps
from redis import Redis

redis = Redis.from_url(os.getenv('REDIS_URL'))

def cache_result(ttl=300):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = f"cache:{f.__name__}:{str(args)}:{str(kwargs)}"
            result = redis.get(key)
            if result:
                return json.loads(result)
            
            result = f(*args, **kwargs)
            redis.setex(key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

## Alternative: Docker Deployment

For more control, also deploy as Docker container:

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements-vercel.txt .
RUN pip install --no-cache -r requirements-vercel.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "wsgi:app"]
```

Deploy to:
- **Railway.app** - $5/month
- **Render.com** - $7/month
- **Heroku** - $7/month (containers)
- **DigitalOcean App Platform** - $12/month

## Next Steps

1. ✅ Create Supabase/PlanetScale account
2. ✅ Generate security keys
3. ✅ Set up Upstash Redis
4. ✅ Push code to GitHub
5. ✅ Link Vercel to GitHub repo
6. ✅ Set environment variables
7. ✅ Deploy to Vercel
8. ✅ Test API endpoints
9. ✅ Configure custom domain
10. ✅ Monitor in Vercel dashboard

## Support

- **Vercel Docs**: https://vercel.com/docs
- **Flask on Vercel**: https://vercel.com/docs/concepts/functions/serverless-functions/supported-languages#official-runtimes
- **Supabase Docs**: https://supabase.com/docs
- **Upstash Docs**: https://docs.upstash.io

---

**Ready for deployment!** 🚀
