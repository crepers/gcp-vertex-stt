

## Deployment to Google Cloud

### Environment Variable Settings

```
PROJECT_ID=<YOUR_PROJECT_ID>
ORGANIZATION_ID=<YOUR_ORGANIZATION_ID>
LOCATION=<YOUR_LOCATION>
SERVICE_ACCOUNT_NAME=<YOUR_SERVICE_ACCOUNT_NAME>
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
CLOUDRUN_SERVICE=<YOUR_CLOUDRUN_SERVICE>
ARTIFACT_REGISTRY_REPO=<YOUR_ARTIFACT_REGISTRY_REPO>
IMAGE_NAME=<YOUR_IMAGE_NAME>
IMAGE_TAG="v1"
```


### API Setup

```
gcloud services enable run.googleapis.com --project=$PROJECT_ID
```

### Create Artifact Registry Repository

```
gcloud artifacts repositories create "$ARTIFACT_REGISTRY_REPO" \
    --repository-format=docker \
    --location="$LOCATION" \
    --description="Docker repository for $CLOUDRUN_SERVICE" \
    --project="$PROJECT_ID"
```


## Service Account

### Create SA

```
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
  --description="Service account for Speech to Text processor Cloud Run service" \
  --display-name="$SERVICE_ACCOUNT_NAME" \
  --project="$PROJECT_ID"
```


### Permission Configuration

-   Grant Vertex AI User role

```
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/aiplatform.user"
```

-   Grant Vertex AI Service Agent role (if needed)

```
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/aiplatform.serviceAgent"
```


-   Grant Logging Admin role (for Cloud Run log writing)

```
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/logging.admin"
```

-   Grant Cloud Service Account User role (necessary for Cloud Run to use the service account)

```
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.invoker"
```

- Grant the roles/run.invoker role to the Cloud Run service account

```
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/iam.serviceAccountUser"
```


## Create Cloud Run Service

```
python -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```
cd cloudrun-src
pip install -r requirements.txt
```

### Build Docker Image and Push to Artifact Registry

- For M1 Mac
```
docker build --platform linux/arm64 -t "$LOCATION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REGISTRY_REPO/$IMAGE_NAME:$IMAGE_TAG" -f cloudrun-src/Dockerfile cloudrun-src
```

- For Linux
```
docker build -t "$LOCATION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REGISTRY_REPO/$IMAGE_NAME:$IMAGE_TAG" -f cloudrun-src/Dockerfile cloudrun-src
```

- Configure Docker
Run the following command to configure gcloud as the credential helper for the Artifact Registry domain associated with this repository's location:

```
gcloud auth configure-docker $LOCATION-docker.pkg.dev
```

- Push the docker image
```
docker push "$LOCATION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REGISTRY_REPO/$IMAGE_NAME:$IMAGE_TAG"
```

### Deploy Cloud Run Service

```
gcloud run deploy "$CLOUDRUN_SERVICE" \
  --image="$LOCATION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REGISTRY_REPO/$IMAGE_NAME:$IMAGE_TAG" \
  --region="$LOCATION" \
  --max-instances=1 \
  --concurrency=1 \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,REGION=$LOCATION" \
  --service-account="$SERVICE_ACCOUNT_EMAIL" \
  --project="$PROJECT_ID"
```

### Get Cloud Run Service URL and Service Account Email

```
CLOUDRUN_SERVICE_URL=$(gcloud run services describe "$CLOUDRUN_SERVICE" --region="$LOCATION" --format="value(status.url)" --project="$PROJECT_ID")
```

