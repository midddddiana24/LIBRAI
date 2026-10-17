# Free Gmail notifications: step-by-step guide

Updated: 17 October 2026.

## Start here

**Use this guide if you want to keep Render Free and send library emails from Gmail without a paid worker.** The planned connection is **Gmail API over HTTPS**.

**Current status:** Gmail API delivery, a one-time authorization command, staff **Send now**, and optional automatic polling are implemented and tested. Google authorization succeeded; Gmail accepted one authorized sample QR email from an isolated local test, and the recipient confirmed receiving its QR attachment. Verify the Render deployment includes registration before following Step 8. Automatic delivery defaults to off.

| Part | Who does it | Status |
| --- | --- | --- |
| Steps 1-5: Google setup | You, in your browser | Can do now |
| Step 6: authorize the library sender | You, in the Google sign-in window | Required before sending |
| Steps 7-8: deploy and test | After Step 6 | Do later |

Render Free blocks SMTP ports 25, 465 and 587. Gmail API avoids those SMTP ports. Standard Gmail API use has no additional API charge within Google's allowance; sending and API quotas still apply, and pricing can change. Do not enable paid quota increases for this setup. Sources: [Render Free](https://render.com/docs/free), [Google Gmail API quotas and pricing](https://developers.google.com/workspace/gmail/api/reference/quota).

You do **not** need a Gmail App Password for the Gmail API route. It uses Google sign-in permission, called **OAuth**.

## Step 1 - Choose the library sender account

1. Use a Gmail inbox you control, preferably a dedicated library account.
2. Sign into that account in your browser.
3. Keep it open while completing the next steps.

**Checkpoint:** this is the address students will receive their library emails from. Students only receive mail; they do not need to authorize Google access.

## Step 2 - Create the Google Cloud project

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Open the project selector at the top.
3. Choose **New project**.
4. Name it **LIBRAI Notifications** and create it.
5. Select that project.

**Checkpoint:** the selected project is **LIBRAI Notifications**. You are creating a project, not purchasing hosting.

## Step 3 - Enable Gmail API

1. In the project menu, open **APIs & Services > Library**.
2. Search for **Gmail API**.
3. Open Google's Gmail API entry and choose **Enable**.

**Checkpoint:** its page offers **Manage** or says the API is enabled.

## Step 4 - Set up Google sign-in consent

1. Open **Google Auth Platform > Branding**. Choose **Get started** if prompted.
2. Use **LIBRAI Notifications** as the app name and your library Gmail as the support/contact email.
3. For a personal `@gmail.com` account, choose **External** under **Audience**. **Internal** is only appropriate for an eligible school/organization Workspace project.
4. Keep the initial setup in **Testing** and add your sender Gmail under **Audience > Test users**.
5. Under **Data Access**, add the send-only scope: `https://www.googleapis.com/auth/gmail.send`.
6. Save the configuration.

**Checkpoint:** your sender is a test user and the requested Gmail permission is sending mail. LIBRAI does not need inbox-reading permission for notifications.

## Step 5 - Create the OAuth client

1. Open **Google Auth Platform > Clients > Create client**.
2. Select **Desktop app**, named **LIBRAI sender setup**. This is for the planned one-time authorization on your computer.
3. Create it and download the JSON credentials file.
4. Store that file privately **outside the LIBRAI repository**. Do not paste its contents into chat or commit it to GitHub.

**Checkpoint:** you have the downloaded OAuth client JSON. This is not an API key or an App Password. Downloading it has not authorized LIBRAI to send yet.

Google documents project, consent and desktop-client preparation in its [Python quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python). Its sample reads Gmail labels; do not run that sample expecting LIBRAI QR emails.

## Step 6 - Authorize your library Gmail sender

This uses the Desktop client from Step 5. It does not send an email.

1. Open **VS Code > Terminal > New Terminal** in the LIBRAI folder.
2. Run the following command. Replace the client filename with your downloaded JSON filename, and replace the sender with your library Gmail address. For a file outside the project, use its full path inside quotes.

   ```powershell
   .\.venv\Scripts\python.exe -m backend.scripts.authorize_gmail --client ".\client_secret_YOUR_DOWNLOAD.json" --sender "your-library@gmail.com"
   ```

3. In Google, choose **the same sender account** and approve the permission to send mail. The command requests only `gmail.send`, with offline access; it does not request inbox-reading permission.
4. Return to the terminal. Expect `GMAIL_AUTHORIZED: private credentials saved to generated/gmail-oauth.json. No email was sent.`
5. Keep `generated/gmail-oauth.json` private. It contains the refresh token needed after the access token expires. The generated directory and downloaded `client_secret*.json` files are ignored by Git.

The command waits up to five minutes. After a timeout, fix the Google setting and run it again. If the output file already exists, choose a new `--output` path for reauthorization rather than overwriting credentials still used by a sender.

**Checkpoint:** the terminal reports `GMAIL_AUTHORIZED`. The downloaded client file alone is insufficient.

### If Google says Access blocked / Error 403: access_denied

When the page says the app is being tested and only developer-approved testers can access it:

1. Select the Google Cloud project containing the downloaded OAuth client.
2. Open **Google Auth Platform > Audience > Test users > Add users**.
3. Add the exact Gmail sender address, save, then run the authorization command again.
4. Choose that same account in the browser.

If this persists, confirm the client belongs to this project rather than another project with the same app name. Organization-policy errors may require the school Google administrator. Do not publish the app just to bypass a missing test-user entry.

### Before unattended use: finish the OAuth production setup

External apps left in **Testing** receive refresh tokens that expire after seven days for Gmail scopes. Testing is suitable for the initial check, not ongoing library notifications. Before regular use, configure the appropriate production audience/publishing status and complete any Google verification requirements that apply. Publishing alone is not a promise of verification or permanent tokens. [Google refresh-token rules](https://developers.google.com/identity/protocols/oauth2#expiration).

## Step 7 - Deploy on the existing Render Free API

1. Publish the reviewed code to **online-admin-postgres**. Deploy the existing API and kiosk/admin services from that branch. Local changes do not update Render by themselves.
2. In the API service, open **Environment > Secret Files** and add **gmail-oauth.json**.
3. Open local `generated/gmail-oauth.json` privately in VS Code. Copy its contents into that Render secret file and save. Never paste them into chat or GitHub.
4. Add the following environment variables to the API service:

   | Name | Exact value |
   | --- | --- |
   | `EMAIL_TRANSPORT` | `gmail_api` |
   | `GMAIL_OAUTH_FILE` | `/etc/secrets/gmail-oauth.json` |
   | `EMAIL_AUTOSEND_ENABLED` | `false` for the first test |

5. Save and redeploy. Keep the existing Neon database, stable API secret, AI key, storage, CORS and API URL. This route does not require a paid worker or Gmail App Password.
6. The existing API start command must apply migrations before Uvicorn. Do not seed or replace records.
7. Open [API health](https://librai-api-free-pg.onrender.com/health). Expect `status: healthy` and `database: connected`.
8. Open [Library admin](https://librai-kiosk-zjic.onrender.com/admin), sign in and verify the dashboard and users load.

**Checkpoint:** Gmail credentials and code are deployed; automatic delivery is still off.

Render documents the private file path in [Secret files](https://render.com/docs/configure-environment-variables#secret-files).

## Step 8 - Test one email and its QR

### If you cannot see Register

1. Open the [web kiosk](https://librai-kiosk-zjic.onrender.com/) in a browser. **Register** appears below the four main actions, beside **My account** and **Ask LIBRAI**; scroll down if necessary.
2. If it is missing, check **Render > kiosk service > Events**. The live deployment must include the registration update from **online-admin-postgres**. The API service must deploy that update too; a local edit or GitHub push alone is not proof that either service is live.
3. If needed, use **Manual Deploy > Deploy latest commit** on the API and kiosk services after their source branch is correct. Wait for both to report a successful deployment, then refresh with **Ctrl+Shift+R**.
4. Test the browser version first. The installed APK has its own bundled interface; it needs a new build and installation before it can show registration. Refreshing the website does not update that APK.
5. Keep automatic email delivery off during this first test. Configure the private Gmail secret file in Step 7 before using **Send now**.

### Test registration and approval

1. Use a test member with an inbox you own and permission to receive the test.
2. Submit kiosk registration. It should stay **pending**, with no usable QR emailed before approval.
3. In admin, review the details and approve the member.
4. Open **Email deliveries**. Check the test welcome email's recipient, choose **Send now** on that row, then confirm. This requests only that email.
5. Confirm its state changes to **sent**. This means the provider accepted it, not proof of inbox arrival.
6. Check your inbox and spam folder for **Your LIBRAI library ID** and **library-id.png**.
7. Display that image on another screen and scan it in the kiosk. Confirm it identifies the intended test member.
8. After success, review the existing pending backlog. When staff want those messages sent, set `EMAIL_AUTOSEND_ENABLED=true` in the Render API environment and redeploy. While awake, the API polls up to five pending messages per cycle, normally every 30 seconds.
9. If an email fails, fix the cause, choose **Retry** to queue it, then **Send now**, or wait for enabled automatic delivery.

**Checkpoint:** approval, inbox receipt and kiosk recognition all work. Do not mark email delivery verified from a pending queue row alone.

### Render Free sleep and recovery

Polling runs inside the API process and pauses when Render sleeps or restarts. Pending emails remain in Neon and resume at startup if automatic delivery is enabled. This is not an always-on scheduled worker. If Gmail accepts a message before the process stops and the database cannot record success, a duplicate is possible; check Gmail Sent mail before retrying an uncertain delivery. PostgreSQL row locks coordinate concurrent senders; SQLite requires one worker.

## Other notifications using the same queue

| Event | Email content |
| --- | --- |
| Approved registration / active member creation | Library ID QR |
| Borrow | Borrow confirmation and due date |
| Return | Return confirmation |
| Renewal | Updated due date |
| Reservation | Queue confirmation or ready-for-pickup notice |
| Fine assessed / paid | Fine notification or payment confirmation |

These notifications require a registered email address. Scheduled due-soon reminders and password-reset emails are not implemented by the current notification feature.

## If you want the free option that uses the existing SMTP code

Run the worker on an internet-connected school PC and leave that PC on. The website can stay on Render Free while the PC reads the same Neon queue and sends Gmail SMTP emails. When the PC is off, messages wait. This avoids a paid worker but still uses the PC's electricity and internet.

Follow [the separate SMTP setup guide](gmail_smtp_setup.md), using its **Local alternative / commands** section. That route requires a Google App Password; the Gmail API steps above do not.

## What to do now

**If your OAuth client is ready, continue at Step 6. If Google blocks testing access, add the sender under Audience > Test users first.**
