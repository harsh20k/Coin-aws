# Dalla Project.

```ad-info
A smart finance advisor web-app where users log their transactions and get personalised advice and ask questions about their budget and habits.
```

## Simple day‑by‑day checklist (Feb 12–23)

### [[Feb 12]] (today) 
- **Main 1**: Write 3–5 sentences describing what the app will do for a normal user.
- **Main 2**: Roughly draw the app flow: user → website → server → database → AI advice.
- **Nice**: Decide tech: React or simple HTML/JS; choose one and stick to it.

### [[Feb 13]]
- **Main 1**: Decide what a “transaction” looks like (fields like amount, date, category, note).
- **Main 2**: List the screens/pages you will have (add transaction, list, insights).
- **Nice**: List the buttons/actions you need on each screen.

### Feb 14
- **Main 1**: Create the basic web app skeleton (one page that says “Smart Finance Advisor”).
- **Main 2**: Add a simple “Add transaction” form on the page (not connected to backend yet).
- **Nice**: Add a basic layout and simple styling so it doesn’t look totally plain.

### Feb 15
- **Main 1**: On AWS, create a database/table for transactions (e.g., DynamoDB).
- **Main 2**: Create one simple cloud function that just returns “OK” when called.
- **Nice**: Test the function from your laptop with curl/Postman.

### Feb 16
- **Main 1**: Make a cloud function that saves a new transaction into the database.
- **Main 2**: Make a cloud function that reads back recent transactions for one user.
- **Nice**: Add basic checks (no negative amount, required fields).

### Feb 17
- **Main 1**: Connect the web “Add transaction” form to the real backend save function.
- **Main 2**: Show a simple transaction list on the page using real data from the backend.
- **Nice**: Show a small message when saving succeeds or fails.

### Feb 18
- **Main 1**: On the server, write logic to sum up spending by month and by category.
- **Main 2**: Add an endpoint that returns this summary data in JSON.
- **Nice**: Mark each category as “need” or “want” in your summary.

### Feb 19
- **Main 1**: Call the AI service (e.g., Bedrock) from a function using the summary JSON.
- **Main 2**: Make an endpoint that returns both: summary numbers + AI-generated advice text.
- **Nice**: Try one or two different prompts and pick the one that sounds best.

### Feb 20
- **Main 1**: Add an “Insights” section/page on the web app.
- **Main 2**: Show key numbers (total spent, needs vs wants %) and the advice paragraph.
- **Nice**: Take a few screenshots for your report and slides.

### Feb 21
- **Main 1**: Clean up the UI: better labels, spacing, simple colors.
- **Main 2**: Fix any obvious bugs in the main flow (add → list → insights).
- **Nice**: Add one small extra feature (e.g., filter by month).

### Feb 22
- **Main 1**: Write a simple report outline: intro, what you built, which AWS services, how AI is used.
- **Main 2**: Draw a neat architecture diagram in diagrams.net and export it.
- **Nice**: Draft bullet points for what you will say in the video demo.

### Feb 23
- **Main 1**: Do a full dry run: pretend you are recording the video and click through the app.
- **Main 2**: Fix any last-minute issues that break the demo and stop changing code after that.
- **Nice**: Double-check you can redeploy everything with one or two simple commands.

