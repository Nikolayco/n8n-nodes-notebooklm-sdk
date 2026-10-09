<img src="nodes/NotebookLm/notebooklm.svg" width="90" height="90">

# n8n-nodes-notebooklm-sdk

An [n8n](https://n8n.io) community node for [Google NotebookLM](https://notebook.google.com). Manage notebooks, sources, artifacts, chat, and notes from your n8n workflows.

Built on top of [notebooklm-sdk](https://github.com/agmmnn/notebooklm-sdk), with a patched build for the new `notebook.google.com` host and for video generation (see [`vendor/`](vendor/README.md)). Session handling follows [notebooklm-py](https://github.com/teng-lin/notebooklm-py).

---

## Installation

This fork is not published to npm. The npm package with the same name is the original build and still targets the old NotebookLM host. Install the `.tgz` from a [release of this repository](https://github.com/Nikolayco/n8n-nodes-notebooklm-sdk/releases) inside your n8n data folder. For an n8n Docker container, for example:

```bash
docker exec -u node <n8n-container> sh -c "cd /home/node/.n8n/nodes && npm install --ignore-scripts https://github.com/Nikolayco/n8n-nodes-notebooklm-sdk/releases/download/v0.3.2/n8n-nodes-notebooklm-sdk-0.3.2.tgz"
docker restart <n8n-container>
```

Replace `<n8n-container>` with the name of your n8n container and use the link of the newest release. The data folder may differ in your setup.

---

## Authentication

NotebookLM has no public API key. The node signs in with the Google session cookies of a NotebookLM account, stored in a **NotebookLM API** credential (field **Session JSON**).

**Cookies go stale.** Google rotates the short-lived `__Secure-1PSIDTS` cookie every few hours. This SDK never rotates it, so a session pasted once stops working after a while. [notebooklm-py](https://github.com/teng-lin/notebooklm-py) does rotate it, which is why the setup below keeps the credential fresh automatically.

### Recommended: notebooklm-py with automatic refresh

1. On the machine that will keep the session, install notebooklm-py and sign in once. A browser window opens; sign in to the Google account that owns or can edit your notebooks:
   ```bash
   pip install "notebooklm-py[browser]"
   playwright install chromium
   notebooklm login
   ```
2. Every 15-20 minutes (cron, a systemd timer, any scheduler) run [`scripts/sync-session-to-n8n.py`](scripts/sync-session-to-n8n.py). It refreshes the session (`notebooklm auth refresh --verify`) and writes the fresh Google cookies into the n8n credential through the n8n API (`PATCH /api/v1/credentials/{id}`):
   ```bash
   N8N_URL=http://localhost:5678 N8N_API_KEY=... N8N_CREDENTIAL_ID=... python3 scripts/sync-session-to-n8n.py
   ```
   Create the credential first (any placeholder in **Session JSON**), take its ID from the URL of the credential page, and create an API key under **Settings → n8n API**. Use a private address for `N8N_URL` (a LAN or Tailscale address, for example) so the cookies do not travel through a public proxy.

### Manual: Cookie header

Open https://notebook.google.com in a signed-in browser, copy the `Cookie` request header from the developer tools (Network tab) and paste it into **Session JSON**. It works until the cookies rotate; then you have to paste a fresh one.

### Known issue: `npx notebooklm-sdk login`

The login helper of the SDK cannot sign in on a browser profile that is not signed in yet. `notebook.google.com` now shows a landing page to signed-out visitors, so the helper does not wait for the sign-in and fails with `Missing required cookie: SID`. Prefer the setup above. The helper still works when its browser profile is already signed in.

### Adding the credential in n8n

1. Go to **Credentials → New Credential → NotebookLM API**
2. Paste the session into **Session JSON**: the content of notebooklm-py's `storage_state.json`, the `session.json` written by the SDK helper, or a `Cookie` header
3. Save

---

## Resources & Operations

### Notebook

| Operation | Description                        |
| --------- | ---------------------------------- |
| List      | List all notebooks in your account |
| Get       | Get a notebook by ID               |
| Create    | Create a new notebook              |
| Delete    | Delete a notebook                  |

### Source

| Operation        | Description                             | Parameters                           |
| ---------------- | --------------------------------------- | ------------------------------------ |
| List             | List all sources in a notebook          | Notebook ID                          |
| Add URL          | Add a web URL as a source               | Notebook ID, URL                     |
| Add Text         | Add plain text as a source              | Notebook ID, Title, Content          |
| Get Fulltext     | Get the full extracted text of a source | Notebook ID, Source ID               |
| Wait Until Ready | Poll until a source finishes processing | Notebook ID, Source ID, Timeout      |
| Delete           | Delete a source                         | Notebook ID, Source ID               |

### Artifact

| Operation             | Description                                        | Parameters                                  |
| --------------------- | -------------------------------------------------- | ------------------------------------------- |
| List                  | List all artifacts                                 | Notebook ID                                 |
| List Audio Overviews  | List audio overview artifacts                      | Notebook ID                                 |
| List Reports          | List report artifacts                              | Notebook ID                                 |
| Create Audio Overview | Generate an audio overview podcast                 | Notebook ID                                 |
| Create Report         | Generate a briefing doc, study guide, or blog post | Notebook ID, Format                         |
| Create Mind Map       | Generate a mind map note                           | Notebook ID                                 |
| Create Infographic    | Generate an infographic image                      | Notebook ID, Orientation, Detail, Style     |
| Create Video          | Generate a video overview (see below)              | Notebook ID, Format, Style, Style Prompt    |
| Create Quiz           | Generate a quiz                                    | Notebook ID, Quantity, Difficulty           |
| Create Flashcards     | Generate flashcards                                | Notebook ID, Quantity, Difficulty           |
| Create Slide Deck     | Generate a slide deck                              | Notebook ID, Format, Length                 |
| Wait Until Ready      | Poll until an artifact finishes generating         | Notebook ID, Artifact ID, Timeout, Interval |
| Download Audio        | Download an audio overview as MP3                  | Notebook ID, Artifact ID                    |
| Download Video        | Download a video artifact as MP4                   | Notebook ID, Artifact ID                    |
| Download Slide Deck   | Download a slide deck as PDF or PPTX               | Notebook ID, Artifact ID, Format            |
| Download Infographic  | Download an infographic as PNG                     | Notebook ID, Artifact ID                    |
| Export Report         | Export a report artifact to Google Docs            | Notebook ID, Artifact ID, Title             |

**Report formats:** `Briefing Doc`, `Study Guide`, `Blog Post`

**Video options (Create Video):**

| Option       | Values                                                                                                                                                                                                  |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Format       | `Explainer`, `Brief`, `Cinematic` (Veo 3 footage; needs Google AI Pro/Ultra and speaks English whatever the language setting is), `Short` (vertical 9:16 with a fixed visual style)                    |
| Style        | `Auto Select`, `Classic`, `Whiteboard`, `Kawaii`, `Anime`, `Watercolor`, `Retro Print`, `Heritage`, `Paper Craft`, `Custom`. Explainer and Brief only; Cinematic and Short ignore it                    |
| Style Prompt | Only with Style = `Custom`: describes the look of the video, English works best. Example: `photorealistic real-world documentary footage, live-action video of real fishing scenes, natural lighting` |
| Instructions | What the video should say and how (topic, tone, voice, language rules)                                                                                                                                  |

A video takes minutes to render. Follow **Create Video** with **Wait Until Ready** (set Timeout to 1800 s or more, and raise the workflow's execution timeout above it) and then **Download Video**. Daily limits depend on your Google plan.

> Download operations output a **binary item** (field name: `data`). Connect them to nodes like **Write Binary File**, **Send Email**, or **HTTP Request** to use the file.

### Chat

| Operation | Description                                     | Parameters           |
| --------- | ----------------------------------------------- | -------------------- |
| Ask       | Send a question and receive a grounded response | Notebook ID, Message |

### Note

| Operation | Description                       | Parameters           |
| --------- | --------------------------------- | -------------------- |
| List      | List all text notes in a notebook | Notebook ID          |
| Create    | Create a new note                 | Notebook ID, Content |

---

## Example workflows

**Summarize a webpage into a NotebookLM notebook:**

1. **HTTP Request** — fetch a webpage URL
2. **NotebookLM: Source → Add URL** — add the URL to a notebook
3. **NotebookLM: Artifact → Create Report** — generate a briefing doc
4. **NotebookLM: Chat → Ask** — ask a follow-up question grounded in the source

**Generate and download an audio overview:**

1. **NotebookLM: Artifact → Create Audio Overview** — kick off generation (returns `artifactId`)
2. **NotebookLM: Artifact → Wait Until Ready** — poll until status is `completed`
3. **NotebookLM: Artifact → Download Audio** — download the MP3 as binary data
4. **Write Binary File** — save to disk, or pipe to any other binary-capable node

**Create and download an infographic from your latest notebook** ([example JSON](examples/list-create-download-infographic.json)):

1. **NotebookLM: Notebook → List** — list all notebooks (returned in most-recently-accessed order)
2. **Code** — `return [$input.first()]` to pick the latest one
3. **NotebookLM: Artifact → Create Infographic** — kick off generation
4. **NotebookLM: Artifact → Wait Until Ready** — poll every 5 s, up to 300 s
5. **NotebookLM: Artifact → Download Infographic** — download the PNG as binary data

---

## Finding your Notebook ID

The notebook ID is the long alphanumeric string in the NotebookLM URL:

```
https://notebook.google.com/notebook/abc123def456...
                                       ^^^^^^^^^^^^^^^^
```

You can also use **Notebook → List** as the first step in a workflow to retrieve notebook IDs dynamically.

---

## Local development

```bash
git clone https://github.com/Nikolayco/n8n-nodes-notebooklm-sdk
cd n8n-nodes-notebooklm-sdk
npm install
npm run build
```

To test in a local n8n instance:

```bash
# In this repo
npm link

# In your n8n directory
npm link n8n-nodes-notebooklm-sdk
```

Then restart n8n — the node will appear in the node palette under **NotebookLM**.

---

## License

MIT
