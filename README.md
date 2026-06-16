# BLS Workspace App

This repository contains a modified version of `openbb-bls` package. It serves data exclusively from relatively small XLSX spreadsheets and lists of PDF documents. There is no database to build or complex caching system, it relies on simple TTL.

## Running Locally

```sh
docker compose up --build
```

## Deployment

Deployment is automated via GitHub Actions using [Dokku](https://dokku.com). Pushing to `main` triggers a deploy.
