# Cloud Storage Management System

Automated cloud storage integration for dataset synchronization and model backups.

## Features

- **Multi-Provider Support**: Backblaze B2, Wasabi, AWS S3, DigitalOcean Spaces, Cloudflare R2
- **Auto-Sync on Startup**: Automatically downloads datasets when the storage manager connects
- **Incremental Sync**: Only uploads/downloads changed files to save bandwidth
- **Model Backup**: Automatically backs up trained models after fine-tuning
- **Model Restore**: Restore previously backed up models
- **Simple CLI**: Easy-to-use command-line interface

## Supported Providers

| Provider | Storage Cost | Egress Cost | Setup |
|----------|-------------|-------------|-------|
| **Backblaze B2** | ~$5/TB/month | $10/TB | [backblaze.com](https://www.backblaze.com/b2/) |
| **Wasabi** | ~$6/TB/month | Free | [wasabi.com](https://wasabi.com/) |
| **AWS S3** | ~$23/TB/month | Variable | [aws.amazon.com/s3](https://aws.amazon.com/s3/) |
| **DigitalOcean Spaces** | $5/month (250GB + 1TB) | Included | [digitalocean.com/spaces](https://www.digitalocean.com/products/spaces) |
| **Cloudflare R2** | $15/TB/month | Free | [cloudflare.com/r2](https://www.cloudflare.com/products/r2/) |

## Quick Start

### 1. Install Dependencies

```bash
pip install boto3
```

### 2. Configure Provider

Copy `.env.example` to `.env` and configure your chosen provider:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Choose your provider
STORAGE_PROVIDER=backblaze  # or: wasabi, s3, digitalocean, cloudflare_r2

# Auto-sync settings
AUTO_SYNC_ON_STARTUP=true
AUTO_BACKUP_AFTER_TRAINING=true

# Backblaze B2 credentials (example)
BACKBLAZE_BUCKET=my-ml-bucket
BACKBLAZE_KEY_ID=your_key_id
BACKBLAZE_APPLICATION_KEY=your_application_key
BACKBLAZE_ENDPOINT=https://s3.us-west-004.backblazeb2.com
```

### 3. Test Connection

```bash
python main.py --storage-connect
```

Expected output:
```
✅ Storage connected successfully!

📦 Storage Information:
   Provider: BACKBLAZE
   Bucket: my-ml-bucket
   Files: 42
   Total Size: 1234.56 MB
   Local Dataset Dir: data/datasets
   Local Models Dir: models/saved
```

## Usage

### Connect to Storage

```bash
python main.py --storage-connect
```

### Download Datasets

Download only new/changed files (incremental):
```bash
python main.py --storage-download
```

Download all files (force):
```bash
python main.py --storage-download --force
```

### Upload Datasets

Upload only new/changed files (incremental):
```bash
python main.py --storage-upload
```

Upload all files (force):
```bash
python main.py --storage-upload --force
```

### Backup Models

Backup a model after training:
```bash
python main.py --storage-backup models/security_classification
```

Backup with custom name:
```bash
python main.py --storage-backup models/security_classification --model-name security_v2
```

### Restore Models

List all backed up models:
```bash
python main.py --storage-list
```

Restore a specific model:
```bash
python main.py --storage-restore security_classification_20250101_120000
```

Restore to custom location:
```bash
python main.py --storage-restore security_v2 --model-name models/restored/security_v2
```

## Programmatic Usage

### Basic Example

```python
from module.storage import StorageManager

# Initialize storage manager
storage = StorageManager()

# Connect to cloud storage
if storage.connect():
    print("Connected to storage!")

    # Download datasets
    stats = storage.download_datasets()
    print(f"Downloaded: {stats['downloaded']} files")

    # Upload datasets
    stats = storage.upload_datasets()
    print(f"Uploaded: {stats['uploaded']} files")

    # Backup a model
    storage.backup_model(
        'models/security_classification',
        model_name='security_v1',
        metadata={'accuracy': 0.95, 'epoch': 10}
    )

    # List backed up models
    models = storage.list_models()
    print(f"Backed up models: {models}")

    # Restore a model
    storage.restore_model('security_v1', destination='models/restored')
```

### Custom Configuration

```python
from module.storage import StorageManager

# Custom configuration
config = {
    'provider_type': 'wasabi',
    'provider_config': {
        'bucket_name': 'my-bucket',
        'access_key': 'YOUR_ACCESS_KEY',
        'secret_key': 'YOUR_SECRET_KEY',
        'region': 'us-east-1'
    },
    'local_dataset_dir': 'custom/datasets',
    'local_models_dir': 'custom/models',
    'auto_sync_on_startup': False,
}

storage = StorageManager(config=config)
storage.connect()
```

### Using Specific Providers

```python
from module.storage.providers import BackblazeProvider, WasabiProvider

# Backblaze B2
backblaze = BackblazeProvider(
    bucket_name='my-bucket',
    key_id='YOUR_KEY_ID',
    application_key='YOUR_APP_KEY'
)

if backblaze.connect():
    # Upload file
    backblaze.upload_file('local/model.pt', 'models/model_v1.pt')

    # Download file
    backblaze.download_file('models/model_v1.pt', 'downloaded/model.pt')

    # List files
    files = backblaze.list_files(prefix='models')
    for file in files:
        print(f"{file['key']}: {file['size']} bytes")
```

## Integration with Training Pipeline

The storage manager can automatically download datasets on startup and backup models after training:

```python
from module.storage import StorageManager
from module.model.model_manager import ModelManager

# Initialize storage
storage = StorageManager()
storage.connect()  # Auto-downloads datasets if AUTO_SYNC_ON_STARTUP=true

# Train model
model_manager = ModelManager(task='security_classification', model_name='codebert-base')
trainer = AdvancedTrainer(model_manager)
trainer.train_model(
    dataset_path='data/datasets/security_data.json',
    model_save_path='models/security_classification'
)

# Backup trained model
if os.getenv('AUTO_BACKUP_AFTER_TRAINING', 'true').lower() == 'true':
    storage.backup_model(
        'models/security_classification',
        model_name=f'security_classification_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        metadata={
            'task': 'security_classification',
            'base_model': 'codebert-base',
            'training_date': datetime.now().isoformat()
        }
    )
```

## Directory Structure

```
data/
  datasets/              # Local datasets (synced from cloud)
    security_data.json
    code_generation.json
    ...

models/
  saved/                 # Local trained models (backed up to cloud)
    security_classification/
      pytorch_model.bin
      config.json
      ...
```

Cloud bucket structure:
```
bucket/
  datasets/             # Remote datasets
    security_data.json
    code_generation.json
    ...

  models/               # Remote model backups
    security_classification_20250101_120000/
      pytorch_model.bin
      config.json
      metadata.json
    code_generation_20250101_130000/
      ...
```

## Environment Variables

### General Settings

- `STORAGE_PROVIDER`: Provider type (backblaze, wasabi, s3, digitalocean, cloudflare_r2)
- `AUTO_SYNC_ON_STARTUP`: Auto-download datasets on connection (true/false)
- `AUTO_BACKUP_AFTER_TRAINING`: Auto-backup models after training (true/false)
- `LOCAL_DATASET_DIR`: Local dataset directory (default: data/datasets)
- `LOCAL_MODELS_DIR`: Local models directory (default: models/saved)
- `REMOTE_DATASET_PREFIX`: Remote dataset prefix (default: datasets)
- `REMOTE_MODELS_PREFIX`: Remote model prefix (default: models)

### Provider-Specific Settings

See `.env.example` for complete provider configuration examples.

## Troubleshooting

### Connection Failed

1. **Check credentials**: Ensure your API keys are correct in `.env`
2. **Check bucket name**: Verify the bucket exists and you have access
3. **Check endpoint**: For Backblaze, ensure the endpoint matches your bucket region
4. **Check permissions**: Ensure your API key has read/write permissions

### Import Error (boto3)

```bash
pip install boto3 botocore
```

### Slow Downloads/Uploads

- Use incremental sync (default) instead of `--force`
- Check your internet connection
- Consider using a provider with better performance in your region

## Advanced Features

### Custom Provider

You can create custom storage providers by extending `BaseStorageProvider`:

```python
from module.storage.base_provider import BaseStorageProvider

class MyCustomProvider(BaseStorageProvider):
    def connect(self) -> bool:
        # Implementation
        pass

    def upload_file(self, local_path, remote_path, metadata=None) -> bool:
        # Implementation
        pass

    # ... implement other abstract methods
```

### Encryption

For sensitive data, consider encrypting files before upload:

```python
import cryptography

# Encrypt before upload
encrypted_data = encrypt(model_data)
storage.upload_file(encrypted_path, remote_path)

# Decrypt after download
storage.download_file(remote_path, encrypted_path)
decrypted_data = decrypt(encrypted_path)
```

## Best Practices

1. **Use incremental sync**: Saves bandwidth and time
2. **Backup regularly**: Set `AUTO_BACKUP_AFTER_TRAINING=true`
3. **Use descriptive model names**: Include version, date, or metrics
4. **Monitor storage costs**: Track your bucket size and downloads
5. **Test restore**: Periodically verify backups can be restored
6. **Use .gitignore**: Keep credentials and large files out of git

## Cost Optimization

1. **Choose the right provider**: Wasabi/Cloudflare R2 have free egress
2. **Use incremental sync**: Only transfer changed files
3. **Compress datasets**: Reduce storage and transfer costs
4. **Clean old backups**: Delete outdated model backups
5. **Monitor usage**: Set up billing alerts with your provider

## Support

For issues or questions:
1. Check this README
2. Check provider-specific documentation
3. Review error logs in `ml_system.log`
4. Check GitHub issues

## License

MIT License - see LICENSE file for details
