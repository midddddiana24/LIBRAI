# LIBRAI: step-by-step free online setup

**Goal:** keep the existing library records and reset admin password, then let the website and Android kiosk use one public API. This setup uses Neon Free for PostgreSQL and private file storage, plus a new Render Free API. The current live website and API remain in place until the new setup is tested.

**Current status (14 October 2026):** The Neon CLI and editor integration are installed. This folder is linked **offline** to Neon project `small-river-91786237`, branch `production`; the link has not been verified with Neon. [`neon.ts`](../neon.ts) declares a private bucket named `librai-media`. **`neon deploy` has not succeeded.** The CLI still reports no signed-in account because browser login timed out twice. `npm run build` passed locally. The existing local database backup and media ZIP are still on this computer; no records have been uploaded to Neon. The new Render API has not been created.

## Part 1 — Sign in and create the private bucket

Do these steps on the computer that contains this repository. You can use the terminal built into VS Code; you do not need to find a separate PowerShell app.

1. In VS Code, choose **Terminal → New Terminal**. If needed, move to the project folder:

   ```powershell
   cd C:\Users\rober\Desktop\LIBRAI
   ```

2. Run:

   ```powershell
   neon login
   ```

   A Neon sign-in page should open in your browser. Complete it promptly, then return to the **same VS Code terminal**. The terminal must report a successful login. A page showing a `psql -h ...` command is Neon's database connection screen; that command does not sign in the CLI. If the terminal says the login timed out, run `neon login` again in **your own VS Code terminal** and finish the newly opened browser page within about a minute. If it still fails, tell me the browser message and terminal error; do not share tokens or passwords.

3. Check that the CLI really saved the login:

   ```powershell
   neon profile list
   ```

   The active profile's **Account** must show your Neon account, rather than `-` or `missing`. **Stop here if it still shows `-`.**

4. In the [Neon Console](https://console.neon.tech/), open project `small-river-91786237`. On its Overview page, check that its region is **AWS Asia Pacific (Singapore)** (`aws-ap-southeast-1`) and that the branch named `production` exists. [Neon's region table](https://neon.com/docs/introduction/regions) confirms that Singapore supports both PostgreSQL and Object Storage. A project's region cannot be changed after creation; if this one is elsewhere, stop and tell me the region before deploying.

5. Back in the VS Code terminal, preview the proposed Neon change:

   ```powershell
   neon config plan
   ```

   Check that it targets the project and `production` branch above and creates the **private `librai-media` bucket**. If it proposes deleting or replacing something you need, stop and share only the non-secret summary.

6. Apply the plan:

   ```powershell
   neon deploy
   ```

   Expect a success message for the bucket and a message that Neon variables were pulled into this project's ignored `.env` file. The file contains credentials; **do not commit it or paste it into chat**. If the command fails, stop and share the error with secrets removed. You can confirm the bucket in the Neon Console under **Object Storage**.

**At this point, tell me “Neon deploy succeeded.”** I can check the database and file connections and handle the record import with you. Do not switch the website or Android app yet.

## Part 2 — Move the existing records and files

The saved sources are `backups/librai-20261014-012653-887385.db` and `backups/librai-media-20261014-012656-462596.zip`. They contain the locally reset admin account and all records you confirmed need keeping: 2 users, 6 books, 8 copies, and 1 borrowing. The ZIP contains four referenced files, including a private student photo. Keep both files private and keep an offline copy after migration.

Do this only after Part 1 succeeds and the `production` branch is confirmed to be the intended place for these records.

1. In `.env`, confirm the keys `DATABASE_URL`, `AWS_ENDPOINT_URL_S3`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION` are present. Add this line once if it is missing:

   ```dotenv
   MEDIA_BUCKET=librai-media
   ```

   Neon writes the credentials; never invent them or send them to me. The Python API reads these values from `.env`. For schema migration and data import, use Neon's **Direct** PostgreSQL connection, whose host does **not** contain `-pooler`. If `.env` has a pooled URL, select **Direct connection** in Neon Console → **Connect**, then use that direct URL for the migration. Do not paste it into chat. [Neon recommends direct connections for migrations](https://neon.com/docs/connect/connection-pooling).

2. Run the existing Alembic migrations on the **empty** Neon database from the repository root:

   ```powershell
   .\.venv\Scripts\python.exe -m alembic upgrade head
   ```

   If this fails, stop. Do not run `seed.py`, delete tables, or try the import on an unknown database.

3. Copy the local backup into Neon. The command asks for the **Direct PostgreSQL URL**; input is hidden as you type or paste. Use the backup made **after** the admin password reset:

   ```powershell
   .\.venv\Scripts\python.exe -m backend.scripts.migrate_sqlite_to_postgres --sqlite-backup backups/librai-20261014-012653-887385.db
   ```

   Expect `COPY_COMPLETE`. The script requires an empty target and matching Alembic versions. If it reports existing records or a mismatch, **stop**. It will not merge or erase them automatically.

4. Upload the matching files into the private Neon bucket:

   ```powershell
   .\.venv\Scripts\python.exe -m backend.scripts.upload_media_bundle --media-bundle backups/librai-media-20261014-012656-462596.zip
   ```

   Expect `MEDIA_UPLOAD_COMPLETE files=4`. If the upload fails partway, stop and ask for help before repeating it; the script refuses to overwrite existing objects.

5. Test the API locally against Neon:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
   ```

   Open `http://127.0.0.1:8001/health` in a browser. It should say `status: healthy` and `database: connected`. Press **Ctrl+C** in the terminal to stop the local API. Then run `npm run build` from the repository root; it should end with `✓ built`. A healthy response proves the database connection, but we still need to test sign-in, cover/photo/report downloads, and a real borrow/return before switching clients.

## Part 3 — Create the new Free API on Render

Do this after Part 2 is verified. The free Render service is separate from your current API, so the existing site is not changed during setup.

1. The current code must be committed and pushed to the `online-admin-postgres` GitHub branch before Render can build it. Check with me before this step if Part 1 or 2 failed; a local edit alone is not deployed.
2. In [Render](https://dashboard.render.com/), choose **New → Blueprint**, select the `LIBRAI` GitHub repository and the `online-admin-postgres` branch, then select [`render.free-persistent.yaml`](../render.free-persistent.yaml). Review the preview: it should create **one Free web service** named `librai-api-free-pg` in **Singapore**, with no Render database or disk. Do not select the paid `render.production.yaml` file.
3. In that new API service's **Environment**, enter the Neon values for `DATABASE_URL`, `AWS_ENDPOINT_URL_S3`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`. `MEDIA_BUCKET=librai-media` is in the Blueprint. Add **one** AI provider key (`GEMINI_API_KEY` or `TOKENROUTER_API_KEY`), because this backend currently requires one in production. Render generates `SECRET_KEY`; keep it stable across deploys. Put secrets in Render only, never Git or chat.
4. Deploy the new service. Open `https://<new-api-host>/health`. It must say `status: healthy` and `database: connected`. If the service was idle, Render Free may take roughly a minute to wake. [Render Free limitations](https://render.com/docs/free) explain its sleep and usage limits.
5. Verify admin sign-in with the locally reset password, the expected record counts, the four files, and a test borrow and return. Restart the new API service and confirm the records and files still appear. Keep the local backup and ZIP until restore has been tested.

## Part 4 — Switch the website and Android kiosk

Only after the new API passes the checks above:

1. In Render, open the existing **librai-kiosk** service. Change its `VITE_API_BASE_URL` to `https://<new-api-host>/api/v1` and **redeploy** the website; this value is compiled into the JavaScript build.
2. Open `https://librai-kiosk-zjic.onrender.com/admin` and sign in. Confirm the migrated books, users, and borrowing appear. Test from a phone browser as well.
3. Rebuild and install the Android APK with the same new API URL. Test a real QR borrow and return on the tablet using school Wi-Fi and another internet connection. The old APK still points to the old API until rebuilt.

## What is free, and what to keep safe

Neon announced 1 GB PostgreSQL and 5 GB Object Storage per Free project in October 2026; [check the current Free limits](https://neon.com/blog/neon-free-plan-1-gb-per-project) in your account. Render Free services sleep and lose **local** files on restart, which is why this setup places records and files in Neon. Free plans still have usage and recovery limits. Make regular backups of **both** PostgreSQL data and Object Storage files; a database backup alone does not contain images or reports.

The old API at `https://librai-api-zjic.onrender.com` and the old website remain unchanged until Part 4. `neon init` only installed tooling and wrote local configuration; it did **not** create the bucket, import records, or publish the API.


## Gmail notifications and emailed library IDs

See [Gmail notifications setup](gmail_notifications.md). Render Free blocks SMTP ports; use a separate SMTP-capable worker. Approval queues the member QR email; queued does not mean sent.
