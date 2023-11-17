# App Packager

This allows a micropython device to be updated automatically over tcp.

## Workflow:
 * Commit changes to your branch
   * `.github/workflows/deploy_web_downloads.yml` will deploy all app_packages to the folder `web_downloads`
 * The micropython device will poll for changes
   * update its software

## Preparation

 * Repo: Copy `.github/workflows/deploy_web_downloads.yml`
 * Repo: Copy `software/app_packager`
 * Repo: Add `software/app_package.py`
 * Github: https://github.com/<project>/settings/pages
   * `GitHub Pages` -> `Build and deployment` -> `Source` ==> Set to `GitHub Actions`


## app_packager.py

This app will copy the files according to `app_package.py` and will deploy package.tar file to `web_downloads`.
