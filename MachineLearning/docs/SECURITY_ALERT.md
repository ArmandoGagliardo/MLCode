# 🚨 SECURITY ALERT - IMMEDIATE ACTION REQUIRED

## Critical Issue Detected

A GitHub API token was found hardcoded in your repository:

**File**: `module/preprocessing/github_crawler.py` (line 88)
**Token**: `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`

## ⚠️ IMMEDIATE ACTIONS REQUIRED

### 1. Revoke the Exposed Token (DO THIS FIRST!)

The token is now exposed in your git history and must be revoked immediately:

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Find the token `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`
3. Click **Delete** or **Revoke**
4. Confirm deletion

**Why?** Anyone who clones or accesses this repository can use this token to access your GitHub account with the permissions you granted.

### 2. Create a New Token

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Give it a descriptive name: "ML Project Crawler"
4. Select minimum required scopes:
   - For public repos only: `public_repo`
   - For private repos: `repo`
5. Set expiration (recommended: 90 days)
6. Click **Generate token**
7. **Copy the token immediately** (you won't see it again!)

### 3. Configure Your Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your NEW token:
   ```env
   GITHUB_TOKEN=your_new_token_here
   ```

3. Verify `.env` is in `.gitignore` (already done):
   ```bash
   grep "^\.env$" .gitignore
   ```

### 4. Install Missing Dependencies

```bash
pip install python-dotenv
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### 5. Test the Configuration

```bash
python -c "from config import validate_config; validate_config(); print('✅ Configuration valid!')"
```

### 6. Clean Git History (IMPORTANT!)

The old token is in your git history. If this repository is public or will be pushed to GitHub, you MUST clean the history:

**Option A: BFG Repo-Cleaner (Recommended)**
```bash
# Install BFG
# Download from: https://rtyley.github.io/bfg-repo-cleaner/

# Replace the token in all commits
java -jar bfg.jar --replace-text passwords.txt
git reflog expire --expire=now --all && git gc --prune=now --aggressive
```

**Option B: Git Filter-Repo**
```bash
# Install git-filter-repo
pip install git-filter-repo

# Create a file with the token to remove
echo "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" > tokens-to-remove.txt

# Filter repository
git filter-repo --replace-text tokens-to-remove.txt
```

**Option C: Start Fresh (If not yet pushed)**
If you haven't pushed this repo to GitHub yet:
```bash
# Remove git history
rm -rf .git

# Initialize fresh repository
git init
git add .
git commit -m "Initial commit with secure configuration"
```

### 7. Force Push (If Already on GitHub)

⚠️ **WARNING**: This will rewrite history. Notify all collaborators!

```bash
git push --force --all
git push --force --tags
```

## Prevention Checklist

- [x] `.gitignore` updated to exclude `.env` files
- [x] Configuration system using environment variables
- [x] `.env.example` template created
- [x] README documentation updated
- [ ] Old token revoked
- [ ] New token created
- [ ] `.env` file configured
- [ ] Git history cleaned
- [ ] Changes pushed

## What Changed

The following improvements have been implemented:

1. **Configuration System** (`config.py`):
   - Centralized configuration management
   - Loads settings from `.env` file
   - Validates required settings on startup
   - Provides secure header generation

2. **Environment Template** (`.env.example`):
   - Template for all required environment variables
   - Clear instructions for obtaining GitHub token

3. **Enhanced Security** (`.gitignore`):
   - Protects `.env` files and secrets
   - Excludes sensitive data from version control

4. **Improved Code** (`github_crawler.py`):
   - Removed hardcoded token
   - Uses environment variable
   - Fails gracefully with clear error messages

5. **Better Logging** (`main.py`):
   - Structured logging to file and console
   - Error tracking and debugging

6. **Constants Organization** (`module/config/constants.py`):
   - Centralized magic numbers
   - Easier maintenance and updates

## Testing Your Setup

After completing all steps, test the crawler:

```bash
python main.py --crawl_git
```

You should see:
- ✅ Configuration loaded successfully
- ✅ Crawling starts without errors
- ❌ No token-related errors

## Need Help?

If you encounter issues:

1. Check logs: `ml_system.log`
2. Verify `.env` file exists and contains token
3. Ensure token has correct permissions
4. Verify token is not expired

## Additional Security Recommendations

1. **Use Short-lived Tokens**: Set expiration dates on GitHub tokens
2. **Minimal Permissions**: Only grant required scopes
3. **Regular Rotation**: Change tokens every 90 days
4. **Monitor Usage**: Check token usage in GitHub settings
5. **Enable 2FA**: Protect your GitHub account with two-factor authentication

## Questions?

- GitHub Token Documentation: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
- Git History Cleaning: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository

---

**Date**: 2025-10-30
**Severity**: CRITICAL
**Status**: Code fixed, user action required
