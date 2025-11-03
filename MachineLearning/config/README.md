# Unified Configuration System

This directory contains the unified environment configuration system for the Machine Learning project.

## ⚠️ SECURITY WARNING

**NEVER commit .env files with real credentials to Git!**
- All `.env` files are gitignored
- Use `.env.example` files as templates
- Regenerate any exposed credentials immediately

## Configuration Structure

```
config/
├── README.md           # This file
├── .env.common         # Shared variables across all environments
├── .env.local          # Local development configuration
├── .env.gpu            # GPU instance configuration
└── .env.production     # Production configuration (optional)
```

## How to Use

### 1. For Local Development

```bash
# Set environment
export ENVIRONMENT=local

# Copy templates and customize
cp config/.env.common .env.common
cp config/.env.local .env.local

# Edit with your credentials
nano config/.env.common  # Add GITHUB_TOKEN, storage credentials
nano config/.env.local    # Adjust local settings

# Run the application
python main.py
```

### 2. For GPU Instance (Brev, AWS, etc.)

```bash
# Set environment
export ENVIRONMENT=gpu

# Copy templates
cp config/.env.common .env.common
cp config/.env.gpu .env.gpu

# Configure for GPU
nano config/.env.common  # Add credentials
nano config/.env.gpu      # Set CUDA_VISIBLE_DEVICES, batch sizes, etc.

# Start training
python main.py --train code_generation
```

### 3. For Production

```bash
export ENVIRONMENT=production
# Uses .env.production configuration
```

## Environment Variables

### Common Variables (.env.common)

These are shared across all environments:

- **GitHub**: `GITHUB_TOKEN` - Required for repository access
- **Storage**: Provider selection and credentials
- **Paths**: Dataset and model directories
- **Logging**: Log level and formatting

### Local Variables (.env.local)

Optimized for local development:

- **CUDA**: Set to `-1` for CPU only
- **Training**: Small batch sizes and epochs
- **Dataset**: Limited file counts for testing
- **Sync**: Disabled cloud sync

### GPU Variables (.env.gpu)

Optimized for GPU instances:

- **CUDA**: Multi-GPU support
- **Training**: Large batch sizes, more epochs
- **Performance**: Memory pinning, benchmarking
- **API**: Server configuration for inference
- **Monitoring**: Metrics and health checks

## Variable Naming Convention

All cloud storage variables follow a consistent pattern:

```
{PROVIDER}_{RESOURCE}_{ATTRIBUTE}

Examples:
- BACKBLAZE_BUCKET_NAME
- AWS_ACCESS_KEY_ID
- DO_SECRET_ACCESS_KEY
- CLOUDFLARE_ACCOUNT_ID
```

## Migration from Old System

If you have existing `.env` files:

```bash
# Check for issues
python migrate_env.py --check

# Perform migration
python migrate_env.py

# Auto-migrate without prompts
python migrate_env.py --auto
```

The migration script will:
1. Backup existing configuration
2. Convert old variable names to new standard
3. Split variables into appropriate config files
4. Detect exposed secrets and warn you

## Configuration Priority

1. Environment-specific file (e.g., `.env.gpu`)
2. Common configuration (`.env.common`)
3. Default values in code

Later values override earlier ones.

## Switching Environments

### Method 1: Environment Variable

```bash
export ENVIRONMENT=gpu
python main.py
```

### Method 2: In Python

```python
import os
os.environ['ENVIRONMENT'] = 'gpu'
from config import config
```

### Method 3: Command Line (future)

```bash
python main.py --env gpu
```

## Storage Provider Configuration

### Backblaze B2

```bash
STORAGE_PROVIDER=backblaze
BACKBLAZE_BUCKET_NAME=your-bucket
BACKBLAZE_KEY_ID=your-key-id
BACKBLAZE_APPLICATION_KEY=your-app-key
```

### DigitalOcean Spaces

```bash
STORAGE_PROVIDER=digitalocean
DO_BUCKET_NAME=your-space
DO_ACCESS_KEY_ID=your-key
DO_SECRET_ACCESS_KEY=your-secret
DO_REGION=nyc3
```

### AWS S3

```bash
STORAGE_PROVIDER=s3
AWS_BUCKET_NAME=your-bucket
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```

## Troubleshooting

### Issue: "GITHUB_TOKEN not found"

**Solution**: Add your GitHub token to `config/.env.common`:
```bash
GITHUB_TOKEN=ghp_your_token_here
```

### Issue: Old variable names not working

**Solution**: Run migration script:
```bash
python migrate_env.py
```

### Issue: Wrong environment loaded

**Solution**: Check environment variable:
```bash
echo $ENVIRONMENT  # Should show: local, gpu, or production
```

### Issue: Credentials exposed in Git

**Solution**:
1. Remove from Git history
2. Revoke all exposed credentials
3. Generate new credentials
4. Ensure .gitignore is working

## Best Practices

1. **Never commit real credentials** - Use placeholders in examples
2. **Use environment detection** - Let the system choose the right config
3. **Keep secrets separate** - Don't mix dev and production credentials
4. **Regular rotation** - Change credentials periodically
5. **Minimal permissions** - Grant only necessary access

## Development Workflow

1. **Local Testing**:
   ```bash
   ENVIRONMENT=local python main.py --test
   ```

2. **GPU Training**:
   ```bash
   ENVIRONMENT=gpu python main.py --train
   ```

3. **Production Inference**:
   ```bash
   ENVIRONMENT=production uvicorn gpu_server:app
   ```

## Support

For issues or questions:
1. Check this README
2. Run migration script diagnostics: `python migrate_env.py --check`
3. Review config_new.py for implementation details
4. Check logs for configuration loading messages